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
from owl_ai.domain.po import AiTokenRecordPo
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.serializer import JsonSerializer
from sqlalchemy import select, func
from datetime import datetime, timedelta

RATE_LIMIT_PREFIX = "ai:rate:user:"
DAILY_LIMIT = 30


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

        context = AiChatService.build_context(user_id, session_id, msg)
        usage = None
        has_key = bool(DeepSeekClient.API_KEY and DeepSeekClient.API_KEY.strip())

        if has_key:
            result = DeepSeekClient.chat_sync_with_tools(context, user_id)
            reply_text = result.get("reply") if result else None
            usage = result.get("usage") if result else None
        else:
            reply_text = DeepSeekClient.chat_sync(context)

        reply_text = reply_text or "模型暂无有效回复，请换个问题重试"
        new_sid = AiChatService.save_reply(user_id, session_id, msg, reply_text)

        if usage and usage.get('total_tokens', 0) > 0:
            try:
                record = AiTokenRecordPo(
                    user_id=user_id, session_id=new_sid,
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0),
                    model=DeepSeekClient.MODEL
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
    try:
        page_num = int(request.args.get('pageNum', 1))
        page_size = min(int(request.args.get('pageSize', 20)), 100)
        filter_user = request.args.get('userId', '').strip()
        date_from = request.args.get('dateFrom', '').strip()
        date_to = request.args.get('dateTo', '').strip()

        stmt = select(AiTokenRecordPo, SysUserPo.user_name, SysUserPo.nick_name).outerjoin(SysUserPo, AiTokenRecordPo.user_id == SysUserPo.user_id)
        if filter_user:
            try: stmt = stmt.where(AiTokenRecordPo.user_id == int(filter_user))
            except ValueError: pass
        if date_from:
            try: stmt = stmt.where(AiTokenRecordPo.create_time >= datetime.strptime(date_from, '%Y-%m-%d'))
            except ValueError: pass
        if date_to:
            try: stmt = stmt.where(AiTokenRecordPo.create_time < datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
            except ValueError: pass
        stmt = stmt.order_by(AiTokenRecordPo.create_time.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.session.execute(count_stmt).scalar() or 0
        rows = db.session.execute(stmt.limit(page_size).offset((page_num-1)*page_size)).all()

        records = [{
            "id": r[0].id,
            "userId": r[0].user_id,
            "userName": r[1] or '',
            "nickName": r[2] or '',
            "sessionId": r[0].session_id,
            "promptTokens": r[0].prompt_tokens,
            "completionTokens": r[0].completion_tokens,
            "totalTokens": r[0].total_tokens,
            "model": r[0].model,
            "createTime": str(r[0].create_time) if r[0].create_time else ''
        } for r in rows]
        return TableResponse(rows=records, total=total)
    except Exception:
        return AjaxResponse.from_error(msg="查询失败，请稍后重试")


@reg.api.route("/admin/ai/token-summary", methods=["GET"])
@JsonSerializer()
def admin_ai_token_summary():
    """汇总统计"""
    if not _is_admin():
        from owl_common.exception import UnauthorizedException; raise UnauthorizedException("无权访问")
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today + timedelta(days=1), datetime.min.time())
        daily_stmt = select(func.count(AiTokenRecordPo.id), func.sum(AiTokenRecordPo.total_tokens), func.sum(AiTokenRecordPo.prompt_tokens), func.sum(AiTokenRecordPo.completion_tokens)).where(AiTokenRecordPo.create_time >= today_start, AiTokenRecordPo.create_time < today_end)
        daily_row = db.session.execute(daily_stmt).one_or_none()
        total_stmt = select(func.count(AiTokenRecordPo.id), func.sum(AiTokenRecordPo.total_tokens))
        total_row = db.session.execute(total_stmt).one_or_none()
        return AjaxResponse.from_success(data={
            "dailyCalls": int(daily_row[0] or 0) if daily_row else 0,
            "dailyTokens": int(daily_row[1] or 0) if daily_row else 0,
            "dailyPromptTokens": int(daily_row[2] or 0) if daily_row else 0,
            "dailyCompletionTokens": int(daily_row[3] or 0) if daily_row else 0,
            "totalCalls": int(total_row[0] or 0) if total_row else 0,
            "totalTokens": int(total_row[1] or 0) if total_row else 0
        })
    except Exception:
        return AjaxResponse.from_error(msg="查询失败，请稍后重试")


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
    context = AiChatService.build_context(user_id, session_id, msg)
    def on_token(token): socketio.emit('ai-token', {'token': token}, namespace='/ai', room=request.sid)
    def on_done(full_text): socketio.emit('ai-done', {'fullText': full_text, 'sessionId': AiChatService.save_reply(user_id, session_id, msg, full_text)}, namespace='/ai', room=request.sid)
    def on_error(err): socketio.emit('ai-error', {'msg': err}, namespace='/ai', room=request.sid)
    DeepSeekClient.chat_stream(context, on_token=on_token, on_done=on_done, on_error=on_error)