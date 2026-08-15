# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.constant import UserConstants
from owl_common.base.model import AjaxResponse
from owl_common.domain.entity import SysDept
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator,PathValidator
from owl_common.utils import security_util as SecurityUtil
from owl_system.service.sys_dept import SysDeptService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/dept/list", methods=["GET"])
@QueryValidator()
@PreAuthorize(HasPerm("system:dept:list"))
@JsonSerializer()
def system_dept_list(dto:SysDept):
    '''
        获取部门列表
    '''
    rows = SysDeptService.select_dept_list(dto)
    ajax_response = AjaxResponse.from_success(data=rows)
    return ajax_response


@reg.api.route("/system/dept/list/exclude/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:dept:list"))
@JsonSerializer()
def system_dept_list_exclude(id:int):
    '''
        获取部门列表（排除节点）
    '''
    rows = SysDeptService.select_dept_list(None)
    rows_copy = []
    for row in rows:
        if row.dept_id != id:
            rows_copy.append(row)
    ajax_response = AjaxResponse.from_success(data=rows_copy)
    return ajax_response


@reg.api.route("/system/dept/treeselect", methods=["GET"])
@QueryValidator()
@JsonSerializer()
def system_dept_treeselect(dto:SysDept):
    '''
        获取部门下拉树
    '''
    rows = SysDeptService.select_dept_list(dto)
    ajax_response = AjaxResponse.from_success(
        data=SysDeptService.build_dept_tree_select(rows)
    )
    return ajax_response


@reg.api.route("/system/dept/roleDeptTreeselect/<int:roleId>", methods=["GET"])
@PathValidator()
@JsonSerializer()
def system_dept_roletreeselect(role_id:int):
    '''
        获取角色的部门下拉树
    '''
    rows = SysDeptService.select_dept_list(None)
    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, "checked_keys", SysDeptService.select_dept_list_by_role_id(role_id))
    setattr(ajax_response, "depts", SysDeptService.build_dept_tree_select(rows))
    return ajax_response


@reg.api.route("/system/dept/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:dept:query"))
@JsonSerializer()
def system_dept(id:int):
    '''
        获取部门详情
    '''
    SysDeptService.check_dept_data_scope(id)
    dept = SysDeptService.select_dept_by_id(id)
    ajax_response = AjaxResponse.from_success(data=dept)
    return ajax_response


@reg.api.route("/system/dept", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dept:add"))
@Log(title="部门管理",business_type=BusinessType.INSERT)
@JsonSerializer()
def system_dept_create(dto:SysDept):
    '''
        新增部门
    '''
    if UserConstants.NOT_UNIQUE == SysDeptService.check_dept_name_unique(dto):
        ajax_response = AjaxResponse.from_error("部门名称已存在")
        return ajax_response
    dto.create_by_user(SecurityUtil.get_username())
    SysDeptService.insert_dept(dto)
    ajax_response = AjaxResponse.from_success()
    return ajax_response


@reg.api.route("/system/dept", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dept:edit"))
@Log(title="部门管理",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_dept_update(dto:SysDept):
    '''
        修改部门
    '''
    SysDeptService.check_dept_data_scope(dto.dept_id)
    if UserConstants.UNIQUE != SysDeptService.check_dept_name_unique(dto):
        return AjaxResponse.from_error("部门名称已存在")
    elif dto.parent_id == dto.dept_id:
        return AjaxResponse.from_error("上级部门不能是自己")
    elif UserConstants.DEPT_DISABLE == dto.status and \
        SysDeptService.select_normal_children_dept_by_id(dto.id) > 0:
        return AjaxResponse.from_error("该部门包含未停用的子部门！")
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysDeptService.update_dept(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/dept/<int:id>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:dept:remove"))
@Log(title="部门管理",business_type=BusinessType.DELETE)
@JsonSerializer()
def system_dept_delete(id:int):
    '''
        删除部门
    '''
    if SysDeptService.has_child_by_dept_id(id):
        return AjaxResponse.from_error("该部门存在下级部门，不允许删除")
    if SysDeptService.check_dept_exist_user(id):
        return AjaxResponse.from_error("该部门存在用户，不允许删除")
    SysDeptService.check_dept_data_scope(id)
    flag = SysDeptService.delete_dept_by_id(id)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()
