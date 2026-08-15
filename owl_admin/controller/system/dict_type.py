# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from flask_login import login_required

from owl_common.base.transformer import ids_to_list
from owl_common.constant import UserConstants
from owl_common.base.model import AjaxResponse, TableResponse
from owl_common.domain.entity import SysDictType
from owl_common.domain.enum import BusinessType
from owl_common.descriptor.serializer import BaseSerializer, JsonSerializer
from owl_common.descriptor.validator import BodyValidator, QueryValidator, PathValidator
from owl_common.utils import security_util as SecurityUtil
from owl_system.service import SysDictTypeService
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route("/system/dict/type/list", methods=["GET"])
@QueryValidator(is_page=True)
@PreAuthorize(HasPerm("system:dict:list"))
@JsonSerializer()
def system_dict_type_list(dto:SysDictType):
    '''
        获取字典类型列表
    '''
    rows = SysDictTypeService.select_dict_type_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/dict/type/export", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:export"))
@Log(title = "字典类型", business_type = BusinessType.EXPORT)
@BaseSerializer()
def system_dict_type_export(dto:SysDictType):
    '''
        # todo
        导出字典类型列表
    '''
    rows = SysDictTypeService.select_dict_type_list(dto)
    table_response = TableResponse(rows=rows)
    return table_response


@reg.api.route("/system/dict/type/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("system:dict:query"))
@JsonSerializer()
def system_dict_type_get(id:int):
    '''
        根据id，获取字典类型
    '''
    eo = SysDictTypeService.select_dict_type_by_id(id)
    return AjaxResponse.from_success(data=eo) if eo else  \
        AjaxResponse.from_error(data="字典类型不存在")


@reg.api.route("/system/dict/type", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:add"))
@Log(title = "字典类型", business_type = BusinessType.INSERT)
@JsonSerializer()
def system_dict_type_add(dto:SysDictType):
    '''
        添加字典类型
    '''
    if UserConstants.NOT_UNIQUE == SysDictTypeService.check_dict_type_unique(dto):
        return AjaxResponse.from_error("新增字典'{}'失败，字典已存在".format(dto.dict_name))
    dto.create_by_user(SecurityUtil.get_username())
    SysDictTypeService.insert_dict_type(dto)
    return AjaxResponse.from_success()


@reg.api.route("/system/dict/type", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("system:dict:edit"))
@Log(title = "字典类型", business_type = BusinessType.UPDATE)
@JsonSerializer()
def system_dict_type_update(dto:SysDictType):
    '''
        修改字典类型
    '''
    if UserConstants.NOT_UNIQUE == SysDictTypeService.check_dict_type_unique(dto):
        return AjaxResponse.from_error(
            "修改字典'{}'失败，字典已存在".format(dto.dict_name)
        )
    dto.update_by_user(SecurityUtil.get_username())
    flag = SysDictTypeService.update_dict_type(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/system/dict/type/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("system:dict:remove"))
@Log(title = "字典类型", business_type = BusinessType.DELETE)
@JsonSerializer()
def system_dict_type_delete(
    ids: Annotated[List[int],BeforeValidator(ids_to_list)]
):
    '''
        删除字典类型
    '''
    SysDictTypeService.delete_dict_type_by_ids(ids)
    return AjaxResponse.from_success()


@reg.api.route("/system/dict/type/refreshCache", methods=["DELETE"])
@PreAuthorize(HasPerm("system:dict:remove"))
@Log(title = "字典类型", business_type = BusinessType.CLEAN)
@JsonSerializer()
def system_dict_type_refresh():
    '''
        刷新字典类型缓存
    '''
    SysDictTypeService.reset_dict_type_cache()
    return AjaxResponse.from_success()


@reg.api.route("/system/dict/type/optionselect", methods=["GET"])
@login_required
@JsonSerializer()
def system_dict_type_optionselect():
    '''
        获取字典选择框列表
    '''
    rows:List[SysDictType] = SysDictTypeService.select_dict_type_all()
    return AjaxResponse.from_success(data=rows)
