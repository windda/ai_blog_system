# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from pydantic import BeforeValidator, Field
from typing_extensions import Annotated
from werkzeug.datastructures import ImmutableMultiDict, FileStorage
from flask_login import login_required

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.constant import UserConstants
from owl_common.utils import security_util as SecurityUtil
from owl_common.utils.base import ExcelUtil
from owl_common.domain.entity import SysUser, SysRole
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.descriptor.validator import FileDownloadValidator, \
    FileUploadValidator, QueryValidator, BodyValidator, PathValidator
from owl_system.domain.entity import SysPost
from owl_system.service.sys_post import SysPostService
from owl_system.service.sys_role import SysRoleService
from owl_system.mapper.sys_user_role import SysUserRoleMapper
from owl_system.mapper.sys_user_post import SysUserPostMapper
from owl_system.mapper import SysUserMapper
from owl_system.service import SysUserService
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_framework.descriptor.log import Log
from ... import reg


@reg.api.route("/system/user/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("system:user:list"))
@JsonSerializer()
def system_user_list(dto:SysUser):
    '''
        获取用户列表
    '''
    rows = SysUserService.select_user_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/user/", methods=["GET"])
@reg.api.route("/system/user/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:user:query"))
@JsonSerializer()
def system_get_user(id:Optional[int]=None):
    '''
        获取用户详情
    '''
    SysUserService.check_user_data_scope(id)
    ajax_response = AjaxResponse.from_success()
    roles:List[SysRole] = SysRoleService.select_role_all()
    posts:List[SysPost] = SysPostService.select_post_all()
    if not SecurityUtil.is_admin(id):
        roles = [role for role in roles if not role.is_admin()]
    setattr(ajax_response,"roles",roles)
    setattr(ajax_response,"posts",posts)
    if id:
        user = SysUserService.select_user_by_id(id)
        setattr(ajax_response,"data",user)
        post_ids = SysUserPostMapper.select_post_ids_by_user_id(id)
        setattr(ajax_response,"postIds",post_ids)
        role_ids = SysUserRoleMapper.select_role_ids_by_user_id(id)
        setattr(ajax_response,"roleIds",role_ids)
    return ajax_response


