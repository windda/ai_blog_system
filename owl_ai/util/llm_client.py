# -*- coding: utf-8 -*-
"""
统一 AI 调度网关客户端（llm_client.py）

本模块是「统一 AI 调度网关」，所有 AI 能力统一接入：
    - llm：文本大模型（DeepSeek 等）
    - asr：语音转写（OpenAI whisper 等）

设计解耦：新增能力/服务商只需在 config.yaml 加配置 + call() 加分支，
不改调度核心（重试、日志、鉴权复用）。
预留扩展：边缘设备 / 具身智能硬件接入（后续可新增 ai_type='edge'/'embodied'）。

异常精细化：
    - 超时：重试 1 次
    - 429 限流：重试 1 次 + 限流告警
    - 401/403：禁止重试，直接记录
    - 解析失败：保存原始返回文本（raw）
"""

import os
import json
import time
import logging

import requests

logger = logging.getLogger(__name__)

# ============================================================
# 配置加载
# ============================================================

# config.yaml 位于项目根目录（llm_client.py -> util -> owl_ai -> 项目根）
_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
)


def _load_yaml_config() -> dict:
    """读取 config.yaml（失败时返回空配置，由上层兜底）"""
    try:
        import yaml
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:  # noqa: BLE001
        logger.warning("[AI网关] 读取 config.yaml 失败：%s", e)
        return {}


def get_provider_config(capability: str) -> dict:
    """获取指定能力（llm/asr）当前环境下的服务商配置（dev/prod 由 ai.env 决定）"""
    data = _load_yaml_config()
    ai_cfg = data.get('ai', {}) or {}
    env = ai_cfg.get('env', 'dev')
    return (ai_cfg.get(capability, {}) or {}).get(env, {}) or {}


# ============================================================
# 异常定义（精细化分类）
# ============================================================

class AICallError(Exception):
    """AI 调用异常，带分类，便于上层针对不同类别做不同处理"""

    TIMEOUT = 'timeout'          # 超时
    RATE_LIMIT = 'rate_limit'    # 429 限流
    AUTH = 'auth'                # 401/403 鉴权失败
    PARSE = 'parse'              # 返回解析失败
    NETWORK = 'network'          # 网络错误
    UNKNOWN = 'unknown'          # 未知错误

    def __init__(self, category: str, message: str, raw: str = None):
        self.category = category
        self.message = message
        self.raw = raw  # 原始返回文本：解析失败时保存，用于排查
        super().__init__(message)


# ============================================================
# 统一调度网关客户端
# ============================================================

