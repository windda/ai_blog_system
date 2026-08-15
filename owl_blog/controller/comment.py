# -*- coding: utf-8 -*-

"""
评论管理控制器。

评论需登录后发表，管理员可审核全部评论，普通用户仅能管理自己的评论；
前台仅展示已通过审核的评论。
"""

from typing import List
from pydantic import BeforeValidator
from typing_extensions import Annotated
from flask import g, request
import datetime

from owl_common.base.transformer import ids_to_list
from owl_common.base.model import AjaxResponse, TableResponse, CriterianMeta, PageModel
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import BodyValidator, PathValidator
from owl_common.domain.enum import BusinessType
from owl_common.exception import ForbiddenException, NotFoundException, UnauthorizedException
from owl_blog.domain.entity import BlogComment
from owl_blog.service import BlogCommentService
from owl_blog.mapper.article import BlogArticleMapper
import traceback

from owl_blog.utils import get_current_user, is_admin, safe_int, sanitize_xss
from owl_framework.descriptor.log import Log
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_admin import reg
from owl_admin.ext import db, redis_cache
from owl_blog.mapper.comment import BlogCommentMapper


@reg.api.route("/blog/comment/list", methods=["GET"])
@PreAuthorize(HasPerm("blog:comment:list"))
@JsonSerializer()
def blog_comment_list():
    """
    后台评论管理列表
    管理员：查看全部
    普通用户：只看自己文章的评论 + 自己发布的评论
    """
    current_user = get_current_user()

    g.criterian_meta = CriterianMeta()
    page = PageModel(
        page_num=safe_int(request.args.get('pageNum'), 1),
        page_size=min(safe_int(request.args.get('pageSize'), 10), 100)
    )
    g.criterian_meta.page = page

    content = (request.args.get('content') or '').strip() or None
    status = (request.args.get('status') or '').strip() or None
    article_id = safe_int(request.args.get('articleId'), None)

    if is_admin(current_user):
        ids = [article_id] if article_id else None
        rows = BlogCommentService.select_comment_page(
            article_ids=ids,
            content=content,
            status=status
        )
    else:
        own_article_ids = BlogArticleMapper.select_article_ids_by_author(current_user.user_id)
        if article_id:
            if article_id not in own_article_ids:
                return AjaxResponse.from_error(msg="无权查看该文章的评论")
            ids = [article_id]
        else:
            ids = own_article_ids
        rows = BlogCommentService.select_comment_page(
            article_ids=ids if ids else [-1],
            content=content,
            status=status
        )

    return TableResponse(rows=rows)


@reg.api.route("/blog/comment/list/<int:article_id>", methods=["GET"])
@JsonSerializer()
def blog_comment_list_by_article(article_id: int):
    """
    文章评论列表
    前台默认只返回已通过的评论
    后台管理员传 ?all=1 可查看所有状态评论
    """
    all_status = request.args.get('all') == '1'

    if all_status:
        from owl_blog.domain.po import BlogCommentPo
        from sqlalchemy import select
        stmt = select(BlogCommentPo) \
            .where(BlogCommentPo.article_id == article_id) \
            .order_by(BlogCommentPo.create_time)
        rows = db.session.execute(stmt).scalars().all()
        comments = BlogCommentMapper._rows_to_list(rows)
    else:
        comments = BlogCommentService.select_comments_by_article(article_id)

    return AjaxResponse.from_success(data=comments)


