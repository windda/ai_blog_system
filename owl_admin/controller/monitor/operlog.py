# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.validator import QueryValidator, PathValidator
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.domain.enum import BusinessType
from owl_system.domain.entity import SysOperLog
from owl_system.service.sys_oper_log import SysOperLogService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route('/monitor/operlog/list',methods=['GET'])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("monitor:operlog:list"))
@JsonSerializer()
def monitor_operlog_list(dto:SysOperLog):
    '''
        查询登录日志列表
    '''
    rows = SysOperLogService.select_operlog_list(dto)
    return TableResponse(rows=rows)


@reg.api.route('/monitor/operlog/export',methods=['POST'])
@PreAuthorize(HasPerm("monitor:operlog:EXPORT"))
@Log(title = "操作日志", business_type = BusinessType.EXPORT)
@BaseSerializer()
def monitor_operlog_export():
    '''
        导出登录日志
    '''
    # todo
    return AjaxResponse.from_success()


@reg.api.route('/monitor/operlog/<ids>',methods=['DELETE'])
@PathValidator()
@PreAuthorize(HasPerm("monitor:operlog:remove"))
@Log(title = "操作日志", business_type = BusinessType.DELETE)
@JsonSerializer()
def monitor_operlog_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        批量删除登录日志
    '''
    SysOperLogService.delete_operlog_by_ids(ids)
    return AjaxResponse.from_success()


@reg.api.route('/monitor/operlog/clean',methods=['DELETE'])
@PreAuthorize(HasPerm("monitor:operlog:remove"))
@Log(title = "操作日志", business_type = BusinessType.CLEAN)
@JsonSerializer()
def monitor_operlog_clean():
    '''
        清空登录日志
    '''
    SysOperLogService.clean_operlog()
    return AjaxResponse.from_success()
