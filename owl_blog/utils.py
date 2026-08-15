# -*- coding: utf-8 -*-
"""
博客模块公共工具类。

抽取各控制器重复的公共方法（当前用户获取、管理员判断等），
并统一抛出 ServiceException 子类，由全局异常处理器处理。
"""

from flask_login import current_user as flask_user

from owl_common.exception import UnauthorizedException
from owl_common.utils import security_util as SecurityUtil


def get_current_user():
    """
    获取当前登录用户

    Returns:
        LoginUser: 登录用户对象

    Raises:
        UnauthorizedException: 未登录或登录已过期
    """
    try:
        if not flask_user.is_authenticated:
            raise UnauthorizedException('未登录或登录已过期')
        login_user = SecurityUtil.get_login_user()
        if login_user is None:
            raise UnauthorizedException('未登录或登录已过期')
        if getattr(login_user, 'user_id', None) is None:
            raise UnauthorizedException('未登录或登录已过期')
        return login_user
    except UnauthorizedException:
        raise
    except Exception:
        raise UnauthorizedException('未登录或登录已过期')


def is_admin(user) -> bool:
    """
    判断用户是否为管理员

    Args:
        user: 登录用户对象

    Returns:
        bool: True=管理员, False=普通用户
    """
    if user is None:
        return False
    try:
        # 方式1：user_id == 1
        user_id = getattr(user, 'user_id', None)
        if user_id is not None and user_id == 1:
            return True
        # 方式2：角色key包含admin
        roles = getattr(user, 'roles', None)
        if roles:
            for r in roles:
                if getattr(r, 'role_key', None) == 'admin':
                    return True
        # 方式3：直接有role_key属性
        if getattr(user, 'role_key', None) == 'admin':
            return True
        return False
    except Exception:
        return user is not None and getattr(user, 'user_id', None) == 1


def safe_int(val, default=None):
    """安全转int"""
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def sanitize_html(text: str) -> str:
    """
    XSS 过滤：bleach 白名单 HTML 净化。

    后端必须过滤，不能只依赖前端；白名单模式比正则黑名单更安全。

    白名单策略：
    - 允许的标签：p, br, strong, em, a, code, pre, ul, ol, li, h2, h3 等
    - 允许的属性：a 标签的 href/title/rel
    - 禁止 javascript: 伪协议
    - 不在白名单的标签被剥离，但保留内部文本内容

    Args:
        text: 原始文本

    Returns:
        str: 净化后文本
    """
    import bleach
    if not text:
        return text

    ALLOWED_TAGS = [
        'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'em', 'i',
        'li', 'ol', 'p', 'pre', 'strong', 'ul', 'h2', 'h3', 'span'
    ]
    ALLOWED_ATTRS = {
        'a': ['href', 'title', 'rel'],
    }

    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,  # 剥除非白名单标签，但保留内部文本
        protocols=['http', 'https', 'mailto']  # 禁止 javascript: 伪协议
    )


def sanitize_xss(text: str) -> str:
    """
    [DEPRECATED] 旧版正则黑名单 XSS 过滤，请使用 sanitize_html()

    保留此函数以兼容旧代码引用
    """
    return sanitize_html(text)
