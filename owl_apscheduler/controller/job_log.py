# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from owl_apscheduler.domain.entity import SysJobLog
from owl_apscheduler.service.job_log import SysJobLogService
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.base.transformer import ids_to_list
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import QueryValidator
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from .. import reg


@reg.api.route("/monitor/jobLog/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm('monitor:job:list'))
@JsonSerializer()
def common_joblog_list(dto: SysJobLog):
    """
    获取定时任务日志列表
    
    Args:
        dto: 查询条件
    
    Returns:
        TableResponse: 响应数据
    """
    rows:List[SysJobLog] = SysJobLogService.select_job_log_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/monitor/jobLog/export", methods=["POST"])
@PreAuthorize(HasPerm('monitor:job:export'))
@JsonSerializer()
def common_joblog_export():
    """
    导出定时任务日志
    
    Returns:
        Response: 响应数据
    """
    return "Hello, World!"


@reg.api.route("/monitor/jobLog/<int:id>", methods=["GET"])
@PreAuthorize(HasPerm('monitor:job:query'))
@JsonSerializer()
def common_joblog_detail(id:int):
    """
    获取定时任务日志详情
    
    Args:
        id: 日志ID
    
    Returns:
        AjaxResponse: 响应数据
    """
    joblog = SysJobLogService.select_job_log_by_id(id)
    ajax_response = AjaxResponse.from_success(data=joblog)
    return ajax_response


@reg.api.route("/monitor/jobLog/<ids>", methods=["DELETE"])
@PreAuthorize(HasPerm('monitor:job:remove'))
@JsonSerializer()
def common_joblog_remove(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
) -> AjaxResponse:
    """
    批量删除定时任务日志
    
    Args:
        ids(List[int]): 日志ID列表
    
    Returns:
        AjaxResponse: 响应数据
    """
    flag = SysJobLogService.delete_job_log_by_ids(ids)
    ajax_response = AjaxResponse.from_success() if flag > 0 else AjaxResponse.from_error()
    return ajax_response


@reg.api.route("/monitor/jobLog/clean", methods=["DELETE"])
@PreAuthorize(HasPerm('monitor:job:remove'))
@JsonSerializer()
def common_joblog_clean():
    """
    清空定时任务日志
    
    Returns:
        AjaxResponse: 响应数据
    """
    SysJobLogService.clean_job_logs()
    return AjaxResponse.from_success()
