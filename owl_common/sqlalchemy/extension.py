# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from flask import Flask
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy

from .listener import init_listener


class SQLAlchemy(_SQLAlchemy):
    
    def init_app(self, app: Flask) -> None:
        """
        初始化SQLAlchemy实例，并注册事件监听器

        Args:
            app (Flask): flask应用实例
        """
        super().init_app(app)
        for engine in self._app_engines[app].values():
            init_listener(engine)
        return self

