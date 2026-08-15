# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from concurrent.futures import Future
from typing import Callable

from flask import current_app
from owl_framework.config import ThreadPoolConfig


class TaskManager:

    Tasks = []
    
    @classmethod
    def execute(cls, runner:Callable, *args, **kwargs):
        """
        执行任务

        Args:
            runner (Callable): 任务函数
            *args: 任务函数参数
            **kwargs: 任务函数关键字参数
        """
        app = current_app._get_current_object()
        task = ThreadPoolConfig.thread_pool().submit(runner,app, *args, **kwargs)
        task.add_done_callback(cls.on_complete)
        if task and task not in cls.Tasks:
            cls.Tasks.append(task)
    
    @classmethod
    def on_complete(cls, fu:Future):
        """
        任务完成回调
        
        Args:
            fu (Future): 任务Future对象
        """
        if fu.exception():
            raise fu._exception
        