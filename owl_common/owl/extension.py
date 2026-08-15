# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from .registry import OwlModuleRegistry
from .config import OwlConfigLoader
from .log import OwlLog


'''
    FlaskOwl 是用来模块化基于flask应用的目录结构
'''

class FlaskOwl(object):
    
    def __init__(self,app=None,proot=None):
        if app is not None:
            if proot is None:
                proot = app.root_path
            self.init_app(app,proot)
        
    def init_app(self,app,proot=None):
        """
        初始化插件
        
        Args:
            app: Flask应用实例
            proot: 项目根目录
        """
        if proot is None:
            proot = app.root_path
        self.proot = proot
        app.extensions['flaskowl'] = self
        
        config_loader = OwlConfigLoader(app.root_path)
        config_loader.set_app(app)
        
        module_reg = OwlModuleRegistry(app,proot)
        module_reg.register_modules()
        
        log_handler = OwlLog.generate_handler_from_config(config_loader.cache)
        if log_handler:
            app.logger.addHandler(log_handler)
                

__all__ = ["FlaskOwl"]