@reg.api.route("/blog/comment", methods=["POST"])
@BodyValidator()
@Log(title="博客评论", business_type=BusinessType.INSERT)
@JsonSerializer()
def blog_comment_add(dto: BlogComment):
    """
    发表评论（必须登录）。

    游客需先注册登录才能评论；评论人显示为登录用户名；
    文章作者在自己文章下评论自动通过审核。
    """
    article = BlogArticleMapper.select_article_by_id(dto.article_id)
    if not article:
        raise NotFoundException("文章不存在")

    # 强制登录
    current_user = get_current_user()
    dto.user_id = current_user.user_id
    dto.author_name = current_user.user_name

    # Redis 频率限制
    COMMENT_RATE_LIMIT = 60
    COMMENT_MAX_COUNT = 3
    try:
        rate_key = f"blog:comment:rate:user:{current_user.user_id}"
        count = redis_cache.incr(rate_key)
        if count == 1:
            redis_cache.expire(rate_key, COMMENT_RATE_LIMIT)
        if count > COMMENT_MAX_COUNT:
            ttl = redis_cache.ttl(rate_key)
            return AjaxResponse.from_error(msg=f"评论过于频繁，请 {ttl} 秒后再试")
    except Exception:
        traceback.print_exc()

    # XSS 过滤
    if dto.content:
        dto.content = sanitize_xss(dto.content)

    dto.create_time = datetime.datetime.now()
    # 审核策略：文章作者在自己文章下评论 → 自动通过
    auto_approved = (article.author_id == current_user.user_id)
    dto.status = "1" if auto_approved else "0"
    BlogCommentService.insert_comment(dto)

    msg = "评论成功" if auto_approved else "评论成功，等待审核"
    return AjaxResponse.from_success(msg=msg)


@reg.api.route("/blog/comment/status", methods=["PUT"])
@BodyValidator()
@PreAuthorize(HasPerm("blog:comment:edit"))
@Log(title="博客评论", business_type=BusinessType.UPDATE)
@JsonSerializer()
def blog_comment_status(dto: BlogComment):
    """审核评论（管理员或文章作者）+ 站内通知"""
    current_user = get_current_user()
    
    # 检查权限：管理员 或 文章作者
    comment = BlogCommentService.select_comment_by_id(dto.comment_id)
    if not comment:
        raise NotFoundException("评论不存在")
    article = BlogArticleMapper.select_article_by_id(comment.article_id)
    if not is_admin(current_user) and article.author_id != current_user.user_id:
        raise ForbiddenException("无权审核此评论")

    flag = BlogCommentService.update_comment_status(dto.comment_id, dto.status)

    if flag and article and article.author_id:
        try:
            status_label = {"1": "通过", "2": "驳回"}.get(dto.status, "已审核")
            from owl_system.mapper import SysNoticeMapper
            from owl_system.domain.entity import SysNotice
            notice = SysNotice(
                notice_title=f"评论审核{status_label}",
                notice_type="1",
                notice_content=f"您在「{article.title}」下的评论已审核{status_label}。",
                create_by=current_user.user_name,
                create_time=datetime.datetime.now()
            )
            SysNoticeMapper.insert_notice(notice)

            try:
                from owl_admin.ext import socketio
                socketio.emit('new_notification', {
                    'title': f"评论审核{status_label}",
                    'content': f"您在「{article.title}」下的评论已审核{status_label}。",
                    'time': datetime.datetime.now().isoformat(),
                    'type': 'comment_audit'
                }, room=f"user:{article.author_id}")
            except Exception:
                pass
        except Exception:
            pass

    return AjaxResponse.from_success() if flag else AjaxResponse.from_error()


@reg.api.route("/blog/comment/<ids>", methods=["DELETE"])
@PathValidator()
@PreAuthorize(HasPerm("blog:comment:remove"))
@Log(title="博客评论", business_type=BusinessType.DELETE)
@JsonSerializer()
def blog_comment_delete(ids: Annotated[List[int], BeforeValidator(ids_to_list)]):
    """删除评论"""
    current_user = get_current_user()

    for comment_id in ids:
        comment = BlogCommentService.select_comment_by_id(comment_id)
        if not comment:
            raise NotFoundException("评论不存在")

        if not is_admin(current_user):
            if comment.user_id != current_user.user_id:
                raise ForbiddenException("只能删除自己的评论")

        BlogCommentService.delete_comment_by_id(comment_id)

    return AjaxResponse.from_success()