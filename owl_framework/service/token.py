# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional
from flask import Request, request

from owl_common.exception import ServiceException
from owl_common.utils import AddressUtil, IpUtil, TokenUtil
from owl_common.constant import Constants
from owl_common.domain.entity import LoginUser
from owl_framework.config import TokenConfig
from owl_admin.ext import redis_cache


class TokenService:
    
    @classmethod
    def create_token(cls, user:LoginUser) -> str:
        """
        创建token
        
        Args:
            user(LoginUser): 登录用户
        
        Returns:
            str: token
        """
        cls.set_useragent(user)
        cls.refresh_token(user)
        claims = {
            Constants.LOGIN_USER_KEY: user.token.hex
        }
        return cls.create_token_by_claims(claims)
    
    @classmethod
    def create_token_by_claims(cls, claims:dict) -> str: 
        """
        根据claims创建token

        Args:
            claims (dict): token的参数claims

        Returns:
            str: token
        """
        token = TokenUtil.encode(claims,TokenConfig.secret)
        return token
    
    @classmethod
    def verify_token(cls,user:LoginUser):
        '''
        验证token有效期
        
        Args:
            user(LoginUser): 登录用户
        '''
        expire_time = user.expire_time
        current_time = datetime.now()
        if (expire_time - current_time).min < 20:
            cls.refresh_token(user)
        
    @classmethod
    def refresh_token(cls, user:LoginUser):
        '''
        刷新token
        
        Args:
            user(LoginUser): 登录用户
        '''
        user.login_time = datetime.now()
        user.expire_time = user.login_time + TokenConfig.expire_time()
        usertoken_key = cls.get_token_key(user.token.hex)
        user_json = user.model_dump_json()
        redis_cache.set(usertoken_key, user_json, TokenConfig.expire_time() * 60)
        
    @classmethod
    def set_useragent(cls, user:LoginUser):
        '''
        设置浏览器信息
        
        Args:
            user(LoginUser): 登录用户
        '''
        user.ip_addr = IpUtil.get_ip()
        user.login_location = AddressUtil.get_address(user.ip_addr)
        user.browser = request.user_agent.browser
        user.os = request.user_agent.platform
    
    @classmethod
    def parse_token(cls, token:str) -> dict:
        '''
        解析token
        
        Args:
            token(str): token
        
        Returns:
            dict: token参数claims
        '''
        payload = TokenUtil.decode(token, TokenConfig.secret)
        return payload
        
    @classmethod
    def get_login_user(cls, request:Request) -> Optional[LoginUser]:
        '''
        获取登录用户信息
        
        Args:
            request(Request): 请求对象
        
        Returns:
            LoginUser: 登录用户信息
        '''
        token = cls.get_token(request)
        if token:
            claims = cls.parse_token(token)
            token_uuid = claims.get(Constants.LOGIN_USER_KEY)
            usertoken_key = cls.get_token_key(token_uuid)
            jsoned_user = redis_cache.get(usertoken_key)
            if not jsoned_user:
                return None
            login_user = LoginUser.model_validate_json(jsoned_user)
            if login_user:
                return login_user
            else:
                raise ServiceException("Token信息不存在")
            
    @classmethod
    def get_token(cls,request:Request) -> str:
        '''
        获取token
        
        Args:
            request(Request): 请求对象
        
        Returns:
            str: token
        '''
        token = request.headers.get(Constants.TOKEN_HEADER)
        if token and token.startswith(Constants.TOKEN_PREFIX):
            token = token[len(Constants.TOKEN_PREFIX):]
            token = token.strip()
        return token
                       
    @classmethod
    def get_token_key(cls, uuid:str) -> str:
        '''
        获取token缓存key
        
        Args:
            uuid(str): token的uuid
        
        Returns:    
            str: token缓存key
        '''
        return Constants.LOGIN_TOKEN_KEY + uuid
    
    @classmethod
    def set_login_user(cls, user:LoginUser):
        '''
        设置登录用户信息
        
        Args:
            user(LoginUser): 登录用户信息
        '''
        if user and user.token:
            cls.refresh_token(user)
    
    @classmethod
    def del_login_user(cls, token:str):
        '''
        删除登录用户信息
        
        Args:
            token(str): token
        '''
        if token:
            user_key:str = cls.get_token_key(token)
            redis_cache.delete(user_key)
