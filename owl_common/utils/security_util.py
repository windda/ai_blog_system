# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import bcrypt
from flask import abort
from flask_login import current_user
from owl_common.constant import HttpStatus
from owl_common.exception import ServiceException
from owl_common.domain.entity import LoginUser
from owl_common.utils.base import UtilException


def get_user_id() -> int:
    """
    获取当前登录用户的ID

    Raises:
        UtilException: 获取用户ID异常

    Returns:
        int: 当前登录用户的ID 
    """
    try:
        return get_login_user().user_id
    except Exception:
        raise UtilException("获取用户ID异常", HttpStatus.UNAUTHORIZED)

def get_dept_id() -> int:
    """
    获取当前登录用户的部门ID

    Raises:
        UtilException: 获取部门ID异常

    Returns:
        int: 当前登录用户的部门ID 
    """
    try:
        return get_login_user().dept_id
    except Exception:
        raise UtilException("获取部门ID异常", HttpStatus.UNAUTHORIZED)

def get_username() -> str:
    """
    获取当前登录用户的账户

    Raises:
        UtilException: 获取用户账户异常

    Returns:
        str: 当前登录用户的账户 
    """
    try:
        return get_login_user().user_name
    except Exception as e:
        raise UtilException("获取用户账户异常", HttpStatus.UNAUTHORIZED)

def get_login_user() -> LoginUser:
    """
    获取当前登录用户的信息

    Raises:
        UtilException: 获取用户信息异常

    Returns:
        LoginUser: 当前登录用户的信息 
    """
    try:
        if not current_user.is_authenticated:
            abort(401)
        return current_user
    except Exception:
        raise UtilException("获取用户信息异常", HttpStatus.UNAUTHORIZED)

def encrypt_password(password:str) -> str:
    """
    加密密码

    Args:
        password (str): 原始密码

    Returns:
        str: 加密后的密码
    """
    if not password:
        raise ServiceException("密码不能为空")
    salt = bcrypt.gensalt(rounds=10)
    bcrypt_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return bcrypt_password.decode('utf-8')

def matches_password(raw_password:str, encoded_password:str) -> bool:
    """
    验证密码是否匹配

    Args:
        raw_password (str): 原始密码
        encoded_password (str): 加密后的密码

    Returns:
        bool: 密码是否匹配
    """
    if not raw_password or not encoded_password:
        return False
    try:
        return bcrypt.checkpw(raw_password.encode('utf-8'), encoded_password.encode('utf-8'))
    except ValueError:
        return False

def is_admin(user_id) -> bool:
    """
    判断用户是否为管理员

    Args:
        user_id (int): 用户ID

    Returns:
        bool: 用户是否为管理员
    """
    return user_id is not None and user_id == 1

def login_user_is_admin() -> bool:
    """
    判断当前登录用户是否为管理员

    Returns:
        bool: 当前登录用户是否为管理员
    """
    return is_admin(get_user_id())
