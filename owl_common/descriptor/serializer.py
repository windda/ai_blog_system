# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import functools
from typing import Any, Callable
from flask import Response, make_response
from werkzeug.exceptions import HTTPException, InternalServerError

from owl_common.base.model import BaseEntity,VoSerializerContext
from owl_common.base.signal import log_signal
from owl_common.exception import ServiceException
from owl_common.utils.base import DescriptUtil


class BaseSerializer:
    
    def __call__(self, func) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                res = func(*args, **kwargs)
            except HTTPException as e:
                # self.send_http_exception(func, e)
                raise e
            except Exception as e:
                raise e
            else:
                response = self.serialize(func, res)
                self.send_success(func, res)
            return response
        return wrapper

    def send_http_exception(self, func, e:HTTPException):
        """
        发送http异常的消息
        
        Args:
            func: 被装饰的函数
            e: http异常
        """
        raw_func = DescriptUtil.get_raw(func)
        log_signal.send(raw_func,message=e)
        
    def send_success(self, func, res:Response):
        """
        发送成功响应的消息
        
        Args:
            func: 被装饰的函数
            res: 成功响应
        """
        raw_func = DescriptUtil.get_raw(func)        
        log_signal.send(raw_func,message=res)
    
    def serialize(self, func, res:Any) -> Response:
        """
        序列化对象
        
        Args:
            func: 被装饰的函数
            res: 被序列化的对象
        
        Returns:
            Response: 序列化后的Response对象
        """
        if isinstance(res, Response):
            response = res
        else:
            response = make_response(res, 200)
        return response

    
class JsonSerializer(BaseSerializer):
    
    def __init__(self, 
        exclude_fields: list=[], 
        include_fields: list|None=None, 
        exclude_none: bool=False, 
        exclude_unset: bool=False, 
        exclude_default: bool=False,
        success_code: int=200, 
        mimetype: str='application/json', 
        headers: dict={},
        ):

        self.mimetype = mimetype
        self.headers = headers
        self.success_code = success_code
        self.context = VoSerializerContext(
            by_alias=True,
            exclude_fields=exclude_fields,
            include_fields=include_fields,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            exclude_default=exclude_default
        )

    def serialize(self, func, res:Any) -> Response:
        """
        序列化对象
        
        Args:
            func: 被装饰的函数
            res: 被序列化的对象
        
        Returns:
            Response: 序列化后的Response对象
        """
        if isinstance(res, BaseEntity):
            response = self.handle_entity(func, res)
        elif isinstance(res, list) and len(res) == 2:
            res, code = res
            response = self.serialize(func,res)
            response.status_code = code
        elif isinstance(res, Response):
            response = res
        else:
            response = self.handle_other(func, res)
        return response
    
    def handle_entity(self, func, res:BaseEntity) -> Response:
        """
        处理BaseEntity对象
        
        Args:
            func: 被装饰的函数
            res: 被序列化的对象
        
        Returns:
            Response: 序列化后的Response对象
        """
        try:
            res = res.model_dump_json(
                **self.context.as_kwargs(),
                context=self.context
            )
        except HTTPException as e:
            http_exc = InternalServerError(description="序列化实体对象异常")
            self.send_http_exception(func, http_exc)
            raise http_exc
        except Exception as e:
            raise e
        else:
            response = make_response(res, self.success_code)
            if self.mimetype:
                response.mimetype = self.mimetype
            if self.headers:
                response.headers.update(self.headers)
        return response
    
    def handle_other(self, func, res:Any) -> Response:
        """
        处理其他对象
        
        Args:
            func: 被装饰的函数
            res: 被序列化的对象
        
        Returns:
            Response: 序列化后的Response对象
        """
        try:
            response = make_response(res)
            if self.mimetype:
                response.mimetype = self.mimetype
            if self.headers:
                response.headers.update(self.headers)
        except HTTPException as e:
            http_exc = InternalServerError(description="序列化其他对象异常")
            self.send_http_exception(func, http_exc)
            raise http_exc
        except Exception as e:
            raise e
        return response
