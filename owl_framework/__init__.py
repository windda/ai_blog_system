# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import sys
from types import ModuleType

from owl_common.descriptor.listener import ModuleSignalListener
from owl_common.base.signal import module_initailize
from owl_common.owl.registry import OwlModuleRegistry


@ModuleSignalListener(sys.modules[__name__],module_initailize)
def import_hook(module:ModuleType, registry:OwlModuleRegistry):
    """
    导入模块

    Args:
        module: 模块对象
        module_register: 模块注册器
    """
    pass
