# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from datetime import datetime
from functools import wraps
from typing import Any, Callable
from werkzeug.exceptions import HTTPException
from flask import Response, request
from pydantic import BaseModel

from owl_common.domain.entity import LoginUser
from owl_common.domain.enum import BusinessStatus, BusinessType,OperatorType
from owl_common.utils import IpUtil
from owl_common.utils import security_util as SecurityUtil
from owl_common.base.signal import log_signal
from owl_common.utils.base import DescriptUtil
from owl_framework.asyncsched.manager import TaskManager
from owl_framework.asyncsched.task import record_operlog
from owl_system.domain.entity import SysOperLog


class Log:
    
    def __init__(self, 
        title:str, 
        business_type:BusinessType=BusinessType.OTHER,
        operator_type:BusinessType=OperatorType.MANAGE, 
        is_save_request_data:bool=True, 
        is_save_response_data:bool=True
    ):
        self.title = title
        self.business_type = business_type
        self.operator_type = operator_type
        self.is_save_request_data = is_save_request_data
        self.is_save_response_data = is_save_response_data

        self._oper_log = SysOperLog()
        self._oper_log.title = self.title
        self._oper_log.business_type = self.business_type.value
        self._oper_log.operator_type = self.operator_type.value
        
    def __call__(self, func) -> Callable:
        
        raw_func = DescriptUtil.get_raw(func)        
        log_signal.connect_via(sender=raw_func)(self.on_event)
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            
            rv = func(*args, **kwargs)
            return rv
                
        return wrapper
    
    def on_event(self, sender, **kwargs):
        '''
        监听信号
        
        Args:
            sender: 信号发送者
            **kwargs: 信号消息
        '''
        message = kwargs.get('message')
        self.handle_request(sender)
        self.handle_login_user()
        if isinstance(message, HTTPException):
            self.handle_exception(message)
        else:
            self.handle_response(message)
        TaskManager.execute(record_operlog,self._oper_log)
    
    def handle_exception(self, e:Exception):
        '''
        处理异常
        
        Args:
            e(Exception): 异常
        '''
        self._oper_log.status = BusinessStatus.FAIL.value
        self._oper_log.error_msg = str(e)[:2000]
    
    def handle_login_user(self):
        '''
        处理登录用户
        
        Args:
            login_user(LoginUser): 登录用户
        '''
        self._oper_log.status = BusinessStatus.SUCCESS.value
        login_user:LoginUser = SecurityUtil.get_login_user()
        if login_user:
            self._oper_log.oper_name = login_user.user_name
        
    def handle_request(self, func):
        '''
        处理请求参数
        
        Args:
            func: 被装饰的函数
        '''
        if self.is_save_request_data:
            json_param = request.get_data(as_text=True)
            self._oper_log.oper_ip = IpUtil.get_ip()
            self._oper_log.oper_param = json_param[:2000] if json_param else ""
            self._oper_log.request_method = request.method
            self._oper_log.oper_url = request.path
            self._oper_log.method = "{}.{}".format(func.__module__, func.__name__)
            self._oper_log.oper_time = datetime.now()
                        
    def handle_response(self, response:Response|BaseModel):
        '''
        处理响应参数
        
        Args:
            response(Response|BaseModel): 响应参数
        '''
        if self.is_save_response_data:
            if isinstance(response, BaseModel):
                self._oper_log.json_result = response.model_dump_json(exclude_none=True)[:2000]
            elif isinstance(response, Response):
                print("handle_response response: {}".format(response))
                json_result = response.get_data(as_text=False)
                if json_result:
                    self._oper_log.json_result = json_result[:2000]
                    
