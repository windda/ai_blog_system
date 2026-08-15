# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from flask_login import login_required

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.domain.entity import SysDictData
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator, PathValidator
from owl_common.utils import security_util as SecurityUtil
from owl_system.service import SysDictDataService
from owl_system.service.sys_dict_type import SysDictTypeService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/dict/data/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("system:dict:list"))
@JsonSerializer()
def system_dict_data_list(dto:SysDictData):
    '''
        获取字典数据列表
    '''
    rows = SysDictDataService.select_dict_data_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/system/dict/data/export", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:export"))
@Log(title = "字典数据", business_type = BusinessType.EXPORT)
@BaseSerializer()
def system_dict_data_export(dto:SysDictData):
    '''
        # todo
        导出字典数据列表
    '''
    rows = SysDictDataService.select_dict_data_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/system/dict/data/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:dict:query"))
@JsonSerializer()
def system_dict_data_get(id:int):
    '''
        根据id，获取字典数据
    '''
    eo = SysDictDataService.select_dict_data_by_id(id)
    return AjaxResponse.from_success(data=eo)


@reg.api.route("/system/dict/data/type/<name>", methods=["GET"])
@PathValidator()
@login_required
@JsonSerializer()
def system_dict_data_by_type(name:str):
    '''
        根据字典类型查询字典数据信息
    '''
    eos: List[SysDictData] = SysDictTypeService.select_dict_data_by_type(name)
    return AjaxResponse.from_success(data=eos)


@reg.api.route("/system/dict/data", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:add"))
@Log(title = "字典数据", business_type = BusinessType.INSERT)
@JsonSerializer()
def system_dict_data_add(dto:SysDictData):
    '''
        添加字典数据
    '''
    dto.create_by_user(SecurityUtil.get_username())
    SysDictDataService.insert_dict_data(dto)
    ajax_response = AjaxResponse.from_success()
    return ajax_response


@reg.api.route("/system/dict/data", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:edit"))
@Log(title = "字典数据", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_dict_data_update(dto:SysDictData):
    '''
        修改字典数据
    '''
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysDictDataService.update_dict_data(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/dict/data/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:dict:remove"))
@Log(title="字典数据",business_type = BusinessType.DELETE)
@JsonSerializer()
def system_dict_data_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除字典数据
    '''
    flag = SysDictDataService.delete_dict_data_by_ids(ids)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()
