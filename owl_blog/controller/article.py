# -*- coding: utf-8 -*-

"""
文章管理控制器。

负责文章相关 HTTP 请求的接收与参数组装，业务逻辑交由 service 层处理，
异常由全局 errorhandler 统一处理；管理员查看全部数据，普通用户仅查看自己的数据。
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
from owl_blog.domain.entity import BlogArticle
from owl_blog.service import BlogArticleService
from owl_blog.mapper.article import BlogArticleMapper
from owl_blog.utils import get_current_user, is_admin, safe_int
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_admin import reg


@reg.api.route("/blog/article/list", methods=["GET"])
@PreAuthorize(HasPerm("blog:article:list"))
@JsonSerializer()
def blog_article_list():
    """
    文章管理列表 - 只显示当前用户的文章（含草稿）
    管理员看全部，普通用户只看自己的
    """
    current_user = get_current_user()

    g.criterian_meta = CriterianMeta()
    page = PageModel(
        page_num=safe_int(request.args.get('pageNum'), 1),
        page_size=min(safe_int(request.args.get('pageSize'), 10), 100)
    )
    g.criterian_meta.page = page

    dto = BlogArticle()
    dto.title = (request.args.get('title') or '').strip() or None
    dto.status = (request.args.get('status') or '').strip() or None
    category_id = safe_int(request.args.get('categoryId'), None)
    if category_id:
        dto.category_id = category_id

    # 数据隔离：非管理员只看自己的文章
    if not is_admin(current_user):
        dto.author_id = getattr(current_user, 'user_id', -1)

    rows = BlogArticleService.select_article_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/blog/article/pub/list", methods=["GET"])
@JsonSerializer()
def blog_article_pub_list():
    """
    公开文章列表 - 首页用，只显示已发布的文章
    """
    get_current_user()

    g.criterian_meta = CriterianMeta()
    page = PageModel(
        page_num=safe_int(request.args.get('pageNum'), 1),
        page_size=min(safe_int(request.args.get('pageSize'), 10), 100)
    )
    g.criterian_meta.page = page

    dto = BlogArticle()
    dto.title = (request.args.get('title') or '').strip() or None
    dto.status = '1'  # 只看已发布
    category_id = safe_int(request.args.get('categoryId'), None)
    if category_id:
        dto.category_id = category_id

    rows = BlogArticleService.select_article_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/blog/article/<int:id>", methods=["GET"])
@PathValidator()
@JsonSerializer()
def blog_article_get(id: int):
    """
    文章详情
    已发布的人人都能看，草稿只有作者和管理员能看
    """
    current_user = get_current_user()
    eo = BlogArticleService.select_article_by_id(id)

    if eo is None:
        raise NotFoundException("文章不存在")

    # 草稿权限控制
    if getattr(eo, 'status', '1') == '0':
        uid = getattr(current_user, 'user_id', -1)
        if not is_admin(current_user) and eo.author_id != uid:
            raise NotFoundException("文章不存在或无权查看")

    return AjaxResponse.from_success(data=eo)


@reg.api.route("/blog/article", methods=["POST"])
@BodyValidator()
@PreAuthorize(HasPerm("blog:article:add"))
@Log(title="博客文章", business_type=BusinessType.INSERT)
@JsonSerializer()
def blog_article_add(dto: BlogArticle):
    current_user = get_current_user()
    dto.author_id = getattr(current_user, 'user_id')
    dto.create_by_user(getattr(current_user, 'user_name', ''))
    BlogArticleService.insert_article(dto)
    return AjaxResponse.from_success()


@reg.api.route("/blog/article", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("blog:article:edit"))
@Log(title="博客文章", business_type=BusinessType.UPDATE)
@JsonSerializer()
def blog_article_update(dto: BlogArticle):
    current_user = get_current_user()

    if not is_admin(current_user):
        old = BlogArticleService.select_article_by_id(dto.article_id)
        if not old or old.author_id != getattr(current_user, 'user_id', -1):
            return AjaxResponse.from_error(msg="只能修改自己的文章")

    dto.update_by_user(SecurityUtil.get_username())
    flag = BlogArticleService.update_article(dto)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/blog/article/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("blog:article:remove"))
@Log(title="博客文章", business_type=BusinessType.DELETE)
@JsonSerializer()
def blog_article_delete(ids: Annotated[List[int], BeforeValidator(ids_to_list)]):
    current_user = get_current_user()

    if not is_admin(current_user):
        for aid in ids:
            old = BlogArticleService.select_article_by_id(aid)
            if not old or old.author_id != getattr(current_user, 'user_id', -1):
                return AjaxResponse.from_error(msg="只能删除自己的文章")

    flag = BlogArticleService.delete_article_by_ids(ids)
    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/blog/article/view/<int:id>", methods=["PUT"])
@JsonSerializer()
def blog_article_view(id: int):
    BlogArticleService.increment_view_count(id)
    return AjaxResponse.from_success()
