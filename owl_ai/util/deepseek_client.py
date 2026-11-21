# -*- coding: utf-8 -*-
"""
DeepSeek API 客户端工具类。

基于 OpenAI 兼容接口，使用 requests 调用 DeepSeek API；
支持流式 SSE 返回、超时控制与重试机制。

环境配置（.env）：
    DEEPSEEK_API_KEY=sk-xxxxx
    DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
    DEEPSEEK_MODEL=deepseek-chat
    DEEPSEEK_SYSTEM_PROMPT=你是一个有帮助的AI助手
"""

import os
import json
import time
import traceback
import requests


class DeepSeekClient:
    """DeepSeek API 客户端"""

    # 从环境变量读取配置
    BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    _DEFAULT_MODEL = "deepseek-chat"
    SYSTEM_PROMPT = os.environ.get(
        "DEEPSEEK_SYSTEM_PROMPT",
        "你是一个智能对话助手，请用简洁清晰的中文回答问题。"
    )
    TIMEOUT = 30       # 请求超时秒数
    MAX_RETRIES = 1    # 最大重试次数（每个供应商最多重试 1 次，防止打爆上游）

    @classmethod
    def _get_api_key(cls, user_id=None) -> str:
        """获取 API Key（BYOK：只从本地 ai_config.json 读，不读环境变量）"""
        try:
            from owl_ai.util.ai_config import get_api_key
            return get_api_key(user_id)
        except Exception:
            return ''

    @classmethod
    def _get_model(cls, user_id=None) -> str:
        """动态获取模型名：优先本地 ai_config.json（BYOK）"""
        try:
            from owl_ai.util.ai_config import get_model
            return get_model(user_id)
        except Exception:
            return cls._DEFAULT_MODEL

    @classmethod
    def _load_providers(cls) -> list:
        """
        从 config.yaml 读取启用的 LLM 供应商列表（按声明顺序，用于故障降级）。

        Returns:
            list: [{'name', 'base_url', 'api_key_env', 'default_model'}, ...]
        """
        try:
            import yaml
            config_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
            )
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            providers = (data.get('ai', {}).get('llm', {}).get('providers') or {})
            result = []
            for name, cfg in providers.items():
                if cfg.get('enabled', False):
                    result.append({
                        'name': name,
                        'base_url': (cfg.get('base_url') or '').rstrip('/'),
                        'api_key_env': cfg.get('api_key_env', ''),
                        'default_model': cfg.get('default_model', cls._DEFAULT_MODEL),
                        'models': cfg.get('models') or [cfg.get('default_model', cls._DEFAULT_MODEL)],
                    })
            return result
        except Exception as e:  # noqa: BLE001
            print(f"[SSE流式] 读取供应商配置失败：{e}")
            return []

    @classmethod
    def _log_provider_call(cls, provider_name, model, success, error_category='', error_message='', latency_ms=0, ai_type='llm', user_id=None):
        """记录服务商调用结果到 ai_provider_call_log（失败原因 + 切换记录，供后台统计成功率）

        Args:
            provider_name: 服务商名（deepseek / hunyuan / qianfan ...）
            model: 模型名
            success: True 成功 / False 失败
            error_category: 失败分类（timeout / 429 / 500 / auth / network / http_xxx / exception）
            error_message: 失败详情
            latency_ms: 耗时（毫秒）
            ai_type: 能力类型（llm / asr）
            user_id: 用户 ID（可选，用于调用日志关联用户）
        """
        try:
            from owl_admin.ext import db
            from owl_ai.domain.po import AiProviderCallLogPo
            record = AiProviderCallLogPo(
                user_id=user_id,
                provider=provider_name or '',
                model=model or '',
                ai_type=ai_type,
                success=1 if success else 0,
                error_category=error_category or '',
                error_message=(error_message or '')[:500],
                latency_ms=latency_ms or 0,
            )
            db.session.add(record)
            db.session.commit()
        except Exception as e:  # noqa: BLE001
            try:
                from owl_admin.ext import db as _db
                _db.session.rollback()
            except Exception:  # noqa: BLE001
                pass
            print(f"[SSE流式] 记录服务商调用日志失败：{e}")

    @classmethod
    def _build_messages(cls, context: list) -> list:
        """
        构建完整的 messages 数组（System Prompt + 上下文）

        Args:
            context: 已有的消息上下文（含 system 可能）

        Returns:
            格式化后的 messages 列表
        """
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]

        # 如果 context 第一项已经是 system，则替换
        if context and context[0].get("role") == "system":
            context = context[1:]

        messages.extend(context)
        return messages

    @classmethod
    def chat_stream(cls, context: list, on_token, on_done=None, on_error=None, api_key=None, model=None, on_usage=None, user_id=None):
        """
        流式对话（SSE 逐 Token 推送，支持多供应商故障降级）。

        供应商来自 config.yaml 的 ai.llm.providers（enabled 的，按声明顺序），
        某个供应商超时 / 连接失败 / 返回 500+ 时，自动降级到下一个供应商。
        """
        messages = cls._build_messages(context)

        # 供应商列表（enabled 的，按顺序）；无配置则兜底 DeepSeek
        providers = cls._load_providers()
        if not providers:
            providers = [{
                'name': 'deepseek',
                'base_url': cls.BASE_URL,
                'api_key_env': 'DEEPSEEK_API_KEY',
                'default_model': cls._DEFAULT_MODEL,
                'models': [cls._DEFAULT_MODEL],
            }]

        # 根据 model 匹配供应商：model 在某供应商的 models 列表里，则优先用该供应商
        if model and providers:
            matched = [p for p in providers if model in (p.get('models') or [])]
            others = [p for p in providers if model not in (p.get('models') or [])]
            providers = matched + others

        # 逐个供应商尝试，失败降级到下一个
        for provider in providers:
            provider_api_key = api_key or os.environ.get(provider.get('api_key_env', ''), '')
            if not provider_api_key:
                print(f"[SSE流式] 供应商 {provider['name']} 未配置 key，跳过")
                continue
            provider_model = model or provider.get('default_model', cls._DEFAULT_MODEL)
            base_url = provider.get('base_url', '').rstrip('/')

            full_reply = []
            usage = {}
            request_body = {
                "model": provider_model,
                "messages": messages,
                "stream": True,
                "stream_options": {"include_usage": True},
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            print(f"[SSE流式] 尝试供应商 {provider['name']}：model={provider_model}")

            succeeded = False
            for attempt in range(cls.MAX_RETRIES + 1):
                start = time.time()
                try:
                    response = requests.post(
                        f"{base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {provider_api_key}",
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream",
                        },
                        json=request_body,
                        stream=True,
                        timeout=cls.TIMEOUT,
                    )
                    latency_ms = int((time.time() - start) * 1000)

                    # 429 限流 → 记录 + 重试 1 次 / 切换下一个供应商
                    if response.status_code == 429:
                        cls._log_provider_call(provider['name'], provider_model, False, '429', '请求过于频繁（429 限流）', latency_ms, user_id=user_id)
                        print(f"[SSE流式] 供应商 {provider['name']} 返回 429 限流")
                        if attempt < cls.MAX_RETRIES:
                            time.sleep(1)
                            continue
                        break

                    # 500+ 服务端故障 → 记录 + 重试 1 次 / 切换下一个供应商
                    if response.status_code >= 500:
                        cls._log_provider_call(provider['name'], provider_model, False, str(response.status_code), f"服务端错误 {response.status_code}", latency_ms, user_id=user_id)
                        print(f"[SSE流式] 供应商 {provider['name']} 返回 {response.status_code}，降级")
                        if attempt < cls.MAX_RETRIES:
                            time.sleep(1)
                            continue
                        break

                    # 401/403 鉴权失败 → 记录 + 直接切换（key 问题重试无意义）
                    if response.status_code in (401, 403):
                        cls._log_provider_call(provider['name'], provider_model, False, 'auth', f"鉴权失败（{response.status_code}），请检查 API Key", latency_ms, user_id=user_id)
                        print(f"[SSE流式] 供应商 {provider['name']} 鉴权失败 {response.status_code}")
                        break

                    # 其他非 200 → 记录 + 重试 1 次 / 切换下一个供应商
                    if not response.ok:
                        cls._log_provider_call(provider['name'], provider_model, False, f'http_{response.status_code}', response.text[:500], latency_ms, user_id=user_id)
                        print(f"[SSE流式] {provider['name']} 返回错误 {response.status_code}：{response.text[:500]}")
                        if attempt < cls.MAX_RETRIES:
                            time.sleep(1)
                            continue
                        break

                    # 逐行解析 SSE 流
                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if data.get("usage"):
                                    usage = data["usage"]
                                    if on_usage:
                                        on_usage(usage)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_reply.append(content)
                                        on_token(content)
                            except json.JSONDecodeError:
                                continue

                    succeeded = True
                    break

                except requests.exceptions.Timeout:
                    latency_ms = int((time.time() - start) * 1000)
                    cls._log_provider_call(provider['name'], provider_model, False, 'timeout', f"请求超时（>{cls.TIMEOUT}s）", latency_ms, user_id=user_id)
                    print(f"[SSE流式] 供应商 {provider['name']} 超时")
                    if attempt < cls.MAX_RETRIES:
                        time.sleep(1)
                        continue
                    break
                except requests.exceptions.ConnectionError as e:
                    latency_ms = int((time.time() - start) * 1000)
                    cls._log_provider_call(provider['name'], provider_model, False, 'network', str(e), latency_ms, user_id=user_id)
                    print(f"[SSE流式] 供应商 {provider['name']} 连接失败")
                    if attempt < cls.MAX_RETRIES:
                        time.sleep(1)
                        continue
                    break
                except Exception as e:
                    latency_ms = int((time.time() - start) * 1000)
                    cls._log_provider_call(provider['name'], provider_model, False, 'exception', str(e), latency_ms, user_id=user_id)
                    traceback.print_exc()
                    if attempt < cls.MAX_RETRIES:
                        time.sleep(1)
                        continue
                    break

            if succeeded:
                # 记录成功日志（含 SSE 解析耗时），用于成功率统计
                total_latency = int((time.time() - start) * 1000)
                cls._log_provider_call(provider['name'], provider_model, True, '', '', total_latency, user_id=user_id)
                # 流结束回调（返回完整文本 + usage，usage 用于 token 入库）
                if on_done:
                    on_done("".join(full_reply), usage)
                return

        # 所有供应商都失败
        if on_error:
            on_error("所有 AI 供应商均调用失败，请稍后重试")

    @classmethod
    def _build_messages_with_tools(cls, context: list) -> list:
        """构建含 tool_calls 的完整 messages"""
        from owl_ai.util.tool_executor import TOOLS_SCHEMA
        system_prompt = (
            "你是一个博客管理助手，可以通过工具帮助用户管理文章。"
            "当用户请求查询文章列表或创建文章时，请调用相应工具。"
            "如果工具返回了结果，请基于结果生成自然语言回复。"
            "生成文章草稿时，请使用自然段落描述，避免大量#号一级标题，"
            "正文使用普通段落+小标题（如**加粗**）即可，适配后台富文本编辑器。"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if context and context[0].get("role") == "system":
            messages[0] = context[0]
            context = context[1:]
        messages.extend(context)
        return messages, TOOLS_SCHEMA

    @classmethod
    def chat_sync_with_tools(cls, context: list, user_id: int) -> dict:
        """
        Function Calling 工具调用模式

        Returns:
            dict: {"reply": str, "tool_used": bool, "usage": dict or None}
        """
        from owl_ai.util.tool_executor import ToolExecutor

        api_key = cls._get_api_key(user_id)
        if not api_key:
            return {"reply": "请先配置 DeepSeek API Key", "tool_used": False, "usage": None}
        try:
            from owl_ai.util.ai_config import is_valid_key
            if not is_valid_key(api_key):
                return {"reply": "API Key 格式不正确，请检查后重新配置", "tool_used": False, "usage": None}
        except Exception:
            pass

        messages, tools = cls._build_messages_with_tools(context)
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        def _sanitize(content):
            """过滤DSML/tool_calls等原生标记，只保留自然语言"""
            import re
            content = re.sub(r'<\s*\|?\s*DSML\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*tool_calls\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*invoke\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*function_call\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            return content.strip()

        try:
            response = requests.post(
                f"{cls.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": cls._get_model(user_id),
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.7,
                    "max_tokens": 2048
                },
                timeout=cls.TIMEOUT
            )
            if not response.ok:
                err_msg = f"API 请求失败（{response.status_code}）"
                try:
                    err_data = response.json()
                    err_msg = err_data.get('error', {}).get('message', err_msg)
                except Exception:
                    pass
                if response.status_code == 401:
                    err_msg = "API Key 无效或已过期，请检查后重新配置"
                elif response.status_code == 429:
                    err_msg = "请求过于频繁或账户余额不足，请稍后再试"
                return {"reply": err_msg, "tool_used": False, "usage": total_usage}

            data = response.json()
            usage1 = data.get("usage", {})
            total_usage["prompt_tokens"] += usage1.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage1.get("completion_tokens", 0)
            total_usage["total_tokens"] += usage1.get("total_tokens", 0)

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            tool_calls = message.get("tool_calls", [])
            if not tool_calls:
                return {"reply": _sanitize(message.get("content", "")), "tool_used": False, "usage": total_usage}

            tool_results = []
            for tc in tool_calls:
                func_info = tc.get("function", {})
                tool_name = func_info.get("name", "")
                try:
                    args = json.loads(func_info.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                result = ToolExecutor.execute(user_id, tool_name, args)
                tool_results.append({
                    "tool_call_id": tc.get("id", ""),
                    "name": tool_name,
                    "result": result
                })

            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": tr["result"]
                })

            response2 = requests.post(
                f"{cls.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": cls._get_model(user_id),
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                timeout=cls.TIMEOUT
            )
            if response2.ok:
                data2 = response2.json()
                usage2 = data2.get("usage", {})
                total_usage["prompt_tokens"] += usage2.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += usage2.get("completion_tokens", 0)
                total_usage["total_tokens"] += usage2.get("total_tokens", 0)
                content = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"reply": _sanitize(content) or "操作已完成", "tool_used": True, "usage": total_usage}

            return {"reply": "生成内容耗时较长，请重新提问", "tool_used": True, "usage": total_usage}

        except requests.exceptions.Timeout:
            return {"reply": "生成内容耗时较长，请重新提问", "tool_used": True, "usage": total_usage}
        except requests.exceptions.ConnectionError:
            return {"reply": "网络连接失败，请检查网络后重试", "tool_used": False, "usage": total_usage}
        except Exception as e:
            traceback.print_exc()
            return {"reply": f"AI 服务调用异常（{type(e).__name__}）：{e}", "tool_used": False, "usage": total_usage}

