# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator, PathValidator
from owl_common.domain.enum import BusinessType
from owl_common.utils import security_util as SecurityUtil
from owl_system.domain.entity import SysNotice
from owl_system.service import SysNoticeService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/notice/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("system:notice:list"))
@JsonSerializer()
def system_notice_list(dto:SysNotice):
    '''
        获取公告信息列表
    '''
    rows = SysNoticeService.select_notice_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/notice/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:notice:query"))
@JsonSerializer()
def system_notice_get(id:int):
    '''
        根据id，获取公告信息
    '''
    eo = SysNoticeService.select_notice_by_id(id)
    return AjaxResponse.from_success(data=eo) if eo else \
        AjaxResponse.from_error()


@reg.api.route("/system/notice", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:notice:add"))
@Log(title="通知公告",business_type=BusinessType.INSERT)
@JsonSerializer()
def system_notice_add(dto:SysNotice):
    '''
        添加公告信息
    '''
    dto.create_by_user(SecurityUtil.get_username())
    SysNoticeService.insert_notice(dto)
    return AjaxResponse.from_success()


@reg.api.route("/system/notice", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:notice:edit"))
@Log(title="通知公告",business_type=BusinessType.UPDATE)
@JsonSerializer()
def system_notice_update(dto:SysNotice):
    '''
        修改公告信息
    '''
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysNoticeService.update_notice(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/notice/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:notice:remove"))
@Log(title="通知公告",business_type=BusinessType.DELETE)
@JsonSerializer()
def system_notice_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除公告信息
    '''
    flag = SysNoticeService.delete_notice_by_ids(ids)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()
