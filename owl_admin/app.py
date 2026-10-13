# -*- coding: utf-8 -*-
# @Author  : shaw-lee

"""
Flask 应用工厂。

负责创建 Flask 应用实例，初始化数据库、Redis、CORS、登录管理等扩展，
并注册全局统一异常处理器（业务异常、HTTP 异常、未知异常），
使 Controller 无需在业务代码中重复编写 try/except。
"""

import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# 加载 .env 环境变量（密钥、数据库密码等敏感配置）
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
except ImportError:
    pass

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from owl_common.exception import ServiceException
from owl_common.base.model import AjaxResponse
from owl_common.utils.base import UtilException


def create_app() -> Flask:
    """
    创建flask应用
    
    Returns:
        Flask: flask应用
    """
    from owl_admin.ext import db, fredis, lm, cors, owl, socketio
    from owl_common.base.signal import app_completed

    app = Flask(__name__, static_folder=None)

    owl.init_app(app, PROJECT_ROOT)
    cors.init_app(app)
    fredis.init_app(app)
    db.init_app(app)
    lm.init_app(app)
    socketio.init_app(app)

    # ============================================================
    # 全局统一异常处理
    # ============================================================

    @app.errorhandler(ServiceException)
    def handle_service_exception(e: ServiceException):
        """业务异常：如参数错误、无权限、资源不存在等"""
        return jsonify(AjaxResponse.from_error(
            code=e.code,
            msg=e.description
        ).model_dump(by_alias=True)), 200

    @app.errorhandler(UtilException)
    def handle_util_exception(e: UtilException):
        """工具类异常：如获取当前登录用户失败（未登录/登录已过期）"""
        return jsonify(AjaxResponse.from_error(
            code=getattr(e, 'status', 500),
            msg=str(e)
        ).model_dump(by_alias=True)), 200

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """HTTP层异常：如404页面不存在、405方法不允许等"""
        return jsonify(AjaxResponse.from_error(
            code=e.code or 500,
            msg=e.description or '请求异常'
        ).model_dump(by_alias=True)), 200

    @app.errorhandler(Exception)
    def handle_unknown_exception(e: Exception):
        """未知异常：捕获所有未处理的异常，打印堆栈后返回500"""
        traceback.print_exc()
        return jsonify(AjaxResponse.from_error(
            code=500,
            msg='服务器内部错误'
        ).model_dump(by_alias=True)), 200

    app_completed.send(app)
    
    # 延迟导入 WebSocket 事件处理器（不作为 HTTP 路由注册）
    import owl_admin.ws_events  # noqa: F401
    
    return app


if __name__ == "__main__":
    app = create_app()
    from owl_admin.ext import socketio
    socketio.run(app,
        load_dotenv=False,
        host=app.config.get('SERVER_HOST'),
        port=app.config.get('SERVER_PORT'),
        allow_unsafe_werkzeug=True
    )
