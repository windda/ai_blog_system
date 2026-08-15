# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator, PathValidator
from owl_common.utils import security_util as SecurityUtil
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_system.domain.entity import SysPost
from owl_system.service import SysPostService
from ... import reg


@reg.api.route("/system/post/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("system:post:list"))
@JsonSerializer()
def system_post_list(dto:SysPost):
    '''
        获取岗位信息列表
    '''
    rows = SysPostService.select_post_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/post/export", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:post:export"))
@Log(title = "岗位管理", business_type = BusinessType.EXPORT)
@BaseSerializer()
def system_post_export(dto:SysPost):
    '''
        # todo
        导出岗位信息列表
    '''
    rows = SysPostService.select_post_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/post/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:post:query"))
@JsonSerializer()
def system_post_get(id:int):
    '''
        根据id，获取岗位信息
    '''
    eo = SysPostService.select_post_by_id(id)
    return AjaxResponse.from_success(data=eo) \
        if eo else AjaxResponse.from_error()


@reg.api.route("/system/post", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:post:add"))
@Log(title = "岗位管理", business_type = BusinessType.INSERT)
@JsonSerializer()
def system_post_add(dto:SysPost):
    '''
        添加岗位信息
    '''
    dto.create_by_user(SecurityUtil.get_username())
    SysPostService.insert_post(dto)
    ajax_response = AjaxResponse.from_success()
    return ajax_response


@reg.api.route("/system/post", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:post:edit"))
@Log(title = "岗位管理", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_post_update(dto:SysPost):
    '''
        修改岗位信息
    '''
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysPostService.update_post(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/post/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:post:remove"))
@Log(title = "岗位管理", business_type = BusinessType.DELETE)
@JsonSerializer()
def system_post_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除岗位信息
    '''
    flag = SysPostService.delete_post_by_ids(ids)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()
