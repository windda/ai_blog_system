# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from flask import Flask

from owl_system.domain.entity import SysLogininfor, SysOperLog
from owl_system.service.sys_logininfo import SysLogininforService
from owl_system.service.sys_oper_log import SysOperLogService


def record_logininfor(app:Flask,logininfo: SysLogininfor) -> bool:
    """
    记录登录日志

    Args:
        app (Flask): flask应用
        logininfo (SysLogininfor): 登录日志信息

    Returns:
        bool: True/False
    """
    with app.app_context():
        res = SysLogininforService.insert_logininfor(logininfo)
    return res > 0


def record_operlog(app:Flask,sys_oper_log: SysOperLog) -> bool:
    """
    记录操作日志

    Args:
        app (Flask): flask应用
        sys_oper_log (SysOperLog): 操作日志信息

    Returns:
        bool: True/False
    """
    with app.app_context():
        res = SysOperLogService.insert_operlog(sys_oper_log)
    return res > 0
