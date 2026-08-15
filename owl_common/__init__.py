# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import os
import sys
from types import ModuleType
from werkzeug.exceptions import HTTPException

from owl_common.base.serializer import JsonProvider,handle_http_exception
from owl_common.descriptor.listener import ModuleSignalListener
from owl_common.base.signal import module_initailize
from owl_common.owl.registry import OwlModuleRegistry


@ModuleSignalListener(sys.modules[__name__],module_initailize)
def import_hook(module:ModuleType, registry:OwlModuleRegistry):
    """
    导入模块
    初始化app的一些操作：
        1.注册json序列化器
        2.注册错误处理器

    Args:
        module: 模块对象
        module_register: 模块注册器
    """
    os.environ['WERKZEUG_DEBUG_PIN'] = 'off'
        
    registry.app.json_provider_class = JsonProvider
    
    registry.app.register_error_handler(
        HTTPException, handle_http_exception
    )
