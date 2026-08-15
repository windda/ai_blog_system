#!/usr/bin/env python
# -- coding: utf-8 --
# @Time : 2024/09/18

import os.path
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType
from flask import Blueprint, Flask

from ..base.signal import module_initailize
from .config import CONFIG_CACHE


def path_to_module(file_path:str, root_path:str) -> str:
    """
    文件路径转为模块名称
    
    Args:
        file_path (str): 文件路径
        root_path (str): 根路径
    
    Returns:
        str: 模块名称
    """
    file_path = Path(file_path)
    root_path = Path(root_path).resolve()
    file_relative = file_path.relative_to(root_path)
    module_path = str(file_relative.with_suffix('')).replace(os.sep, '.').replace('\\', '.')
    return module_path


class OwlModuleRegistry(object):
    
    module_prefix = "owl_"
    controller_name = "controller"
    exclude_modules = ["owl_ui"]
    
    def __init__(self, app:Flask=None, proot:str=None):
        self.app = app
        self.proot = proot
        url_prefix = CONFIG_CACHE["owl.api.version"]
        if not url_prefix.startswith("/"):
            raise ValueError("url_prefix must start with /")
        self.api = Blueprint(
            "api", 
            __name__, 
            url_prefix=url_prefix
        )
    
    def register_modules(self):
        '''
        注册所有模块
        '''
        self.import_modules()
        self.register_controllers()
    
    def import_modules(self):
        '''
        导入所有模块
        '''
        for modname in os.listdir(self.proot):
            if not modname.startswith(self.module_prefix):
                continue
            if modname in self.exclude_modules:
                continue
            if not os.path.exists(
                os.path.join(self.proot,modname,"__init__.py")
            ):
                self.app.logger.warning(f"模块路径不存在__init__.py文件: {modname}")
                continue
            self.import_module(modname)
        
    def import_module(self, modname:str):
        '''
        导入模块
        
        Args:
            modname (str): 模块名称
        '''
        modpath = os.path.join(self.proot,modname)
        mod = import_module(path_to_module(modpath,self.proot))
        module_initailize.send(mod,registry=self)
    
    def is_registered_module(self, modname:str) -> bool:
        '''
        检查模块是否已经注册
        
        Args:
            modname (str): 模块名称
        Returns:
            bool: 是否已经注册
        '''
        flag = modname in sys.modules
        return flag
        
    def unregister_module(self, mod:ModuleType):
        '''
        注销模块
        
        Args:
            mod (ModuleType): 模块对象
        '''
        if mod in self.default_modules:
            return
        # todo

    def register_controllers(self):
        '''
        注册所有控制层路由
        '''
        for modname in os.listdir(self.proot):
            
            if not modname.startswith(self.module_prefix):
                continue
            if modname in self.exclude_modules:
                continue
            if not self.is_registered_module(modname):
                continue
            self.register_controller(modname)
        self.app.register_blueprint(self.api)
    
    def register_controller(self, modname:str):
        '''
        注册控制层路由
        
        Args:
            mod (str): 模块名称
        '''
        modpath = os.path.join(self.proot,modname)
        mod_con_path = os.path.join(modpath,self.controller_name)
        if not os.path.exists(mod_con_path):
            return  
        try:
            self._register_rules(mod_con_path)
        except Exception as e:
            raise Exception(
                "在模块中的路由，注册失败: {}，原因: {}".format(modname,str(e))
            )
    
    def unregister_controller(self, modname:str):
        '''
        注销控制层路由
        
        Args:
            modname (str): 模块名称
        '''
        # todo
    
    
    def _register_rules(self,path:str):
        '''
        注册路由规则
        
        Args:
            path (str): 路由路径
        '''
        for rule_name in os.listdir(path):
            con_path = os.path.join(path,rule_name)
            if os.path.isfile(con_path) and rule_name.endswith(".py") \
                and rule_name != "__init__.py":
                rule_path = path_to_module(con_path,self.proot)
                import_module(rule_path)
            elif os.path.isdir(con_path) and \
                os.path.exists(os.path.join(con_path,"__init__.py")):
                for sub_rule_name in os.listdir(con_path):
                    sub_path = os.path.join(con_path,sub_rule_name)
                    if os.path.isfile(sub_path) and sub_rule_name.endswith(".py") \
                        and sub_rule_name != "__init__.py":
                        rule_path = path_to_module(sub_path,self.proot)
                        import_module(path_to_module(sub_path,self.proot))
            else:
                continue
