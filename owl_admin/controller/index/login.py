# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.base.model import  AjaxResponse
from owl_common.domain.entity import SysUser
from owl_common.domain.vo import LoginBody
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator
from owl_common.utils import security_util as SecurityUtil
from owl_common.constant import Constants
from owl_system.service import SysMenuService
from owl_framework.service import LoginService,SysPermissionService
from ... import reg


@reg.api.route("/login", methods=["POST"])
@BodyValidator()
@JsonSerializer()
def index_login(dto:LoginBody):
    '''
        登录接口
    '''
    token = LoginService.login(dto)
    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, Constants.TOKEN, token)
    return ajax_response


@reg.api.route("/getInfo", methods=["GET"])
@JsonSerializer()
def index_get_info():
    '''
        获取用户信息接口
    '''
    user:SysUser = SecurityUtil.get_login_user().user
    roles = SysPermissionService.get_role_permission(user)
    perms = SysPermissionService.get_menu_permission(user)
    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, "roles", list(roles))
    setattr(ajax_response, "permissions", list(perms))
    setattr(ajax_response, "user", user.model_dump())
    return ajax_response


@reg.api.route("/getRouters", methods=["GET"])
@JsonSerializer()
def index_get_routers():
    '''
        获取路由信息接口
    '''
    user_id = SecurityUtil.get_user_id()
    menus = SysMenuService.select_menu_tree_by_user_id(user_id)
    ajax_response = AjaxResponse.from_success(
        data=SysMenuService.build_menus(menus)
    )
    return ajax_response


@reg.api.route("/logout", methods=["POST"])
@JsonSerializer()
def index_logout():
    '''
        登出接口
    '''
    flag = LoginService.logout()
    return AjaxResponse.from_success(msg="登出成功") \
        if flag else AjaxResponse.from_error(msg="登出异常")