@reg.api.route("/system/user", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:user:add"))
@Log(title="用户管理",business_type=BusinessType.INSERT)
@JsonSerializer()
def system_create_user(dto:SysUser):
    '''
        新增用户
    '''
    if SysUserService.check_user_name_unique(dto) \
        == UserConstants.NOT_UNIQUE:
        return AjaxResponse.from_error(
            f"新增用户'{dto.user_name}'失败，登录账号已存在"
        )
    elif dto.phonenumber \
        and SysUserService.check_phone_unique(dto) \
        == UserConstants.NOT_UNIQUE:
        return AjaxResponse.from_error(
            f"新增用户'{dto.phonenumber}'失败，手机号码已存在"
        )
    elif dto.email \
        and SysUserService.check_email_unique(dto) \
        == UserConstants.NOT_UNIQUE:
        return AjaxResponse.from_error(
            f"新增用户'{dto.email}'失败，邮箱已存在"
        )
    # 修复：新增用户时对密码进行加密
    dto.password = SecurityUtil.encrypt_password(dto.password)
    dto.create_by_user(SecurityUtil.get_username())
    flag = SysUserService.insert_user(dto)
    ajax_response = AjaxResponse.from_success() if flag else AjaxResponse.from_error()
    return ajax_response


@reg.api.route("/system/user", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:user:edit"))
@Log(title="用户管理",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_update_user(dto:SysUser):
    '''
        修改用户
    '''
    SysUserService.check_user_allowed(dto)
    SysUserService.check_user_data_scope(dto.user_id)
    if dto.phonenumber \
        and SysUserService.check_phone_unique(dto) \
        == UserConstants.NOT_UNIQUE:
        return AjaxResponse.from_error(
            f"修改用户'{dto.phonenumber}'失败，手机号码已存在"
        )
    elif dto.email \
        and SysUserService.check_email_unique(dto) \
        == UserConstants.NOT_UNIQUE:
        return AjaxResponse.from_error(
            f"修改用户'{dto.email}'失败，邮箱已存在"
        )
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysUserService.update_user(dto)
    ajax_response = AjaxResponse.from_success() if flag else AjaxResponse.from_error()
    return ajax_response


@reg.api.route("/system/user/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:user:remove"))
@Log(title="用户管理",business_type=BusinessType.DELETE)
@JsonSerializer()
def system_delete_users(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除用户
    '''
    if SecurityUtil.get_user_id() in ids:
        return AjaxResponse.from_error("当前用户不能删除")
    flag = SysUserService.delete_users_by_ids(ids)
    ajax_response = AjaxResponse.from_success() if flag > 0 else AjaxResponse.from_error()
    return ajax_response


@reg.api.route("/system/user/export", methods=["POST"])
@FileDownloadValidator()
@PreAuthorize(HasPerm("system:user:export"))
@Log(title="用户管理",business_type=BusinessType.EXPORT)
@BaseSerializer()
def system_user_export(dto:SysUser):
    '''
        导出用户数据
    '''
    rows = SysUserService.select_user_list(dto)
    excel_util = ExcelUtil(SysUser)
    return excel_util.export_response(rows, "用户数据")


@reg.api.route("/system/user/importData", methods=["POST"])
@FileUploadValidator()
@PreAuthorize(HasPerm("system:user:import"))
@Log(title="用户管理",business_type=BusinessType.IMPORT)
@JsonSerializer()
def system_user_importdata(
    file:List[FileStorage],
    update_support: Annotated[bool,BeforeValidator(lambda x:x!="0")]
):
    '''
        导入用户模板
    '''
    file = file[0]
    excel_util = ExcelUtil(SysUser)
    datas = excel_util.import_file(file,sheetname="用户数据")
    msg = SysUserService.import_user(datas,update_support)
    return AjaxResponse.from_success(msg=msg)


@reg.api.route("/system/user/importTemplate", methods=["POST"])
@login_required
@BaseSerializer()
def system_user_importtemplate():
    '''
        导出模板
    '''
    excel_util = ExcelUtil(SysUser)
    return excel_util.import_template_response(sheetname="用户数据")
    
    
@reg.api.route("/system/user/resetPwd", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:user:resetPwd"))
@Log(title="用户管理",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_update_user_resetpwd(dto:SysUser):
    '''
        重置密码
    '''
    SysUserService.check_user_allowed(dto)
    SysUserService.check_user_data_scope(dto.user_id)
    dto.password = SecurityUtil.encrypt_password(dto.password)
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysUserService.reset_pwd(dto)
    ajax_response = AjaxResponse.from_success() if flag else AjaxResponse.from_error()
    return ajax_response


@reg.api.route("/system/user/changeStatus", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:user:edit"))
@Log(title="用户管理",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_update_user_changestatus(dto:SysUser):
    '''
        修改用户状态
    '''
    SysUserService.check_user_allowed(dto)
    SysUserService.check_user_data_scope(dto.user_id)
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysUserService.update_user_status(dto)
    ajax_response = AjaxResponse.from_success() if flag else AjaxResponse.from_error()
    return ajax_response
    
    
@reg.api.route("/system/user/authRole/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:user:query"))
@JsonSerializer()
def system_get_user_authrole(id:int):
    '''
        获取用户授权角色
    '''
    sysuser:SysUser = SysUserMapper.select_user_detail_by_id(id)
    roles:List[SysRole] = SysRoleService.select_role_list_by_user_id(id)
    if not sysuser.is_admin():
        roles = [role for role in roles if not role.is_admin()]
    ajax_response = AjaxResponse.from_success() if sysuser else AjaxResponse.from_error()
    setattr(ajax_response,"user",sysuser)
    setattr(ajax_response,"roles",roles)
    return ajax_response
    
    
@reg.api.route("/system/user/authRole", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:user:edit"))
@Log(title="用户管理",business_type=BusinessType.GRANT)
@JsonSerializer()
def system_update_user_authrole(
    user_id:Annotated[int,Field(gt=0)],
    role_ids:Annotated[List[int],Field(default_factory=List)]
):
    '''
        授权用户角色
    '''
    SysUserService.check_user_data_scope(user_id)
    SysUserService.update_user_roles(user_id,role_ids)
    return AjaxResponse.from_success()
