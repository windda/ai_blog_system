# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.constant import UserConstants
from owl_common.base.model import AjaxResponse
from owl_common.domain.entity import SysMenu
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator,PathValidator
from owl_common.utils import security_util as SecurityUtil
from owl_system.service.sys_menu import SysMenuService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/menu/list", methods=["GET"])
@QueryValidator()
@PreAuthorize(HasPerm("system:menu:list"))
@JsonSerializer()
def system_menu_list(dto:SysMenu):
    '''
        获取菜单列表
    '''
    rows = SysMenuService.select_menu_list(dto,SecurityUtil.get_user_id())
    ajax_response = AjaxResponse.from_success(data=rows)
    return ajax_response


@reg.api.route("/system/menu/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:menu:query"))
@JsonSerializer()
def system_menu(id:int):
    '''
        获取菜单详情
    '''
    menu = SysMenuService.select_menu_by_id(id)
    ajax_response = AjaxResponse.from_success(data=menu)
    return ajax_response


@reg.api.route("/system/menu/treeselect", methods=["GET"])
@QueryValidator()
@JsonSerializer()
def system_menu_treeselect(dto:SysMenu):
    '''
        获取菜单下拉树
    '''
    rows = SysMenuService.select_menu_list(dto,SecurityUtil.get_user_id())
    ajax_response = AjaxResponse.from_success(
        data=SysMenuService.build_menu_tree_select(rows)
    )
    return ajax_response


@reg.api.route("/system/menu/roleMenuTreeselect/<int:id>", methods=["GET"])
@PathValidator()
@JsonSerializer()
def system_menu_roletreeselect(id:int):
    '''
        获取角色的菜单下拉树
    '''
    rows = SysMenuService.select_menu_list_by_user_id(
        SecurityUtil.get_user_id()
    )
    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, "checked_keys", 
        SysMenuService.select_menu_list_by_role_id(id)
    )
    setattr(ajax_response, "menus", 
        SysMenuService.build_menu_tree_select(rows)
    )
    return ajax_response


@reg.api.route("/system/menu", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:menu:add"))
@Log(title="菜单管理",business_type=BusinessType.INSERT)
@JsonSerializer()
def system_menu_create(dto:SysMenu):
    '''
        新增菜单
    '''
    if UserConstants.NOT_UNIQUE == SysMenuService.check_menu_name_unique(dto):
        return AjaxResponse.from_error("菜单名称已存在")
    elif UserConstants.YES_FRAME == dto.is_frame and not dto.path:
        return AjaxResponse.from_error(
            "新增菜单'{}'失败，地址必须以http(s)://开头".format(dto.menu_name)
        )
    dto.create_by_user(SecurityUtil.get_username())
    SysMenuService.insert_menu(dto)
    ajax_response = AjaxResponse.from_success()
    return ajax_response


@reg.api.route("/system/menu", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:menu:edit"))
@Log(title="菜单管理",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_menu_update(dto:SysMenu):
    '''
        修改菜单
    '''
    if UserConstants.UNIQUE != SysMenuService.check_menu_name_unique(dto):
        return AjaxResponse.from_error("菜单名称已存在")
    elif dto.parent_id == dto.menu_id:
        return AjaxResponse.from_error("上级菜单不能是自己")
    elif UserConstants.YES_FRAME == dto.is_frame and not dto.path:
        return AjaxResponse.from_error(
            "新增菜单'{}'失败，地址必须以http(s)://开头".format(dto.menu_name)
            )
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysMenuService.update_menu(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/menu/<int:id>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:menu:remove"))
@Log(title="菜单管理",business_type=BusinessType.DELETE)
@JsonSerializer()
def system_menu_delete(id:int):
    '''
        删除菜单
    '''
    if SysMenuService.has_child_by_menu_id(id):
        return AjaxResponse.from_error("该菜单存在下级菜单，不允许删除")
    if SysMenuService.check_menu_exist_role(id):
        return AjaxResponse.from_error("该菜单存已分配角色，不允许删除")
    flag = SysMenuService.delete_menu_by_id(id)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()
