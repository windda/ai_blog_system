# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from functools import wraps
from typing import Any, List
from blinker import Signal
from flask import Flask


class AppSignalListener(object):
    '''
    Application信号监听器
    
    Depreciated
    '''
        
    def __init__(self, app:Flask, signal:Signal, method:str):
        self._app = app
        self._signal = signal
        self._method = method
        self._signal.connect_via(self._app)(self.receiver)
    
    def __call__(self, clz) -> Any:
        if not hasattr(clz, self._method):
            raise AttributeError("Method {} not found in class {}".format(self._method, clz))
        func = getattr(clz, self._method)
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            with self._app.app_context():
                ret = func(cls, *args, **kwargs)
            return ret
        setattr(clz, self._method, wrapper)


class ModuleSignalListener(object):
    '''
    模块信号监听器
    '''
    
    def __init__(self, module, signal:Signal):
        self._module = module
        self._signal = signal
    
    def __call__(self, func) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        self._signal.connect_via(self._module)(wrapper)
        
        return wrapper
