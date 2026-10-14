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


# PyInstaller 打包（frozen）环境下，os.listdir 无法发现模块目录（模块被编译进 PYZ 压缩包），
# 因此硬编码 owl_* 顶层模块及其 controller 子模块列表，保证路由正常注册。
FROZEN_MODULES = [
    'owl_admin', 'owl_ai', 'owl_apscheduler', 'owl_blog',
    'owl_common', 'owl_framework', 'owl_system',
]

FROZEN_CONTROLLERS = [
    'owl_admin.controller.common.common',
    'owl_admin.controller.index.captcha',
    'owl_admin.controller.index.index',
    'owl_admin.controller.index.login',
    'owl_admin.controller.index.register',
    'owl_admin.controller.monitor.cache',
    'owl_admin.controller.monitor.logininfo',
    'owl_admin.controller.monitor.operlog',
    'owl_admin.controller.monitor.server',
    'owl_admin.controller.monitor.user_online',
    'owl_admin.controller.system.config',
    'owl_admin.controller.system.dept',
    'owl_admin.controller.system.dict_data',
    'owl_admin.controller.system.dict_type',
    'owl_admin.controller.system.menu',
    'owl_admin.controller.system.notice',
    'owl_admin.controller.system.post',
    'owl_admin.controller.system.profile',
    'owl_admin.controller.system.role',
    'owl_admin.controller.system.user',
    'owl_blog.controller.article',
    'owl_blog.controller.category',
    'owl_blog.controller.comment',
    'owl_blog.controller.dashboard',
    'owl_blog.controller.front',
    'owl_blog.controller.tag',
    'owl_ai.controller.ai_chat',
    'owl_apscheduler.controller.job',
    'owl_apscheduler.controller.job_log',
]


def _is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


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
    
    def _discover_modules(self):
        """发现 owl_* 模块名（frozen 环境硬编码，开发环境扫目录）"""
        if _is_frozen():
            return [m for m in FROZEN_MODULES]
        result = []
        for modname in os.listdir(self.proot):
            if not modname.startswith(self.module_prefix):
                continue
            if modname in self.exclude_modules:
                continue
            result.append(modname)
        return result

    def import_modules(self):
        '''
        导入所有模块
        '''
        for modname in self._discover_modules():
            if not _is_frozen():
                if not os.path.exists(
                    os.path.join(self.proot, modname, "__init__.py")
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
        for modname in self._discover_modules():
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
        if _is_frozen():
            # frozen 环境：直接导入该模块硬编码的 controller 子模块
            prefix = modname + '.controller.'
            for c in FROZEN_CONTROLLERS:
                if c.startswith(prefix):
                    import_module(c)
            return
        modpath = os.path.join(self.proot, modname)
        mod_con_path = os.path.join(modpath, self.controller_name)
        if not os.path.exists(mod_con_path):
            return
        try:
            self._register_rules(mod_con_path)
        except Exception as e:
            raise Exception(
                "在模块中的路由，注册失败: {}，原因: {}".format(modname, str(e))
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
