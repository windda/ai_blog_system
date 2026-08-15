# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.descriptor.validator import QueryValidator, PathValidator
from owl_common.domain.enum import BusinessType
from owl_system.domain.entity import SysLogininfor
from owl_system.service.sys_logininfo import SysLogininforService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route('/monitor/logininfor/list',methods=['GET'])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("monitor:logininfor:list"))
@JsonSerializer()
def monitor_logininfo_list(dto:SysLogininfor):
    '''
        查询登录日志列表
    '''
    rows = SysLogininforService.select_logininfor_list(dto)
    return TableResponse(rows=rows)


@reg.api.route('/monitor/logininfor/export',methods=['POST'])
@PreAuthorize(HasPerm("monitor:logininfor:export"))
@Log(title = "登录日志", business_type = BusinessType.EXPORT)
@BaseSerializer()
def monitor_logininfo_export():
    '''
        导出登录日志
    '''
    # todo
    return AjaxResponse.from_success()


@reg.api.route('/monitor/logininfor/<ids>',methods=['DELETE'])
@PathValidator()
@PreAuthorize(HasPerm("monitor:logininfor:remove"))
@Log(title = "登录日志", business_type = BusinessType.DELETE)
@JsonSerializer()
def monitor_logininfo_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        批量删除登录日志
    '''
    SysLogininforService.delete_logininfor(ids)
    return AjaxResponse.from_success()


@reg.api.route('/monitor/logininfor/clean',methods=['DELETE'])
@PreAuthorize(HasPerm("monitor:logininfor:remove"))
@Log(title = "登录日志", business_type = BusinessType.CLEAN)
@JsonSerializer()
def monitor_logininfo_clean():
    '''
        清空登录日志
    '''
    SysLogininforService.clean_logininfor()
    return AjaxResponse.from_success()