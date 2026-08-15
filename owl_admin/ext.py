# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from werkzeug.local import LocalProxy
from flask import current_app

from flask_redis import FlaskRedis
from flask_login import LoginManager
from flask_cors import CORS
from redis import Redis

from owl_common.owl.extension import FlaskOwl
from owl_common.sqlalchemy.extension import SQLAlchemy
     

owl = FlaskOwl()

# WebSocket 实时通信（Tier3 新增）
# 开发环境暂不初始化（werkzeug 不兼容），部署时用 gunicorn+eventlet 启用
import os
_deploy_env = os.environ.get('FLASK_ENV', 'development')
if _deploy_env == 'production':
    from flask_socketio import SocketIO
    socketio = SocketIO(
        cors_allowed_origins=["http://localhost:80", "http://localhost:1024", "http://127.0.0.1:80", "http://127.0.0.1:1024"],
        logger=False,
        engineio_logger=False
    )
else:
    # 开发环境：提供空占位实例，防止 import 报错
    class _StubSocketIO:
        def init_app(self, app): pass
        def on(self, *args, **kwargs): return lambda f: f
        def emit(self, *args, **kwargs): pass
        def run(self, app, **kwargs):
            host = kwargs.get('host', '127.0.0.1')
            port = kwargs.get('port', 9000)
            debug = kwargs.get('debug', False)
            app.run(host=host, port=port, debug=debug)
    socketio = _StubSocketIO()

# CORS 跨域配置（精准指定前端域名，禁止 * 通配符）
# 注意：SocketIO 的 cors_allowed_origins 只对 WebSocket 握手生效
#       HTTP REST 接口的跨域由 Flask-CORS 独立控制，两者必须分别配置
cors = CORS(
    resources={
        r"/*": {
            "origins": [
                "http://localhost:80",
                "http://localhost:1024",
                "http://127.0.0.1:80",
                "http://127.0.0.1:1024"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "expose_headers": ["Set-Cookie"]
        }
    }
)

fredis = FlaskRedis()
redis_cache:Redis = LocalProxy(
    lambda: current_app.extensions["redis"]._redis_client
) 
lm = LoginManager()
db = SQLAlchemy()
