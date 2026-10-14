# -*- coding: utf-8 -*-
"""
打包入口脚本（PyInstaller 打包时使用）。

双击 exe 后：切换到 exe 目录 → 创建 Flask 应用 → 启动服务 → 自动打开浏览器。
"""

import os
import sys


def _open_browser(url: str):
    """延时打开默认浏览器（避免与启动日志抢输出）"""
    try:
        import webbrowser
        import threading
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    except Exception:
        pass


def main():
    # 打包环境：把工作目录切到 exe 所在目录，保证 uploads/logs 等相对路径可写
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))

    from owl_admin.app import create_app
    from owl_admin.ext import socketio

    app = create_app()

    host = app.config.get('SERVER_HOST', '127.0.0.1')
    port = int(app.config.get('SERVER_PORT', 9000))
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("  AI 博客系统已启动")
    print(f"  请在浏览器访问: {url}")
    print("  默认账号: admin / admin123")
    print("  按 Ctrl+C 退出")
    print("=" * 60)

    if getattr(sys, 'frozen', False):
        _open_browser(url)

    socketio.run(app,
        load_dotenv=False,
        host=host,
        port=port,
        allow_unsafe_werkzeug=True
    )


if __name__ == "__main__":
    main()
