# -*- coding: utf-8 -*-

"""
WebSocket 实时通信事件处理器。

使用 Flask-SocketIO 实现异步实时推送；
用户连接后自动加入私有的通知房间（room:user:{user_id}），
服务端通过房间精准推送，避免全量广播。
"""

import traceback
from flask import request
from flask_socketio import emit, join_room, disconnect

from owl_admin.ext import socketio
from owl_common.utils import security_util as SecurityUtil


@socketio.on('connect')
def handle_connect(auth=None):
    """
    客户端连接事件
    Flask-SocketIO 会传入 auth 参数（客户端 connect(token) 携带），
    从 auth 中提取 token，验证并加入用户专属通知房间
    """
    try:
        # 优先从 auth 取 token，其次从 query string 取
        token = None
        if isinstance(auth, dict):
            token = auth.get('token', '')
        if not token:
            token = request.args.get('token', '')
        if token:
            from owl_framework.service.token import TokenService
            # get_login_user 内部调用 get_token(request) 从 headers 取 token，
            # WebSocket 场景下请求头不可靠，改用 parse_token 直接解析
            try:
                claims = TokenService.parse_token(token)
                if claims:
                    from owl_common.constant import Constants
                    token_uuid = claims.get(Constants.LOGIN_USER_KEY)
                    if token_uuid:
                        from owl_admin.ext import redis_cache
                        jsoned_user = redis_cache.get(TokenService.get_token_key(token_uuid))
                        if jsoned_user:
                            from owl_common.domain.entity import LoginUser
                            login_user = LoginUser.model_validate_json(jsoned_user)
                            if login_user:
                                room = f"user:{login_user.user_id}"
                                join_room(room)
                                emit('connected', {'status': 'ok', 'user_id': login_user.user_id})
                                return
            except Exception:
                pass  # 解析失败继续走匿名逻辑
    except Exception:
        traceback.print_exc()
    # 认证失败不立即断开，允许匿名连接（仅接收公开事件）
    emit('connected', {'status': 'anonymous'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    pass