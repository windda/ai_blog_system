# -*- coding: utf-8 -*-
# @Author  : shaw-lee

"""
用户注册控制器。

负责注册请求入参校验、密码加密存储、默认角色分配，
并统一将业务异常抛出，交由全局异常处理器处理。
"""

import os
import re
import traceback

from sqlalchemy.exc import IntegrityError, OperationalError, DBAPIError

from owl_common.base.model import AjaxResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator
from owl_common.domain.vo import RegisterBody
from owl_common.domain.entity import SysUser
from owl_common.utils import security_util as SecurityUtil
from owl_common.constant import Constants, UserConstants
from owl_common.exception import ServiceException, BadRequestException
from owl_system.service import SysConfigService, SysUserService
from owl_admin.ext import redis_cache
from ... import reg


# 用户名格式：允许英文、数字、下划线、中文，2-20字符
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$')
# 密码格式：6-32字符，必须包含字母和数字
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).{6,32}$')


@reg.api.route("/register", methods=["POST"])
@BodyValidator()
@JsonSerializer()
def index_register(dto: RegisterBody):
    """
    用户注册接口

    标准化错误返回：
    - code=500: 服务器内部错误
    - code=400: 参数校验失败
    """
    # ============================================================
    # 1. 检查注册功能开关（环境变量 + 系统配置双重控制）
    # ============================================================
    env_enable = os.getenv("REGISTER_ENABLE", "false").lower() == "true"
    if not env_enable:
        return AjaxResponse.from_error(msg="当前系统暂未开放公网注册")

    try:
        register_enabled = SysConfigService.select_config_by_key("sys.account.registerUser")
    except Exception:
        register_enabled = "true"  # 默认开启注册

    if register_enabled != "true":
        return AjaxResponse.from_error(msg="当前系统没有开启注册功能")

    # ============================================================
    # 2. 后端二次参数校验（防前端绕过）
    # ============================================================
    username = (dto.username or "").strip()
    # SecretStr 类型需要用 get_secret_value() 获取原始密码
    password = dto.password.get_secret_value() if hasattr(dto.password, 'get_secret_value') else (dto.password or "")
    password = password.strip() if password else ""

    if not username:
        return AjaxResponse.from_error(msg="用户名不能为空")
    if not password:
        return AjaxResponse.from_error(msg="密码不能为空")

    # 用户名格式校验
    if not USERNAME_PATTERN.match(username):
        return AjaxResponse.from_error(msg="用户名仅允许英文、数字、下划线、中文，长度2-20位")

    # 纯数字检测
    if username.isdigit():
        return AjaxResponse.from_error(msg="用户名不能为纯数字")

    # 密码格式校验
    if not PASSWORD_PATTERN.match(password):
        return AjaxResponse.from_error(msg="密码必须包含字母和数字，长度6-32位")

    # ============================================================
    # 3. 检查用户名是否已存在
    #    （修复：check_user_name_unique 需要 SysUser 对象，而非字符串）
    # ============================================================
    try:
        # 构造一个临时 SysUser 对象传入，方法内部读取 .user_name 属性
        temp_user = SysUser(user_name=username)
        if UserConstants.NOT_UNIQUE == SysUserService.check_user_name_unique(temp_user):
            return AjaxResponse.from_error(msg=f"用户名「{username}」已被注册")
    except (AttributeError, TypeError, ValueError) as e:
        # 逻辑异常，记录但不阻断流程（后续插入时数据库会拦截）
        traceback.print_exc()
    except Exception as e:
        # 数据库连接等异常，同样不阻断
        traceback.print_exc()

    # ============================================================
    # 3.5 验证码校验
    # ============================================================
    code = (dto.code or "").strip() if dto.code else ""
    uuid_str = (dto.uuid or "").strip() if dto.uuid else ""

    if not code:
        return AjaxResponse.from_error(msg="验证码不能为空")
    if not uuid_str:
        return AjaxResponse.from_error(msg="验证码已过期，请刷新后重试")

    try:
        verify_key = Constants.CAPTCHA_CODE_KEY + uuid_str
        captcha = redis_cache.get(verify_key)
        if captcha is None:
            return AjaxResponse.from_error(msg="验证码已过期，请刷新后重试")
        # 删除验证码，防止重复使用
        redis_cache.delete(verify_key)
        if code.lower() != captcha.lower():
            return AjaxResponse.from_error(msg="验证码错误")
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_error(msg="验证码校验失败，请稍后重试")

    # ============================================================
    # 4. 密码加密
    # ============================================================
    try:
        encrypted_pwd = SecurityUtil.encrypt_password(password)
    except ServiceException as e:
        return AjaxResponse.from_error(msg=str(e.description))
    except Exception:
        traceback.print_exc()
        return AjaxResponse.from_error(msg="密码加密失败，请检查 bcrypt 依赖是否安装（pip install bcrypt==4.2.0）")

    # ============================================================
    # 5. 创建用户并入库
    # ============================================================
    sys_user = SysUser(
        user_name=username,
        nick_name=username,
        password=encrypted_pwd
    )

    try:
        reg_flag = SysUserService.register_user(sys_user)
    except IntegrityError as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if any(kw in error_msg.lower() for kw in ['duplicate', 'unique', 'primary']):
            return AjaxResponse.from_error(msg=f"用户名「{username}」已被注册")
        traceback.print_exc()
        return AjaxResponse.from_error(msg="注册失败：数据写入冲突，请稍后重试")
    except OperationalError as e:
        traceback.print_exc()
        return AjaxResponse.from_error(msg="注册失败：数据库连接异常，请联系管理员")
    except DBAPIError as e:
        traceback.print_exc()
        return AjaxResponse.from_error(msg="注册失败：数据库写入异常，请联系管理员")
    except Exception as e:
        traceback.print_exc()
        return AjaxResponse.from_error(msg=f"注册失败：服务器内部错误，请稍后重试")

    if not reg_flag:
        return AjaxResponse.from_error(msg="注册失败：数据库写入异常，请联系管理员")

    return AjaxResponse.from_success(msg="注册成功")