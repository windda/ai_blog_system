# -*- coding: utf-8 -*-
# @Author  : shaw-lee

"""
全局异常体系。

所有自定义异常继承自 ServiceException，统一通过全局 errorhandler 捕获，
返回统一的 JSON 格式；分为业务异常、参数校验异常、权限异常、系统异常。
"""

from werkzeug.exceptions import HTTPException


class ServiceException(HTTPException):
    """
    业务异常基类
    所有业务异常继承此类，全局 errorhandler 统一捕获
    """
    code = 500
    description = '服务器内部错误'
    
    def __init__(self, msg: str = None, code: int = None):
        if msg:
            self.description = msg
        if code:
            self.code = code
        super().__init__(self.description)


class BadRequestException(ServiceException):
    """参数校验失败 400"""
    code = 400
    description = '请求参数错误'


class UnauthorizedException(ServiceException):
    """未登录或Token过期 401"""
    code = 401
    description = '未登录或登录已过期'


class ForbiddenException(ServiceException):
    """无权限访问 403"""
    code = 403
    description = '无访问权限'


class NotFoundException(ServiceException):
    """资源不存在 404"""
    code = 404
    description = '请求的资源不存在'


class CaptchaException(ServiceException):
    """验证码错误"""
    code = 500
    description = '验证码错误'


class CaptchaExpireException(ServiceException):
    """验证码过期"""
    code = 500
    description = '验证码已过期'


class FileUploadException(ServiceException):
    """文件上传异常"""
    code = 500
    description = '文件上传失败'