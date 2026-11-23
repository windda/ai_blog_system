# -*- coding: utf-8 -*-
"""
AI 对话控制器

开发环境：HTTP POST /ai/chat 非流式
生产环境：SocketIO ai-chat 事件流式输出
"""

from flask import request

from owl_admin import reg
from owl_admin.ext import socketio, redis_cache, db
from owl_common.utils import security_util as SecurityUtil
from owl_ai.util.deepseek_client import DeepSeekClient
from owl_ai.service.ai_chat import AiChatService
from owl_ai.domain.po import AiTokenRecordPo, BowlAiSession
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.serializer import JsonSerializer
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
import traceback

# 东八区时区（Asia/Shanghai，中国无夏令时，固定 UTC+8）
CST_TZ = timezone(timedelta(hours=8), "Asia/Shanghai")

RATE_LIMIT_PREFIX = "ai:rate:user:"
DAILY_LIMIT = 30


def _estimate_tokens(text):
    """本地估算 token 数：优先 tiktoken，失败用字符数/4 粗略估算"""
    text = text or ''
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except Exception:  # noqa: BLE001
        return max(1, len(text) // 4)


def _calc_cost(model, prompt_tokens, completion_tokens):
    """根据模型单价计算费用（元）。

    公式：费用 = (输入token × 输入单价 + 输出token × 输出单价) / 100万
    单价来自 ai_model_price 表（单位：元/百万token），未配置的模型按 0 计费。
    """
    try:
        from owl_ai.domain.po import AiModelPricePo
        price = db.session.execute(
            select(AiModelPricePo).where(AiModelPricePo.model == model)
        ).scalar_one_or_none()
        if not price:
            return 0.0
        input_cost = (prompt_tokens or 0) * (price.input_price or 0) / 1000000.0
        output_cost = (completion_tokens or 0) * (price.output_price or 0) / 1000000.0
        return round(input_cost + output_cost, 6)
    except Exception:  # noqa: BLE001
        return 0.0


def _get_daily_token_limit(user_id=None):
    """获取每日 Token 限额（后端服务防护限流，独立于厂商额度）

    两种调用模式（平台全局 Key / 用户自有 Key）都受此限额管控。

    默认规则（后台 sys_config 可配置 ai.daily.token.limit 全局覆盖）：
        - 普通用户：10000 token/日
        - 管理员（user_id == 1）：50000 token/日
    """
    try:
        from owl_system.service import SysConfigService
        value = SysConfigService.select_config_by_key("ai.daily.token.limit")
        if value:
            return int(value)
    except Exception:  # noqa: BLE001
        pass
    # 默认规则：管理员 50000，普通用户 10000
    return 50000 if SecurityUtil.is_admin(user_id) else 10000


def _encrypt_platform_key(plaintext: str) -> str:
    """平台全局 Key 加密（带 enc: 前缀标记密文）"""
    from owl_ai.util.ai_config import encrypt_text
    return 'enc:' + encrypt_text(plaintext)


def _decrypt_platform_key(stored: str) -> str:
    """解密平台全局 Key（兼容旧明文数据）"""
    stored = (stored or '').strip()
    if not stored:
        return ''
    if stored.startswith('enc:'):
        from owl_ai.util.ai_config import decrypt_text
        return decrypt_text(stored[4:]).strip()
    return stored  # 兼容旧数据：明文直接返回


def _get_platform_api_key():
    """平台全局 Key（管理员后台配置，加密存数据库；兜底环境变量）"""
    try:
        from owl_system.service import SysConfigService
        value = SysConfigService.select_config_by_key("ai.platform.api.key")
        if value:
            return _decrypt_platform_key(value)
    except Exception:  # noqa: BLE001
        pass
    import os
    return os.environ.get('DEEPSEEK_API_KEY', '')


def _platform_key_fallback_enabled():
    """是否允许用户未填写自有 Key 时，降级使用平台全局 Key（默认开启）

    开关 enable_platform_key_fallback（后台 sys_config）：
        - 开启（默认）：用户无自有 Key → 降级走平台全局 Key
        - 关闭：用户无自有 Key → 直接拦截，提示绑定自己的 Key
    """
    try:
        from owl_system.service import SysConfigService
        value = SysConfigService.select_config_by_key("enable_platform_key_fallback")
        if value is not None and value != '':
            return value.strip().lower() in ('true', '1', 'yes', 'on')
    except Exception:  # noqa: BLE001
        pass
    return True  # 默认开启


def _asr_enabled():
    """ASR 语音识别开关（后台 sys_config 配置，默认关闭）

    开关 ai.asr.enabled（后台 sys_config）：
        - 开启：前端显示录音按钮，/ai/asr 可用
        - 关闭：前端隐藏按钮，/ai/asr 返回友好提示
    """
    try:
        from owl_system.service import SysConfigService
        value = SysConfigService.select_config_by_key("ai.asr.enabled")
        if value is not None and value != '':
            return value.strip().lower() in ('true', '1', 'yes', 'on')
    except Exception:  # noqa: BLE001
        pass
    return False  # 默认关闭


def _today_range_cst():
    """返回东八区（Asia/Shanghai）当天 [0点, 24点) 对应的 UTC naive 时间边界

    说明：
    - 日期按国内自然日（0点到24点）统计，不用 UTC 时间直接 date 判断；
    - 数据库 ai_token_record.create_time 存的是 UTC（CURRENT_TIMESTAMP），
      东八区自然日 0:00 ~ 24:00 = UTC 前一天 16:00 ~ 当天 16:00；
    - 返回 (start_utc, end_utc)，均为 naive datetime，用于与 create_time 比较。
    """
    now_cst = datetime.now(CST_TZ)
    today_start_cst = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_cst = today_start_cst + timedelta(days=1)
    start_utc = today_start_cst.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = today_end_cst.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def _get_today_tokens(user_id, key_source=None):
    """按用户 + 东八区当天，汇总当日消耗 token（输入 + 输出）

    key_source: None 汇总全部；'platform' 只统计平台 Key；'user' 只统计用户自有 Key。
    额度校验时只统计 platform 来源（用户自有 Key 不计入平台额度）。
    """
    try:
        today_start, today_end = _today_range_cst()
        conditions = [
            AiTokenRecordPo.user_id == user_id,
            AiTokenRecordPo.create_time >= today_start,
            AiTokenRecordPo.create_time < today_end,
        ]
        if key_source:
            conditions.append(AiTokenRecordPo.key_source == key_source)
        # 今日消耗 = sum(输入 token + 输出 token)，与限额对比
        stmt = select(
            func.coalesce(func.sum(AiTokenRecordPo.prompt_tokens + AiTokenRecordPo.completion_tokens), 0)
        ).where(*conditions)
        return int(db.session.execute(stmt).scalar() or 0)
    except Exception:  # noqa: BLE001
        return 0


# QPS 频率限流配置：独立于 Token 额度，两种来源的调用都走频率校验
QPS_LIMIT = {'platform': 5, 'user': 8}   # 每分钟最大请求次数
QPS_PREFIX = "ai:qps:user:"


def _check_qps_limit(user_id, key_source='platform'):
    """QPS 频率限流（防并发打崩，独立于 Token 额度）

    返回 (ok: bool, msg: str)。管理员不限流；限流异常时放行不阻断主流程。
    """
    if _is_admin():
        return True, ''
    limit = QPS_LIMIT.get(key_source, QPS_LIMIT['platform'])
    rate_key = f"{QPS_PREFIX}{user_id}"
    try:
        count = redis_cache.incr(rate_key)
        if count == 1:
            redis_cache.expire(rate_key, 60)  # 60 秒滑动窗口
        if count > limit:
            return False, "请求过于频繁，请稍后再试"
        return True, ''
    except Exception:  # noqa: BLE001
        return True, ''


def _is_admin():
    try: return SecurityUtil.login_user_is_admin()
    except: return False

def _check_rate_limit(user_id):
    if _is_admin(): return True
    rate_key = f"{RATE_LIMIT_PREFIX}{user_id}"
    try:
        count = redis_cache.incr(rate_key)
        if count == 1:
            from datetime import datetime, timedelta
            tomorrow = datetime.combine(datetime.utcnow().date() + timedelta(days=1), datetime.min.time())
            redis_cache.expire(rate_key, int((tomorrow - datetime.utcnow()).total_seconds()))
        if count > DAILY_LIMIT: return False
        return True
    except Exception: return True


# ==================== REST 接口 ====================

@reg.api.route("/ai/providers", methods=["GET"])
@JsonSerializer()
def ai_providers():
    """返回启用的供应商 + 模型列表（供前端模型下拉动态渲染）"""
    from owl_ai.util.deepseek_client import DeepSeekClient
    providers = DeepSeekClient._load_providers()
    data = [{
        "provider": p['name'],
        "models": p.get('models') or [p.get('default_model')],
    } for p in providers]
    return AjaxResponse.from_success(data=data)


@reg.api.route("/ai/daily-usage", methods=["GET"])
@JsonSerializer()
def ai_daily_usage():
    """当前用户今日用量（平台额度 + 自有密钥，分开统计）

    平台额度：只统计 key_source='platform'，受每日限额管控；
    自有密钥：只统计 key_source='user'，不计入平台额度，无总量上限。
    """
    user_id = SecurityUtil.get_user_id()
    daily_limit = _get_daily_token_limit(user_id)
    if not user_id:
        return AjaxResponse.from_success(data={
            "todayPlatformTokens": 0, "todayPlatformCount": 0, "dailyLimit": daily_limit,
            "todayUserTokens": 0, "todayUserCount": 0,
        })
    today_start, today_end = _today_range_cst()
    # 平台额度：只统计 platform 来源
    platform_row = db.session.execute(select(
        func.count(AiTokenRecordPo.id),
        func.coalesce(func.sum(AiTokenRecordPo.prompt_tokens + AiTokenRecordPo.completion_tokens), 0),
    ).where(
        AiTokenRecordPo.user_id == user_id,
        AiTokenRecordPo.create_time >= today_start,
        AiTokenRecordPo.create_time < today_end,
        AiTokenRecordPo.key_source == 'platform',
    )).one_or_none()
    # 自有密钥：只统计 user 来源（不计入平台额度，无上限）
    user_row = db.session.execute(select(
        func.count(AiTokenRecordPo.id),
        func.coalesce(func.sum(AiTokenRecordPo.prompt_tokens + AiTokenRecordPo.completion_tokens), 0),
    ).where(
        AiTokenRecordPo.user_id == user_id,
        AiTokenRecordPo.create_time >= today_start,
        AiTokenRecordPo.create_time < today_end,
        AiTokenRecordPo.key_source == 'user',
    )).one_or_none()
    return AjaxResponse.from_success(data={
        "todayPlatformTokens": int(platform_row[1] or 0) if platform_row else 0,
        "todayPlatformCount": int(platform_row[0] or 0) if platform_row else 0,
        "dailyLimit": daily_limit,
        "todayUserTokens": int(user_row[1] or 0) if user_row else 0,
        "todayUserCount": int(user_row[0] or 0) if user_row else 0,
    })


@reg.api.route("/ai/my-token-records", methods=["GET"])
@JsonSerializer()
def ai_my_token_records():
    """当前用户自己的 token 消耗明细（分页），只能查看本人数据"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = int(request.args.get('pageNum', 1))
    page_size = min(int(request.args.get('pageSize', 10)), 100)
    columns = [
        AiTokenRecordPo.id, AiTokenRecordPo.session_id,
        AiTokenRecordPo.prompt_tokens, AiTokenRecordPo.completion_tokens,
        AiTokenRecordPo.total_tokens, AiTokenRecordPo.model, AiTokenRecordPo.create_time,
        AiTokenRecordPo.statistics_source, BowlAiSession.title,
    ]
    conditions = [AiTokenRecordPo.user_id == user_id]
    stmt = select(*columns).outerjoin(
        BowlAiSession, AiTokenRecordPo.session_id == BowlAiSession.session_id
    ).where(*conditions).order_by(AiTokenRecordPo.create_time.desc())
    count_stmt = select(func.count()).select_from(AiTokenRecordPo).where(*conditions)
    total = db.session.execute(count_stmt).scalar() or 0
    rows = db.session.execute(stmt.limit(page_size).offset((page_num - 1) * page_size)).all()
    records = [{
        "id": r[0], "sessionId": r[1],
        "promptTokens": r[2], "completionTokens": r[3], "totalTokens": r[4],
        "model": r[5],
        "createTime": (r[6] + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if r[6] else '',
        "statisticsSource": r[7] or 'api',
        "sessionTitle": r[8] or '',
    } for r in rows]
    return TableResponse(rows=records, total=total)


@reg.api.route("/ai/asr", methods=["POST"])
@JsonSerializer()
def ai_asr():
    """ASR 语音转写：接收音频上传，调用第三方云 ASR 返回文字；识别的对话同样 token 入库"""
    from owl_ai.util.llm_client import AIGatewayClient, AICallError
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    # 开关控制：关闭时直接拦截，友好提示
    if not _asr_enabled():
        return AjaxResponse.from_error(msg="语音识别功能未开启，请联系管理员")
    file = request.files.get('file')
    if not file or not file.filename:
        return AjaxResponse.from_error(msg="缺少音频文件")
    audio_bytes = file.read()
    if not audio_bytes:
        return AjaxResponse.from_error(msg="音频文件为空")
    try:
        result = AIGatewayClient.call('asr', user_id, audio_bytes=audio_bytes)
    except AICallError as e:
        # 统一返回：超时 / 鉴权 / 限流 / 解析等分类错误
        return AjaxResponse.from_error(msg=f"语音识别失败（{e.category}）：{e.message}")
    except Exception as e:  # noqa: BLE001
        return AjaxResponse.from_error(msg=f"语音识别异常：{e}")
    text = (result.get('text') or '').strip()
    if not text:
        return AjaxResponse.from_error(msg="未识别到有效语音内容")
    return AjaxResponse.from_success(data={"text": text})


@reg.api.route("/ai/config", methods=["GET"])
@JsonSerializer()
def ai_config_get():
    """查询当前用户的 AI 配置状态（不返回明文 Key，返回打码预览）"""
    user_id = SecurityUtil.get_user_id()
    from owl_ai.util.ai_config import get_api_key, get_model, has_api_key, mask_key
    key = get_api_key(user_id)
    return AjaxResponse.from_success(data={
        "configured": has_api_key(user_id),
        "model": get_model(user_id),
        "maskedKey": mask_key(key) if key else '',
        "asrEnabled": _asr_enabled(),
    })


@reg.api.route("/ai/config", methods=["POST"])
@JsonSerializer()
def ai_config_save():
    """保存当前用户的 DeepSeek API Key + 模型（BYOK 模式，key 存本地文件）"""
    user_id = SecurityUtil.get_user_id()
    data = request.get_json(silent=True) or {}
    api_key = (data.get('apiKey') or '').strip()
    model = (data.get('model') or '').strip()
    from owl_ai.util.ai_config import save_config, has_api_key, is_valid_key
    if not api_key and not has_api_key(user_id):
        return AjaxResponse.from_error(msg="API Key 不能为空")
    if api_key and not is_valid_key(api_key):
        return AjaxResponse.from_error(msg="API Key 格式不正确，请检查是否包含空格或非法字符")
    ok = save_config(user_id, api_key, model)
    return AjaxResponse.from_success(msg="保存成功") if ok else AjaxResponse.from_error(msg="保存失败")


@reg.api.route("/ai/config", methods=["DELETE"])
@JsonSerializer()
def ai_config_clear():
    """清除当前用户的 DeepSeek API Key"""
    user_id = SecurityUtil.get_user_id()
    from owl_ai.util.ai_config import clear_config
    ok = clear_config(user_id)
    return AjaxResponse.from_success(msg="已清除") if ok else AjaxResponse.from_error(msg="清除失败")


# ============================================================
# 统一 AI 调用接口（ai_type 路由到 LLM / ASR）
#
# 设计说明：
#   本接口是所有 AI 能力的统一入口，前端/其他服务只对接这一个接口，
#   通过 ai_type 参数自动路由到对应能力，新增能力无需前端改接口。
# ============================================================

@reg.api.route("/ai/unified", methods=["POST"])
@JsonSerializer()
def ai_unified():
    """
    统一 AI 调用接口。

    - JSON 请求（ai_type=llm）：body 携带 messages
    - multipart 请求（ai_type=asr）：上传音频文件（file 字段）

    返回：{'ai_type', 'reply'/'text', 'usage', 'elapsed_ms'}
    """
    # ========== 【临时调试】移除 JWT 鉴权（本地测试，不传 token）==========
    # 调试完成后恢复：删除下面 try/except 整段，替换为这一行：
    #     user_id = SecurityUtil.get_user_id()
    try:
        user_id = SecurityUtil.get_user_id()
    except Exception:  # noqa: BLE001
        user_id = 0  # 未登录时 user_id 兜底为 0（仅本地调试用）
    # ========== 【临时调试】结束 ==========
    from owl_ai.util.llm_client import AIGatewayClient, AICallError

    # JSON 请求 → LLM 文本
    if request.is_json:
        data = request.get_json(silent=True) or {}
        ai_type = (data.get('aiType') or data.get('ai_type') or '').strip()
        if ai_type != 'llm':
            return AjaxResponse.from_error(msg=f"JSON 请求仅支持 ai_type=llm，收到：{ai_type or '空'}")

        messages = data.get('messages')
        session_id = data.get('sessionId') or data.get('session_id')
        stream = data.get('stream', False)

        # 流式返回（SSE 打字机效果）
        if stream:
            from flask import Response, stream_with_context
            import queue
            import threading
            import json as _json

            def generate():
                q = queue.Queue()

                def on_token(t):
                    q.put(('token', t))

                def on_done(full, usage):
                    q.put(('done', {'fullText': full, 'usage': usage}))

                def on_error(err):
                    q.put(('error', err))

                def worker():
                    try:
                        AIGatewayClient.stream_llm(
                            user_id, messages, on_token, on_done, on_error, session_id=session_id
                        )
                    except Exception as e:  # noqa: BLE001
                        q.put(('error', str(e)))
                    finally:
                        q.put(('end', None))

                threading.Thread(target=worker, daemon=True).start()

                while True:
                    item = q.get()
                    kind = item[0]
                    if kind == 'end':
                        break
                    if kind == 'token':
                        yield f"data: {_json.dumps({'token': item[1]}, ensure_ascii=False)}\n\n"
                    elif kind == 'done':
                        yield f"data: {_json.dumps({'done': True, **item[1]}, ensure_ascii=False)}\n\n"
                    elif kind == 'error':
                        yield f"data: {_json.dumps({'error': item[1]}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

            return Response(stream_with_context(generate()), mimetype='text/event-stream')

        # 非流式
        try:
            result = AIGatewayClient.call('llm', user_id=user_id, messages=messages)
            return AjaxResponse.from_success(data=result)
        except AICallError as e:
            return AjaxResponse.from_error(msg=e.message)

    # multipart 请求 → ASR 语音转写
    ai_type = (request.form.get('aiType') or request.form.get('ai_type') or 'asr').strip()
    if ai_type != 'asr':
        return AjaxResponse.from_error(msg=f"multipart 请求仅支持 ai_type=asr，收到：{ai_type or '空'}")
    file = request.files.get('file')
    if not file or file.filename == '':
        return AjaxResponse.from_error(msg="缺少音频文件（file 字段）")
    try:
        result = AIGatewayClient.call('asr', user_id=user_id, audio_bytes=file.read())
        return AjaxResponse.from_success(data=result)
    except AICallError as e:
        return AjaxResponse.from_error(msg=e.message)


# ============================================================
# SSE 流式对话接口（复用 AiChatService 会话管理 + bowl_ai 表）
#
# 改造说明：
#   原 chat.vue 走 HTTP POST 非流式，现在改为对接本 SSE 流式接口，
#   会话列表 / 历史读取 / sessionId 隔离逻辑不变，仍复用 AiChatService。
# ============================================================

@reg.api.route("/ai/chat/stream", methods=["POST"])
def ai_chat_stream():
    """
    SSE 流式对话接口（打字机效果）。

    入参（JSON）：
        message:   用户输入
        sessionId: 会话 ID（可选，不传则新建会话）

    返回（SSE，text/event-stream）：
        data: {"token":"..."}      逐 token 推送
        data: {"done":true,"fullText":"...","sessionId":123,"usage":{...}}
        data: [DONE]
    """
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    session_id = data.get('sessionId') or data.get('session_id')
    # key/model 获取：body 传的优先，兜底从 ai_config.json 按 user_id 读（BYOK，对齐线上原版）
    api_key = (data.get('apiKey') or data.get('api_key') or '').strip()
    model = (data.get('model') or '').strip()
    key_source = 'user' if api_key else None  # body 传的 Key 视为用户自有
    from owl_ai.util.ai_config import get_api_key, get_model
    if not api_key:
        api_key = get_api_key(user_id)  # 模式 B：用户自有 Key（加密存储）
        if api_key:
            key_source = 'user'
    if not api_key:
        # 模式 A：平台全局 Key（受开关 enable_platform_key_fallback 控制）
        if _platform_key_fallback_enabled():
            api_key = _get_platform_api_key()  # 后台参数 ai.platform.api.key > 环境变量 DEEPSEEK_API_KEY
            key_source = 'platform'
        else:
            # 关闭兜底：用户没有自有 Key，直接拦截，不使用平台公共 Key
            import json as _json
            from flask import Response
            err = _json.dumps({"error": "请先在「设置 Key」中绑定你的 API Key（平台已关闭公共 Key 兜底）"}, ensure_ascii=False)
            return Response('data: ' + err + '\n\n', mimetype='text/event-stream')
    if not model:
        model = get_model(user_id) or 'deepseek-chat'

    if not message:
        return AjaxResponse.from_error(msg="消息不能为空")

    # QPS 频率限流：独立于 Token 额度，两种来源（平台 Key / 用户自有 Key）都校验
    qps_ok, qps_msg = _check_qps_limit(user_id, key_source)
    if not qps_ok:
        import json as _json
        from flask import Response
        err = _json.dumps({"error": qps_msg}, ensure_ascii=False)
        return Response('data: ' + err + '\n\n', mimetype='text/event-stream')

    # 平台 Token 额度校验：只统计 key_source='platform' 的记录
    # 用户自有 Key（key_source='user'）不计入平台每日额度，无 token 总量上限
    if key_source == 'platform':
        today_tokens = _get_today_tokens(user_id, 'platform')
        daily_limit = _get_daily_token_limit(user_id)
        if today_tokens >= daily_limit:
            import json as _json
            from flask import Response
            err = _json.dumps({"error": "今日平台Token额度已耗尽，请明天再试"}, ensure_ascii=False)
            return Response('data: ' + err + '\n\n', mimetype='text/event-stream')

    # 构建上下文（含历史摘要 + 近期消息），并保存用户提问
    context, actual_sid = AiChatService.build_context(user_id, session_id, message)

    from flask import Response, stream_with_context, current_app
    # 获取真实 app 对象，worker 线程里做 db 操作时需要手动建立应用上下文
    _app = current_app._get_current_object()
    import queue
    import threading
    import json as _json

    def generate():
        q = queue.Queue()

        logged_sessions = set()  # 记录已入库的 session_id，防止重复入库

        def on_token(t):
            q.put(('token', t))

        def on_done(full, usage):
            # 保存回复（复用现有 save_reply，存 bowl_ai_message）
            try:
                with _app.app_context():
                    AiChatService.save_reply(user_id, actual_sid, message, full)
                    print(f"[SSE流式] save_reply 成功：session_id={actual_sid}")
            except Exception as e:  # noqa: BLE001
                print(f"[SSE流式] save_reply 失败：{e}")

            # token 入库（显式 insert，避免 ai_type 列不存在；同一 session_id 只入库一次）
            if actual_sid in logged_sessions:
                print(f"[SSE流式] 跳过重复入库：session_id={actual_sid}")
            else:
                try:
                    logged_sessions.add(actual_sid)
                    # 优先读接口返回的 usage；没有 usage 时本地估算
                    if usage and (usage.get('total_tokens') or usage.get('prompt_tokens') or usage.get('completion_tokens')):
                        input_tokens = usage.get('prompt_tokens', 0) or 0
                        output_tokens = usage.get('completion_tokens', 0) or 0
                        total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
                        statistics_source = 'api'
                    else:
                        input_tokens = _estimate_tokens(message)
                        output_tokens = _estimate_tokens(full)
                        total_tokens = input_tokens + output_tokens
                        statistics_source = 'local_estimate'
                    print(f"[SSE流式] 入库前 token：session_id={actual_sid}, user_id={user_id}, model={model}, input={input_tokens}, output={output_tokens}, total={total_tokens}, source={statistics_source}")
                    # 计费：根据模型单价计算本次调用费用（元）
                    cost = _calc_cost(model, input_tokens, output_tokens)
                    with _app.app_context():
                        from sqlalchemy import insert
                        ins = insert(AiTokenRecordPo.__table__).values(
                            user_id=user_id, session_id=actual_sid,
                            prompt_tokens=input_tokens,
                            completion_tokens=output_tokens,
                            total_tokens=total_tokens,
                            model=model,
                            statistics_source=statistics_source,
                            cost=cost,
                            key_source=key_source,
                        )
                        db.session.execute(ins)
                        db.session.commit()
                    print(f"[SSE流式] token 入库成功：session_id={actual_sid}, model={model}, source={statistics_source}")
                except Exception as e:  # noqa: BLE001
                    try:
                        db.session.rollback()
                    except Exception:  # noqa: BLE001
                        pass
                    print(f"[SSE流式] token 入库失败：{e}")

            q.put(('done', {'fullText': full, 'sessionId': actual_sid, 'usage': usage}))

        def on_error(err):
            q.put(('error', err))

        def worker():
            try:
                DeepSeekClient.chat_stream(context, on_token=on_token, on_done=on_done, on_error=on_error, api_key=api_key, model=model, user_id=user_id)
            except Exception as e:  # noqa: BLE001
                q.put(('error', str(e)))
            finally:
                q.put(('end', None))

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = q.get()
            kind = item[0]
            if kind == 'end':
                break
            if kind == 'token':
                yield f"data: {_json.dumps({'token': item[1]}, ensure_ascii=False)}\n\n"
            elif kind == 'done':
                yield f"data: {_json.dumps({'done': True, **item[1]}, ensure_ascii=False)}\n\n"
            elif kind == 'error':
                yield f"data: {_json.dumps({'error': item[1]}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@reg.api.route("/ai/chat/history", methods=["GET"])
@JsonSerializer()
def ai_chat_history():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("请先登录")
    sessions = AiChatService.get_user_sessions(user_id)
    return AjaxResponse.from_success(data=sessions)


@reg.api.route("/ai/chat/history/<int:session_id>", methods=["GET"])
@JsonSerializer()
def ai_chat_session_detail(session_id):
    try:
        user_id = SecurityUtil.get_user_id()
        if not user_id:
            return AjaxResponse.from_error(msg="请先登录")
        messages = AiChatService.get_session_messages(session_id, user_id)
        return AjaxResponse.from_success(data=messages)
    except Exception:
        return AjaxResponse.from_error(msg="查询失败")


@reg.api.route("/ai/chat/history/<int:session_id>", methods=["DELETE"])
@JsonSerializer()
def ai_chat_delete_session(session_id):
    try:
        user_id = SecurityUtil.get_user_id()
        if not user_id:
            return AjaxResponse.from_error(msg="请先登录")
        AiChatService.delete_session(session_id, user_id)
        return AjaxResponse.from_success(msg="对话已删除")
    except Exception as e:
        return AjaxResponse.from_error(msg=str(e) if str(e) else "删除失败")


@reg.api.route("/ai/chat/history/<int:session_id>/rename", methods=["PUT"])
@JsonSerializer()
def ai_chat_rename_session(session_id):
    """重命名会话标题"""
    try:
        user_id = SecurityUtil.get_user_id()
        if not user_id:
            return AjaxResponse.from_error(msg="请先登录")
        data = request.get_json() or {}
        new_title = (data.get('title') or '').strip()
        if not new_title:
            return AjaxResponse.from_error(msg="标题不能为空")
        from owl_ai.mapper import AiSessionMapper
        session = AiSessionMapper.select_by_id(session_id)
        if not session or session.user_id != user_id:
            return AjaxResponse.from_error(msg="会话不存在或无权操作")
        AiSessionMapper.update_session(session_id, title=new_title)
        return AjaxResponse.from_success(msg="重命名成功")
    except Exception:
        return AjaxResponse.from_error(msg="重命名失败")


@reg.api.route("/ai/chat/history/clear", methods=["POST"])
def ai_chat_clear_all():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("请先登录")
    AiChatService.clear_all_sessions(user_id)
    return AjaxResponse.from_success(msg="已清空所有对话")


@reg.api.route("/ai/chat", methods=["POST"])
@JsonSerializer()
def ai_chat_http():
    try:
        user_id = SecurityUtil.get_user_id()
        if not user_id:
            return AjaxResponse.from_error(msg="请先登录")
        if not _check_rate_limit(user_id):
            return AjaxResponse.from_error(msg=f"今日对话次数已达上限（{DAILY_LIMIT}次）")

        data = request.get_json() or {}
        msg = data.get('message', '').strip()
        session_id = data.get('sessionId', None)
        if not msg:
            return AjaxResponse.from_error(msg="消息不能为空")

        context, actual_sid = AiChatService.build_context(user_id, session_id, msg)
        api_key = DeepSeekClient._get_api_key(user_id)
        if not api_key:
            return AjaxResponse.from_error(msg="请先配置 DeepSeek API Key（点击右上角「设置 Key」）")

        usage = None
        result = DeepSeekClient.chat_sync_with_tools(context, user_id)
        reply_text = result.get("reply") if result else None
        usage = result.get("usage") if result else None

        reply_text = reply_text or "模型暂无有效回复，请换个问题重试"
        new_sid = AiChatService.save_reply(user_id, actual_sid, msg, reply_text)

        if usage and usage.get('total_tokens', 0) > 0:
            try:
                record = AiTokenRecordPo(
                    user_id=user_id, session_id=new_sid,
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0),
                    model=DeepSeekClient._get_model(user_id)
                )
                db.session.add(record)
                db.session.commit()
            except Exception:
                pass

        return AjaxResponse.from_success(data={"sessionId": new_sid, "reply": reply_text})
    except Exception:
        return AjaxResponse.from_error(msg="AI 服务异常，请稍后重试")


# ==================== 后台管理（admin 专用） ====================

@reg.api.route("/admin/ai/sessions", methods=["GET"])
@JsonSerializer()
def admin_ai_sessions():
    user_id = SecurityUtil.get_user_id()
    if not user_id or not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    from owl_ai.mapper import AiSessionMapper
    sessions = AiSessionMapper.select_all()
    data = [{"sessionId": s.session_id, "userId": s.user_id, "title": s.title, "messageCount": s.message_count, "createTime": str(s.create_time)} for s in sessions]
    return AjaxResponse.from_success(data=data)


@reg.api.route("/admin/ai/session/<int:session_id>", methods=["DELETE"])
def admin_ai_delete_session(session_id):
    user_id = SecurityUtil.get_user_id()
    if not user_id or not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    AiChatService.delete_session_admin(session_id)
    return AjaxResponse.from_success(msg="已删除")


# ==================== Token 统计（admin 专用） ====================

from owl_system.domain.po import SysUserPo

@reg.api.route("/admin/ai/users", methods=["GET"])
@JsonSerializer()
def admin_ai_users():
    """用户下拉列表"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    rows = db.session.execute(select(SysUserPo.user_id, SysUserPo.user_name, SysUserPo.nick_name).order_by(SysUserPo.user_id)).all()
    return AjaxResponse.from_success(data=[{"userId": r.user_id, "userName": r.user_name, "nickName": r.nick_name} for r in rows])


@reg.api.route("/admin/ai/token-records", methods=["GET"])
@JsonSerializer()
def admin_ai_token_records():
    """分页 + 左联用户表查用户名"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    page_num = int(request.args.get('pageNum', 1))
    page_size = min(int(request.args.get('pageSize', 20)), 100)
    filter_user = request.args.get('userId', '').strip()
    date_from = request.args.get('dateFrom', '').strip()
    date_to = request.args.get('dateTo', '').strip()

    # 后端校验：开始日期 <= 结束日期（不依赖前端，选反了自动交换）
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    # 单表显式列查询（不查 ai_type / input_tokens / output_tokens，本地表可能没有这些列）
    columns = [
        AiTokenRecordPo.id, AiTokenRecordPo.user_id, AiTokenRecordPo.session_id,
        AiTokenRecordPo.prompt_tokens, AiTokenRecordPo.completion_tokens,
        AiTokenRecordPo.total_tokens, AiTokenRecordPo.model, AiTokenRecordPo.create_time,
        AiTokenRecordPo.statistics_source,
        BowlAiSession.title,
        SysUserPo.user_name, SysUserPo.nick_name,
    ]

    conditions = []
    if filter_user:
        try:
            conditions.append(AiTokenRecordPo.user_id == int(filter_user))
        except ValueError:
            pass
    if date_from:
        try:
            conditions.append(AiTokenRecordPo.create_time >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            # 结束日期 +1 天，包含结束当天
            conditions.append(AiTokenRecordPo.create_time < datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass

    stmt = select(*columns).outerjoin(BowlAiSession, AiTokenRecordPo.session_id == BowlAiSession.session_id).outerjoin(SysUserPo, AiTokenRecordPo.user_id == SysUserPo.user_id).where(*conditions).order_by(AiTokenRecordPo.create_time.desc())
    count_stmt = select(func.count()).select_from(AiTokenRecordPo).where(*conditions)
    total = db.session.execute(count_stmt).scalar() or 0
    rows = db.session.execute(stmt.limit(page_size).offset((page_num-1)*page_size)).all()

    records = [{
        "id": r[0],
        "userId": r[1],
        "sessionId": r[2],
        "promptTokens": r[3],
        "completionTokens": r[4],
        "totalTokens": r[5],
        "model": r[6],
        "createTime": (r[7] + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if r[7] else '',
        "statisticsSource": r[8] or 'api',
        "sessionTitle": r[9] or '',
        "userName": r[10] or '',
        "nickName": r[11] or '',
    } for r in rows]
    return TableResponse(rows=records, total=total)


@reg.api.route("/admin/ai/token-summary", methods=["GET"])
@JsonSerializer()
def admin_ai_token_summary():
    """汇总统计"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    try:
        today_start, today_end = _today_range_cst()
        daily_stmt = select(func.count(AiTokenRecordPo.id), func.sum(AiTokenRecordPo.total_tokens), func.sum(AiTokenRecordPo.prompt_tokens), func.sum(AiTokenRecordPo.completion_tokens), func.coalesce(func.sum(AiTokenRecordPo.cost), 0)).where(AiTokenRecordPo.create_time >= today_start, AiTokenRecordPo.create_time < today_end)
        daily_row = db.session.execute(daily_stmt).one_or_none()
        total_stmt = select(func.count(AiTokenRecordPo.id), func.sum(AiTokenRecordPo.total_tokens), func.coalesce(func.sum(AiTokenRecordPo.cost), 0))
        total_row = db.session.execute(total_stmt).one_or_none()
        return AjaxResponse.from_success(data={
            "dailyCalls": int(daily_row[0] or 0) if daily_row else 0,
            "dailyTokens": int(daily_row[1] or 0) if daily_row else 0,
            "dailyPromptTokens": int(daily_row[2] or 0) if daily_row else 0,
            "dailyCompletionTokens": int(daily_row[3] or 0) if daily_row else 0,
            "dailyCost": round(float(daily_row[4] or 0), 4) if daily_row else 0,
            "totalCalls": int(total_row[0] or 0) if total_row else 0,
            "totalTokens": int(total_row[1] or 0) if total_row else 0,
            "totalCost": round(float(total_row[2] or 0), 4) if total_row else 0,
        })
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_success(data={
            "dailyCalls": 0, "dailyTokens": 0, "dailyPromptTokens": 0,
            "dailyCompletionTokens": 0, "dailyCost": 0, "totalCalls": 0, "totalTokens": 0, "totalCost": 0,
        })


@reg.api.route("/admin/ai/provider-success-rate", methods=["GET"])
@JsonSerializer()
def admin_ai_provider_success_rate():
    """各模型服务商接口成功率统计（供后台监控容灾切换效果）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        from owl_ai.domain.po import AiProviderCallLogPo
        stmt = select(
            AiProviderCallLogPo.provider,
            AiProviderCallLogPo.model,
            func.count().label('total'),
            func.sum(AiProviderCallLogPo.success).label('success_count'),
            func.avg(AiProviderCallLogPo.latency_ms).label('avg_latency'),
        ).group_by(AiProviderCallLogPo.provider, AiProviderCallLogPo.model).order_by(AiProviderCallLogPo.provider)
        rows = db.session.execute(stmt).all()
        data = []
        for r in rows:
            total = int(r.total or 0)
            success = int(r.success_count or 0)
            data.append({
                "provider": r.provider or '',
                "model": r.model or '',
                "total": total,
                "success": success,
                "failed": total - success,
                "successRate": round(success * 100.0 / total, 2) if total else 0.0,
                "avgLatencyMs": int(r.avg_latency or 0),
            })
        return AjaxResponse.from_success(data=data)
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_success(data=[])


@reg.api.route("/admin/ai/platform-key", methods=["GET"])
@JsonSerializer()
def admin_ai_platform_key_get():
    """查询平台全局 Key 配置状态（打码预览，不返回明文）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    from owl_ai.util.ai_config import mask_key
    key = _get_platform_api_key()
    return AjaxResponse.from_success(data={
        "configured": bool(key),
        "maskedKey": mask_key(key) if key else '',
    })


@reg.api.route("/admin/ai/platform-key", methods=["POST"])
@JsonSerializer()
def admin_ai_platform_key_save():
    """保存平台全局 Key（加密存数据库，无需改 yaml 重启服务）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    data = request.get_json(silent=True) or {}
    api_key = (data.get('apiKey') or '').strip()
    if not api_key:
        return AjaxResponse.from_error(msg="平台 API Key 不能为空")
    from owl_ai.util.ai_config import is_valid_key
    if not is_valid_key(api_key):
        return AjaxResponse.from_error(msg="API Key 格式不正确，请检查是否包含空格或非法字符")
    try:
        from owl_system.mapper import SysConfigMapper
        from owl_system.service import SysConfigService
        from owl_system.domain.entity import SysConfig
        encrypted = _encrypt_platform_key(api_key)
        existing = SysConfigMapper.select_config(SysConfig(config_key="ai.platform.api.key"))
        if existing and existing.config_id:
            existing.config_value = encrypted
            existing.update_by_user(SecurityUtil.get_username())
            SysConfigService.update_config(existing)
        else:
            cfg = SysConfig(
                config_name="平台全局API Key",
                config_key="ai.platform.api.key",
                config_value=encrypted,
                config_type="N",
                remark="平台共用的 AI API Key（加密存储，无需改 yaml 即可生效）",
            )
            cfg.create_by_user(SecurityUtil.get_username())
            SysConfigService.insert_config(cfg)
        return AjaxResponse.from_success(msg="平台全局 Key 已保存")
    except Exception as e:  # noqa: BLE001
        return AjaxResponse.from_error(msg=f"保存失败：{e}")


@reg.api.route("/admin/ai/platform-key", methods=["DELETE"])
@JsonSerializer()
def admin_ai_platform_key_clear():
    """清除平台全局 Key"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        from owl_system.mapper import SysConfigMapper
        from owl_system.service import SysConfigService
        from owl_system.domain.entity import SysConfig
        existing = SysConfigMapper.select_config(SysConfig(config_key="ai.platform.api.key"))
        if existing and existing.config_id:
            SysConfigService.delete_config_by_ids([existing.config_id])
        return AjaxResponse.from_success(msg="平台全局 Key 已清除")
    except Exception as e:  # noqa: BLE001
        return AjaxResponse.from_error(msg=f"清除失败：{e}")


@reg.api.route("/admin/ai/token-chart", methods=["GET"])
@JsonSerializer()
def admin_ai_token_chart():
    """Token 监控报表数据：最近 14 天每日消耗趋势 + 各模型用量（供 ECharts 展示）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        today_start, _ = _today_range_cst()
        daily_trend = []
        for i in range(13, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            stmt = select(func.coalesce(func.sum(AiTokenRecordPo.total_tokens), 0)).where(
                AiTokenRecordPo.create_time >= day_start,
                AiTokenRecordPo.create_time < day_end,
            )
            tokens = int(db.session.execute(stmt).scalar() or 0)
            daily_trend.append({"date": (day_start + timedelta(hours=8)).strftime('%m-%d'), "tokens": tokens})
        model_stmt = select(
            AiTokenRecordPo.model,
            func.count(),
            func.coalesce(func.sum(AiTokenRecordPo.total_tokens), 0),
        ).group_by(AiTokenRecordPo.model).order_by(func.sum(AiTokenRecordPo.total_tokens).desc())
        model_usage = [{"model": r[0] or 'unknown', "count": int(r[1] or 0), "tokens": int(r[2] or 0)} for r in db.session.execute(model_stmt).all()]
        return AjaxResponse.from_success(data={"dailyTrend": daily_trend, "modelUsage": model_usage})
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_success(data={"dailyTrend": [], "modelUsage": []})


@reg.api.route("/admin/ai/call-logs", methods=["GET"])
@JsonSerializer()
def admin_ai_call_logs():
    """调用日志列表：时间、用户、模型、耗时、状态、失败原因，支持简单筛选"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        from owl_ai.domain.po import AiProviderCallLogPo
        page_num = int(request.args.get('pageNum', 1))
        page_size = min(int(request.args.get('pageSize', 20)), 100)
        status = request.args.get('status', '').strip()
        model = request.args.get('model', '').strip()
        conditions = []
        if status == 'success':
            conditions.append(AiProviderCallLogPo.success == 1)
        elif status == 'failed':
            conditions.append(AiProviderCallLogPo.success == 0)
        if model:
            conditions.append(AiProviderCallLogPo.model.like(f'%{model}%'))
        columns = [
            AiProviderCallLogPo.id, AiProviderCallLogPo.user_id,
            AiProviderCallLogPo.provider, AiProviderCallLogPo.model,
            AiProviderCallLogPo.success, AiProviderCallLogPo.error_category,
            AiProviderCallLogPo.error_message, AiProviderCallLogPo.latency_ms,
            AiProviderCallLogPo.create_time,
        ]
        stmt = select(*columns).where(*conditions).order_by(AiProviderCallLogPo.id.desc())
        count_stmt = select(func.count()).select_from(AiProviderCallLogPo).where(*conditions)
        total = db.session.execute(count_stmt).scalar() or 0
        rows = db.session.execute(stmt.limit(page_size).offset((page_num - 1) * page_size)).all()
        records = [{
            "id": r[0],
            "userId": r[1],
            "provider": r[2] or '',
            "model": r[3] or '',
            "success": r[4] == 1,
            "errorCategory": r[5] or '',
            "errorMessage": r[6] or '',
            "latencyMs": r[7] or 0,
            "createTime": (r[8] + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if r[8] else '',
        } for r in rows]
        return TableResponse(rows=records, total=total)
    except Exception:
        traceback.print_exc()
        return TableResponse(rows=[], total=0)


@reg.api.route("/admin/ai/platform-key-alert", methods=["GET"])
@JsonSerializer()
def admin_ai_platform_key_alert():
    """平台 Key 余额/失效告警：基于最近 24 小时调用日志的 auth/402 失败判断"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        from owl_ai.domain.po import AiProviderCallLogPo
        since = datetime.now() - timedelta(hours=24)
        stmt = select(func.count()).where(
            AiProviderCallLogPo.success == 0,
            AiProviderCallLogPo.error_category.in_(['auth', 'http_402']),
            AiProviderCallLogPo.create_time >= since,
        )
        fail_count = db.session.execute(stmt).scalar() or 0
        alert = int(fail_count) > 0
        return AjaxResponse.from_success(data={
            "alert": alert,
            "failCount": int(fail_count),
            "reason": f"平台 Key 最近 24 小时出现 {int(fail_count)} 次鉴权/余额不足失败，请检查额度或更换 Key" if alert else '',
        })
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_success(data={"alert": False, "failCount": 0, "reason": ""})


@reg.api.route("/admin/ai/asr", methods=["GET"])
@JsonSerializer()
def admin_ai_asr_status():
    """查询 ASR 语音识别开关状态（管理员）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    return AjaxResponse.from_success(data={"enabled": _asr_enabled()})


@reg.api.route("/admin/ai/asr", methods=["POST"])
@JsonSerializer()
def admin_ai_asr_toggle():
    """开启/关闭 ASR 语音识别（后台开关，存 sys_config）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get('enabled', False))
    try:
        from owl_system.mapper import SysConfigMapper
        from owl_system.service import SysConfigService
        from owl_system.domain.entity import SysConfig
        value = 'true' if enabled else 'false'
        existing = SysConfigMapper.select_config(SysConfig(config_key="ai.asr.enabled"))
        if existing and existing.config_id:
            existing.config_value = value
            existing.update_by_user(SecurityUtil.get_username())
            SysConfigService.update_config(existing)
        else:
            cfg = SysConfig(
                config_name="AI语音识别开关",
                config_key="ai.asr.enabled",
                config_value=value,
                config_type="N",
                remark="是否开启语音识别（true开启/false关闭，默认关闭）",
            )
            cfg.create_by_user(SecurityUtil.get_username())
            SysConfigService.insert_config(cfg)
        return AjaxResponse.from_success(msg="已" + ("开启" if enabled else "关闭") + "语音识别")
    except Exception as e:  # noqa: BLE001
        return AjaxResponse.from_error(msg=f"操作失败：{e}")


@reg.api.route("/admin/ai/model-prices", methods=["GET"])
@JsonSerializer()
def admin_ai_model_prices():
    """查询模型单价配置列表（计费用，单位 元/百万 token）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    try:
        from owl_ai.domain.po import AiModelPricePo
        rows = db.session.execute(select(AiModelPricePo).order_by(AiModelPricePo.id)).scalars().all()
        data = [{"id": p.id, "model": p.model, "provider": p.provider or '', "inputPrice": p.input_price or 0, "outputPrice": p.output_price or 0} for p in rows]
        return AjaxResponse.from_success(data=data)
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_success(data=[])


@reg.api.route("/admin/ai/model-price", methods=["POST"])
@JsonSerializer()
def admin_ai_model_price_save():
    """保存/更新模型单价（管理员配置计费单价）"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("无权访问")
    data = request.get_json(silent=True) or {}
    model = (data.get('model') or '').strip()
    if not model:
        return AjaxResponse.from_error(msg="模型名不能为空")
    try:
        from owl_ai.domain.po import AiModelPricePo
        input_price = float(data.get('inputPrice', 0) or 0)
        output_price = float(data.get('outputPrice', 0) or 0)
        provider = (data.get('provider') or '').strip()
        existing = db.session.execute(select(AiModelPricePo).where(AiModelPricePo.model == model)).scalar_one_or_none()
        if existing:
            existing.input_price = input_price
            existing.output_price = output_price
            existing.provider = provider
        else:
            db.session.add(AiModelPricePo(model=model, provider=provider, input_price=input_price, output_price=output_price))
        db.session.commit()
        return AjaxResponse.from_success(msg="模型单价已保存")
    except Exception as e:  # noqa: BLE001
        try:
            db.session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return AjaxResponse.from_error(msg=f"保存失败：{e}")


# ==================== SocketIO ====================

@socketio.on('ai-chat', namespace='/ai')
def ai_chat_socket(data):
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        emit('ai-error', {'msg': '请先登录'})
        return
    if not _check_rate_limit(user_id):
        emit('ai-error', {'msg': f'今日对话次数已达上限（{DAILY_LIMIT}次），请明天再来'})
        return
    msg = data.get('message', '').strip()
    session_id = data.get('sessionId', None)
    if not msg: emit('ai-error', {'msg': '消息不能为空'}); return
    context, actual_sid = AiChatService.build_context(user_id, session_id, msg)
    def on_token(token): socketio.emit('ai-token', {'token': token}, namespace='/ai', room=request.sid)
    def on_done(full_text, usage=None): socketio.emit('ai-done', {'fullText': full_text, 'sessionId': AiChatService.save_reply(user_id, actual_sid, msg, full_text)}, namespace='/ai', room=request.sid)
    def on_error(err): socketio.emit('ai-error', {'msg': err}, namespace='/ai', room=request.sid)
    DeepSeekClient.chat_stream(context, on_token=on_token, on_done=on_done, on_error=on_error, user_id=user_id)