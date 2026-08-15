# -*- coding: utf-8 -*-

"""
分类管理控制器
"""

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from flask import g, request

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse, CriterianMeta, PageModel
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, PathValidator
from owl_common.domain.enum import BusinessType
from owl_common.utils import security_util as SecurityUtil
from owl_common.exception import NotFoundException
from owl_blog.domain.entity import BlogCategory
from owl_blog.service import BlogCategoryService
from owl_blog.utils import get_current_user, safe_int
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_admin import reg


@reg.api.route("/blog/category/list", methods=["GET"])
@JsonSerializer()
def blog_category_list():
    get_current_user()

    g.criterian_meta = CriterianMeta()
    page = PageModel(
        page_num=safe_int(request.args.get('pageNum'), 1),
        page_size=min(safe_int(request.args.get('pageSize'), 10), 100)
    )
    g.criterian_meta.page = page

    dto = BlogCategory()
    dto.category_name = (request.args.get('categoryName') or '').strip() or None
    dto.status = (request.args.get('status') or '').strip() or None

    rows = BlogCategoryService.select_category_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/blog/category/<int:id>", methods=["GET"])
@PathValidator()
@PreAuthorize(HasPerm("blog:category:query"))
@JsonSerializer()
def blog_category_get(id: int):
    eo = BlogCategoryService.select_category_id(id)
    if not eo:
        raise NotFoundException("分类不存在")
    return AjaxResponse.from_success(data=eo)


@reg.api.route("/blog/category", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("blog:category:add"))
@Log(title="博客分类", business_type=BusinessType.INSERT)
@JsonSerializer()
def blog_category_add(dto: BlogCategory):
    dto.create_by_user(SecurityUtil.get_username())
    BlogCategoryService.insert_category(dto)
    return AjaxResponse.from_success()


@reg.api.route("/blog/category", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("blog:category:edit"))
@Log(title="博客分类", business_type=BusinessType.UPDATE)
@JsonSerializer()
def blog_category_update(dto: BlogCategory):
    dto.update_by_user(SecurityUtil.get_username())
    flag = BlogCategoryService.update_category(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/blog/category/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("blog:category:remove"))
@Log(title="博客分类", business_type=BusinessType.DELETE)
@JsonSerializer()
def blog_category_delete(ids: Annotated[List[int], BeforeValidator(ids_to_list)]):
    flag = BlogCategoryService.delete_category_by_ids(ids)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()

