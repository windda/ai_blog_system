# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import Annotated
from flask_login import login_required
from pydantic import Field, SecretStr
from flask import request

from owl_common.config import OWLConfig
from owl_common.constant import UserConstants
from owl_common.base.model import AjaxResponse, MultiFile
from owl_common.domain.entity import LoginUser, SysUser
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, FileValidator
from owl_common.utils.base import FileUploadUtil
from owl_common.utils import security_util as SecurityUtil
from owl_system.service import SysUserService
from owl_framework.service.token import TokenService
from owl_framework.descriptor.log import Log
from ... import reg


@reg.api.route("/system/user/profile", methods=["GET"])
@login_required
@JsonSerializer()
def system_user_profile():
    '''
        获取个人信息
    '''
    login_user: LoginUser = SecurityUtil.get_login_user()
    user: SysUser = login_user.user
    if not user:
        return AjaxResponse.from_error(msg="用户信息丢失")

    from owl_system.service import SysRoleService, SysPostService
    # 角色组（逗号分隔的角色名）
    roles = SysRoleService.select_roles_by_user_id(user.user_id)
    role_group = ','.join([
        r.role_name for r in roles
        if getattr(r, 'flag', False) and getattr(r, 'role_name', '')
    ])
    # 岗位组（逗号分隔的岗位名）
    post_group = ''
    post_ids = SysPostService.select_post_list_by_user_id(user.user_id)
    if post_ids:
        post_names = []
        for pid in post_ids:
            p = SysPostService.select_post_by_id(pid)
            if p and getattr(p, 'post_name', ''):
                post_names.append(p.post_name)
        post_group = ','.join(post_names)

    ajax_response = AjaxResponse.from_success(data=user)
    setattr(ajax_response, "roleGroup", role_group)
    setattr(ajax_response, "postGroup", post_group)
    return ajax_response


@reg.api.route("/system/user/profile", methods=["PUT"])
@BodyValidator()
@login_required
@Log(title = "个人信息", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_user_profile_update(dto:SysUser):
    '''
        修改个人信息
    '''
    login_user: LoginUser = SecurityUtil.get_login_user()
    user: SysUser = login_user.user
    dto.user_name = user.user_name
    if dto.phonenumber and UserConstants.NOT_UNIQUE == \
        SysUserService.check_phone_unique(dto):
        return AjaxResponse.from_error(msg=f"修改用户'{user.user_name}'失败，手机号码已存在")
    if dto.email and UserConstants.NOT_UNIQUE == SysUserService.check_email_unique(dto):
        return AjaxResponse.from_error(msg=f"修改用户'{user.user_name}'失败，邮箱账号已存在")
    dto.user_id = user.user_id
    dto.password = None
    if SysUserService.update_user_profile(dto):
        user.nick_name = dto.nick_name
        user.email = dto.email
        user.phonenumber = dto.phonenumber
        user.sex = dto.sex
        TokenService.set_login_user(login_user)
        return AjaxResponse.from_success()
    else:
        return AjaxResponse.from_error(msg="修改个人信息异常，请联系管理员")


@reg.api.route("/system/user/profile/updatePwd", methods=["PUT"])
@BodyValidator()
@login_required
@Log(title = "个人信息", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_user_profile_update_pwd(
    old_password:Annotated[SecretStr, Field(..., example='admin')],
    new_password:Annotated[SecretStr, Field(..., example='admin123')]
):
    '''
        修改密码
    '''
    login_user: LoginUser = SecurityUtil.get_login_user()
    if not SecurityUtil.matches_password(
        old_password.get_secret_value(), login_user.user.password
    ):
        return AjaxResponse.from_error(msg="修改密码失败，旧密码错误")
    if SecurityUtil.matches_password(
        new_password.get_secret_value(), login_user.user.password
    ):
        return AjaxResponse.from_error(msg="修改密码失败，新密码不能与旧密码相同")
    if SysUserService.reset_user_pwd(
        login_user.user.user_name, 
        SecurityUtil.encrypt_password(new_password.get_secret_value())
        ):
        login_user.user.password = SecurityUtil.encrypt_password(
            new_password.get_secret_value()
        )
        TokenService.set_login_user(login_user)
        return AjaxResponse.from_success()
    else:
        return AjaxResponse.from_error(msg="修改密码异常，请联系管理员")


@reg.api.route("/system/user/profile/avatar", methods=["POST"])
@login_required
@Log(title = "用户头像", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_user_profile_avatar():
    '''
        头像上传
    '''
    import os
    from werkzeug.utils import secure_filename

    if 'avatarfile' not in request.files:
        return AjaxResponse.from_error(msg="没有上传文件")

    file = request.files['avatarfile']
    if file.filename == '':
        return AjaxResponse.from_error(msg="没有选择文件")
    if file:
        login_user: LoginUser = SecurityUtil.get_login_user()
        import time
        upload_dir = os.path.join(OWLConfig.profile, 'avatar')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        timestamp = str(int(time.time() * 1000))
        safe_name = secure_filename(file.filename)
        if '.' not in safe_name:
            safe_name += '.png'
        new_filename = f"{timestamp}_{safe_name}"
        file.save(os.path.join(upload_dir, new_filename))
        avatar_path = f"/uploads/avatar/{new_filename}"
        num = SysUserService.update_user_avatar(
            login_user.user_name, 
            avatar_path
            )
        if num > 0:
            ajax_response = AjaxResponse.from_success()
            setattr(ajax_response, "imgUrl", avatar_path)
            login_user.user.avatar = avatar_path
            TokenService.set_login_user(login_user)
            return ajax_response
        else:
            return AjaxResponse.from_error(msg="上传头像失败，请联系管理员")
    else:
        return AjaxResponse.from_error(msg="上传头像异常，请联系管理员")


