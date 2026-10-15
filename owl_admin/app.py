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

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from owl_common.exception import ServiceException
from owl_common.base.model import AjaxResponse
from owl_common.utils.base import UtilException


def _resolve_frontend_dir() -> str:
    """前端构建产物目录（开发环境 owl-ui/dist；打包环境 _MEIPASS 解包目录）"""
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = PROJECT_ROOT
    return os.path.join(base, 'owl-ui', 'dist')


def _resolve_data_dir() -> str:
    """数据目录（数据库/上传文件）：开发环境 instance/，打包环境 exe 同目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.join(PROJECT_ROOT, 'instance')


def _init_database_file():
    """打包环境：首次启动时把种子 app.db 复制到 exe 同目录（可写）"""
    if not getattr(sys, 'frozen', False):
        return
    target = os.path.join(_resolve_data_dir(), 'app.db')
    if not os.path.exists(target):
        import shutil
        src = os.path.join(getattr(sys, '_MEIPASS', ''), 'app.db')
        if os.path.exists(src):
            shutil.copyfile(src, target)


def _init_upload_files():
    """打包环境：首次启动把种子图片复制到 exe 同目录的 uploads（可写，支持新上传）"""
    if not getattr(sys, 'frozen', False):
        return
    import shutil
    src = os.path.join(getattr(sys, '_MEIPASS', ''), 'uploads')
    dst = os.path.join(_resolve_data_dir(), 'uploads')
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copytree(src, dst)


def create_app() -> Flask:
    """
    创建flask应用
    
    Returns:
        Flask: flask应用
    """
    from owl_admin.ext import db, lm, cors, owl, socketio, redis_cache, USE_REAL_REDIS
    from owl_common.base.signal import app_completed

    app = Flask(__name__, static_folder=None)

    owl.init_app(app, PROJECT_ROOT)

    # 打包环境：数据库指向 exe 同目录（可写），首次启动复制种子数据
    if getattr(sys, 'frozen', False):
        _init_database_file()
        _init_upload_files()
        db_path = os.path.join(_resolve_data_dir(), 'app.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')

    cors.init_app(app)
    db.init_app(app)
    if USE_REAL_REDIS:
        redis_cache.init_app(app)
    lm.init_app(app)
    socketio.init_app(app)

    # SQLite 场景：自动建表（幂等，已存在的表会跳过）
    with app.app_context():
        db.create_all()

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

    # ============================================================
    # 前端静态资源托管（打包版：前端 build 后由 Flask 同源托管）
    # ============================================================
    frontend_dir = _resolve_frontend_dir()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.isfile(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, 'index.html')

    # 打包版前端 baseURL 为 /prod-api，剥掉前缀后交给后端 API 路由
    class _ProdApiPrefixMiddleware:
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            path = environ.get('PATH_INFO', '')
            if path.startswith('/prod-api'):
                environ['PATH_INFO'] = path[len('/prod-api'):] or '/'
            return self.wsgi_app(environ, start_response)

    app.wsgi_app = _ProdApiPrefixMiddleware(app.wsgi_app)

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
