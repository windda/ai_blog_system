# -*- coding: utf-8 -*-

from flask import flash

from owl_common.domain.vo import RegisterBody
from owl_common.utils import security_util as SecurityUtil
from owl_common.constant import Constants, UserConstants
from owl_common.exception import CaptchaException, CaptchaExpireException
from owl_common.domain.entity import SysUser
from owl_system.service import SysUserService
from owl_admin.ext import redis_cache

# todo

class RegisterService:

    @classmethod
    def register(cls, body:RegisterBody) -> str:
        """
        注册用户
        
        Args:
            body (RegisterBody): 注册信息
        
        Returns:
            str: 注册结果信息    
        """
        msg = ""
        username = body.username
        password = body.password

        # captcha_on_off = cls.config_service.select_captcha_on_off()
        # Captcha switch
        # if captcha_on_off:
            # cls.validate_captcha(username, body.code, body.uuid)

        if not username:
            msg = "Username cannot be empty"
        elif not password:
            msg = "User password cannot be empty"
        elif len(username) < UserConstants.USERNAME_MIN_LENGTH or len(username) > UserConstants.USERNAME_MAX_LENGTH:
            msg = "Account length must be between 2 and 20 characters"
        elif len(password) < UserConstants.PASSWORD_MIN_LENGTH or len(password) > UserConstants.PASSWORD_MAX_LENGTH:
            msg = "Password length must be between 5 and 20 characters"
        elif UserConstants.NOT_UNIQUE == SysUserService.check_user_name_unique(username):
            msg = f"Failed to save user '{username}', registration account already exists"
        else:
            sys_user = SysUser(
                user_name=username,
                nick_name=username,
                password=SecurityUtil.encrypt_password(body.password.get_secret_value())
            )
            reg_flag = SysUserService.register_user(sys_user)
            if not reg_flag:
                msg = "Registration failed, please contact system administrator"
            else:
                flash("user.register.success")
        return msg
    
    @classmethod
    def validate_captcha(self, username:str, code:str, uuid:str):
        """
        验证码校验
        
        Args:
            username (str): 用户名
            code (str): 验证码
            uuid (str): 验证码唯一标识
        
        Raises:
            CaptchaException: 验证码错误
            CaptchaExpireException: 验证码过期
        """
        verify_key = Constants.CAPTCHA_CODE_KEY + (uuid if uuid is not None else "")
        captcha = redis_cache.get_cache_object(verify_key)
        # redis_cache.delete_object(verify_key)
        if captcha is None:
            raise CaptchaExpireException()
        if code.lower() != captcha.lower():
            raise CaptchaException()