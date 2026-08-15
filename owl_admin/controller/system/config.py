# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from flask_login import login_required

from owl_common.base.transformer import ids_to_list
from owl_common.constant import UserConstants
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator, PathValidator
from owl_common.domain.enum import BusinessType
from owl_common.utils import security_util as SecurityUtil
from owl_system.domain.entity import SysConfig
from owl_system.service.sys_config import SysConfigService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/config/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm('system:config:list'))
@JsonSerializer()
def system_config_list(dto:SysConfig):
    '''
        获取配置项列表
    '''
    rows = SysConfigService.select_config_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/config/export", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm('system:config:export'))
@Log(title="参数管理",business_type=BusinessType.EXPORT)
@JsonSerializer()
def system_config_export(dto:SysConfig):
    '''
        # todo
        导出配置项列表
    '''
    rows = SysConfigService.select_user_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/config/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm('system:config:query'))
@JsonSerializer()
def system_config_get(id:int):
    '''
        根据id，获取配置项
    '''
    sysconfig = SysConfigService.select_config_by_id(id)
    ajax_response = AjaxResponse.from_success(data=sysconfig)
    return ajax_response


@reg.api.route("/system/config/configKey/<key>", methods=["GET"])
@PathValidator()
@login_required
@JsonSerializer()
def system_config_get_by_key(key:str):
    '''
        根据key，获取配置项
    '''
    value = SysConfigService.select_config_by_key(key)
    ajax_response = AjaxResponse.from_success(data = value)
    return ajax_response


@reg.api.route("/system/config", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm('system:config:add'))
@Log(title = "参数管理", business_type = BusinessType.INSERT)
@JsonSerializer()
def system_config_add(dto:SysConfig):
    '''
        添加配置项
    '''
    if UserConstants.NOT_UNIQUE == SysConfigService.check_config_key_unique(dto):
        return AjaxResponse.from_error("配置项已存在:{}".format(dto.config_name))
    dto.create_by_user(SecurityUtil.get_username())
    SysConfigService.insert_config(dto)
    ajax_response = AjaxResponse.from_success()
    return ajax_response


@reg.api.route("/system/config", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm('system:config:edit'))
@Log(title = "参数管理", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_config_update(dto:SysConfig):
    '''
        修改配置项
    '''
    if UserConstants.NOT_UNIQUE == \
        SysConfigService.check_config_key_unique(dto):
        return AjaxResponse.from_error(f"修改参数'{dto.config_key}'失败，参数键名已存在")
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysConfigService.update_config(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/config/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm('system:config:remove'))
@Log(title = "参数管理", business_type = BusinessType.DELETE)
@JsonSerializer()
def system_config_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除配置项
    '''
    SysConfigService.delete_config_by_ids(ids)
    return AjaxResponse.from_success()


@reg.api.route("/system/config/refreshCache", methods=["DELETE"])
@PreAuthorize(HasPerm('system:config:remove'))
@Log(title = "参数管理", business_type = BusinessType.CLEAN)
@JsonSerializer()
def system_config_refresh():
    '''
        刷新配置项缓存
    '''
    SysConfigService.reset_config_cache()
    return AjaxResponse.from_success()