class AIGatewayClient:
    """
    统一 AI 调度网关客户端。

    支持能力：llm（文本大模型）/ asr（语音转写）。
    新增能力只需在 call() 加分支 + config.yaml 加配置，核心逻辑不变。
    """

    # 支持的 ai_type 集合（预留：后续可扩展 edge / embodied）
    SUPPORTED_TYPES = {'llm', 'asr'}

    @classmethod
    def call(cls, ai_type: str, user_id=None, **payload) -> dict:
        """
        统一 AI 调用入口，按 ai_type 自动路由。

        Args:
            ai_type: 能力类型，'llm' 或 'asr'
            user_id: 当前用户 ID（用于日志记录）
            **payload: 各能力入参（llm: messages；asr: audio_path/audio_bytes）

        Returns:
            dict: {'reply'/'text': ..., 'usage': {...}, 'ai_type': ..., 'elapsed_ms': ...}
        """
        start = time.time()
        if ai_type == 'llm':
            result = cls._call_llm(user_id, payload)
        elif ai_type == 'asr':
            result = cls._call_asr(user_id, payload)
        else:
            raise AICallError(
                AICallError.UNKNOWN,
                f"不支持的 ai_type: {ai_type}，当前支持 {cls.SUPPORTED_TYPES}"
            )

        result['ai_type'] = ai_type
        result['elapsed_ms'] = int((time.time() - start) * 1000)
        return result

    # ============================================================
    # LLM 文本能力
    # ============================================================
    @classmethod
    def _call_llm(cls, user_id, payload: dict) -> dict:
        """LLM 文本调用：自动采集 usage、统一异常处理、记录日志"""
        cfg = get_provider_config('llm')
        messages = payload.get('messages') or []
        session_id = payload.get('session_id')
        temperature = payload.get('temperature', 0.7)
        max_tokens = payload.get('max_tokens', 4096)
        api_key = os.environ.get(cfg.get('api_key_env', ''), '')

        if not api_key:
            raise AICallError(AICallError.AUTH, "LLM API Key 未配置")

        base_url = cfg.get('base_url', '').rstrip('/')
        model = cfg.get('model', 'deepseek-chat')
        timeout = int(cfg.get('timeout', 30))
        max_retries = int(cfg.get('max_retries', 1))

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        resp = cls._request_with_retry('POST', url, headers, max_retries, timeout=timeout, json=body)

        try:
            data = resp.json()
        except Exception as e:  # noqa: BLE001
            raw_text = resp.text[:2000] if resp is not None else ''
            raise AICallError(AICallError.PARSE, f"LLM 返回解析失败：{e}", raw=raw_text)

        usage = data.get('usage', {}) or {}
        input_tokens = usage.get('prompt_tokens', 0) or 0
        output_tokens = usage.get('completion_tokens', 0) or 0
        total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

        choice = (data.get('choices') or [{}])[0]
        reply = choice.get('message', {}).get('content', '') or ''

        cls._log_call(
            user_id=user_id, session_id=session_id, ai_type='llm', model=model,
            prompt_tokens=input_tokens, completion_tokens=output_tokens,
            total_tokens=total_tokens, input_tokens=input_tokens, output_tokens=output_tokens,
        )

        return {
            'reply': reply,
            'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_tokens': total_tokens},
        }

    # ============================================================
    # ASR 语音转写能力
    # ============================================================
    @classmethod
    def _call_asr(cls, user_id, payload: dict) -> dict:
        """ASR 语音转写：上传音频，返回转写文本，统一日志/异常处理"""
        cfg = get_provider_config('asr')
        audio_path = payload.get('audio_path')
        audio_bytes = payload.get('audio_bytes')
        session_id = payload.get('session_id')
        api_key = os.environ.get(cfg.get('api_key_env', ''), '')

        if not api_key:
            raise AICallError(AICallError.AUTH, "ASR API Key 未配置")
        if not audio_path and not audio_bytes:
            raise AICallError(AICallError.UNKNOWN, "缺少音频数据（audio_path / audio_bytes）")

        base_url = cfg.get('base_url', '').rstrip('/')
        model = cfg.get('model', 'whisper-1')
        timeout = int(cfg.get('timeout', 60))
        max_retries = int(cfg.get('max_retries', 1))

        url = f"{base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        file_obj = None
        if audio_bytes is not None:
            files = {'file': ('audio.webm', audio_bytes, 'audio/webm')}
        else:
            file_obj = open(audio_path, 'rb')
            files = {'file': (os.path.basename(audio_path), file_obj, 'audio/webm')}

        try:
            resp = cls._request_with_retry(
                'POST', url, headers, max_retries,
                timeout=timeout, files=files, data={"model": model}
            )
        finally:
            if file_obj is not None:
                try:
                    file_obj.close()
                except Exception:  # noqa: BLE001
                    pass

        try:
            result = resp.json()
        except Exception as e:  # noqa: BLE001
            raw_text = resp.text[:2000] if resp is not None else ''
            raise AICallError(AICallError.PARSE, f"ASR 返回解析失败：{e}", raw=raw_text)

        text = result.get('text', '') or ''
        # whisper 接口通常不返回 token usage，用转写文本长度粗估输出 token
        output_tokens = max(1, len(text) // 4) if text else 0
        input_tokens = 0

        cls._log_call(
            user_id=user_id, session_id=session_id, ai_type='asr', model=model,
            prompt_tokens=0, completion_tokens=0, total_tokens=output_tokens,
            input_tokens=input_tokens, output_tokens=output_tokens,
        )

        return {
            'text': text,
            'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens},
        }

    # ============================================================
    # 精细化重试 + 异常分类
    # ============================================================
    @classmethod
    def _request_with_retry(cls, method, url, headers, max_retries, **kwargs):
        """
        统一 HTTP 请求 + 精细化异常处理。

        策略：
            - 超时：仅重试 1 次
            - 429 限流：仅重试 1 次 + 日志标记「限流告警」
            - 401/403 鉴权失败：禁止重试，直接抛 AUTH 异常
        """
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                resp = requests.request(method, url, headers=headers, **kwargs)

                if resp.status_code == 429:
                    logger.warning("[AI网关] 429 限流告警：%s（第 %s 次）", url, attempt + 1)
                    if attempt < max_retries:
                        time.sleep(1 * (attempt + 1))
                        continue
                    raise AICallError(AICallError.RATE_LIMIT, "请求过于频繁（429），请稍后再试")

                if resp.status_code in (401, 403):
                    raise AICallError(AICallError.AUTH, f"鉴权失败（{resp.status_code}），请检查 API Key")

                if resp.status_code >= 400:
                    raise AICallError(
                        AICallError.UNKNOWN,
                        f"AI 服务返回错误（{resp.status_code}）：{resp.text[:500]}"
                    )

                return resp

            except requests.exceptions.Timeout as e:
                last_err = e
                logger.warning("[AI网关] 请求超时：%s（第 %s 次）", url, attempt + 1)
                if attempt < max_retries:
                    continue
                raise AICallError(AICallError.TIMEOUT, "请求超时，请稍后重试")

            except requests.exceptions.ConnectionError as e:
                last_err = e
                if attempt < max_retries:
                    continue
                raise AICallError(AICallError.NETWORK, f"网络连接失败：{e}")

        raise AICallError(AICallError.UNKNOWN, f"请求失败：{last_err}")

    # ============================================================
    # 统一日志记录
    # ============================================================
    @classmethod
    def _log_call(cls, user_id, session_id, ai_type, model,
                  prompt_tokens=0, completion_tokens=0, total_tokens=0,
                  input_tokens=0, output_tokens=0):
        """统一日志记录：写入 ai_token_record（失败不影响主流程）"""
        try:
            from owl_admin.ext import db
            from owl_ai.domain.po import AiTokenRecordPo
            record = AiTokenRecordPo(
                user_id=user_id or 0,
                session_id=session_id,
                ai_type=ai_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
            )
            db.session.add(record)
            db.session.commit()
        except Exception as e:  # noqa: BLE001
            try:
                from owl_admin.ext import db as _db
                _db.session.rollback()
            except Exception:  # noqa: BLE001
                pass
            logger.warning("[AI网关] 记录调用日志失败：%s", e)
