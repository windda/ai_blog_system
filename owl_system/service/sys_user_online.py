# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from owl_common.constant import Constants
from owl_common.domain.entity import LoginUser
from owl_system.domain.entity import SysUserOnline
from owl_admin.ext import redis_cache


class SysUserOnlineService:

    @classmethod
    def select_online_by_ipaddr(cls, ipaddr:str, user:LoginUser) \
        -> Optional[SysUserOnline]:
        """
        通过登录地址查询信息
        
        **deprecated**: 该方法已废弃，请使用 cls.select_online_list

        Args:
            ipaddr (str): 登录地址
            user (LoginUser): 用户信息

        Returns:
            SysUserOnline: 登录信息
        """
        if user.ip_addr:
            if ipaddr == user.ip_addr:
                onlineuser:SysUserOnline = SysUserOnline.from_loginuser(user)
                return onlineuser

    
    @classmethod
    def select_online_by_user_name(cls, username:str, user:LoginUser) \
        -> Optional[SysUserOnline]:
        """
        通过登录地址查询信息
        
        **deprecated**: 该方法已废弃，请使用 cls.select_online_list

        Args:
            username (str): 用户名称
            user (LoginUser): 用户信息

        Returns:
            SysUserOnline: 登录信息
        
        """
        if user.user_name:
            if username == user.user_name:
                onlineuser:SysUserOnline = SysUserOnline.from_loginuser(user)
                return onlineuser

    @classmethod
    def select_online_by_info(cls, ipaddr:str, username:str, user:LoginUser) \
        -> Optional[SysUserOnline]:
        """
        通过登录地址查询信息
        
        **deprecated**: 该方法已废弃，请使用 cls.select_online_list

        Args:
            ipaddr (str): 登录地址
            username (str): 用户名称
            user (LoginUser): 用户信息

        Returns:
            SysUserOnline: 登录信息
        """
        if user.ip_addr and user.user_name:
            if ipaddr == user.ip_addr and username == user.user_name:
                onlineuser:SysUserOnline = SysUserOnline.from_loginuser(user)
                return onlineuser
    
    @classmethod
    def select_online_list(cls, query:SysUserOnline) -> List[SysUserOnline]:
        """
        通过请求参数查询信息
        
        Args:
            query (SysUserOnline): 查询参数

        Returns:
            List[SysUserOnline]: 登录信息列表
        """
        keys:list[bytes] = redis_cache.keys(Constants.LOGIN_TOKEN_KEY + "*");
        online_users = []
        for key in keys:
            key_decoded = key.decode("utf-8")
            user_json = redis_cache.get(key_decoded)
            loginuser = LoginUser.model_validate_json(user_json)
            onlineuser:SysUserOnline = SysUserOnline.from_loginuser(loginuser)
            if query.ip_addr and query.user_name:
                if onlineuser.ip_addr == query.ip_addr and onlineuser.user_name == query.user_name:
                    online_users.append(onlineuser)
            elif query.ip_addr:
                if onlineuser.ip_addr == query.ip_addr:
                    online_users.append(onlineuser)
            elif query.user_name:
                if onlineuser.user_name == query.user_name:
                    online_users.append(onlineuser)
            else:
                online_users.append(onlineuser)
        if online_users:
            online_users.reverse()
        return online_users

    @classmethod
    def login_user_to_user_online(cls, user:LoginUser)-> SysUserOnline:
        """
        设置在线用户信息
        
        **deprecated**: 该方法已废弃，请使用 SysUserOnline.from_loginuser

        Args:
            user (LoginUser): 用户信息

        Returns:
            SysUserOnline: 登录信息
        """
        return SysUserOnline(
            token_id=user.token.hex,
            user_name=user.user_name,
            dept_name=user.dept_name,
            ip_addr=user.ip_addr,
            login_location=user.login_location,
            browser=user.browser,
            os=user.os,
            login_time=user.login_time,
        )
    
    @classmethod
    def force_logout(cls, token_id:str)-> bool:
        """
        强制退出登录
        
        Args:
            token_id (str): 用户token

        Returns:
            bool: 是否成功
        """
        redis_cache.delete(Constants.LOGIN_TOKEN_KEY + token_id)
        return True