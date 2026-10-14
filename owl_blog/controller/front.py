# -*- coding: utf-8 -*-

"""
前台博客展示控制器（公开接口，无需登录）。

首页文章列表使用 Redis 缓存（30 分钟过期）；
文章阅读量通过 Redis 计数器自增，由定时任务批量同步 MySQL。
"""

import json
import re

from flask import request, g
from sqlalchemy import select

from owl_common.base.model import AjaxResponse, TableResponse, CriterianMeta, PageModel
from owl_common.descriptor.serializer import JsonSerializer
from owl_blog.domain.entity import BlogArticle
from owl_blog.service import BlogArticleService, BlogCategoryService, BlogTagService, BlogCommentService
from owl_blog.mapper.article import BlogArticleMapper
from owl_blog.mapper.category import BlogCategoryMapper
from owl_blog.mapper.tag import BlogTagMapper
from owl_blog.mapper.comment import BlogCommentMapper
from owl_admin.ext import db, redis_cache
from owl_admin import reg
from owl_blog.utils import safe_int


# Redis Key 常量
HOT_ARTICLES_KEY = "blog:hot_articles"
PV_COUNTER_KEY = "blog:article:pv:counter"
CACHE_ARTICLE_LIST_PREFIX = "blog:front:article_list"


def _invalidate_article_cache():
    """清除所有首页文章列表 Redis 缓存（点赞/收藏变更后调用）"""
    try:
        keys = redis_cache.keys(f"{CACHE_ARTICLE_LIST_PREFIX}:*")
        if keys:
            redis_cache.delete(*keys)
    except Exception:
        pass


# ---- PV 补齐辅助函数 ----
def _get_article_id(row):
    if isinstance(row, dict):
        return row.get('articleId') or row.get('article_id')
    return getattr(row, 'article_id', None)

def _get_view_count(row):
    if isinstance(row, dict):
        return row.get('viewCount') or row.get('view_count') or 0
    return getattr(row, 'view_count', 0) or 0

def _set_view_count(row, value):
    if isinstance(row, dict):
        row['viewCount'] = value
        row['view_count'] = value
    else:
        row.view_count = value


# ==================== 首页 ====================

@reg.api.route("/front/article/list", methods=["GET"])
@JsonSerializer()
def front_article_list():
    """前台公开文章列表（无需登录）"""
    g.criterian_meta = CriterianMeta()
    page = PageModel(
        page_num=safe_int(request.args.get('pageNum'), 1),
        page_size=min(safe_int(request.args.get('pageSize'), 10), 50)
    )
    g.criterian_meta.page = page

    dto = BlogArticle()
    dto.status = '1'

    keyword = (request.args.get('keyword') or '').strip()
    if keyword:
        keyword = keyword[:100]
        keyword = re.sub(r'[\'";\\]', '', keyword)
        keyword = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', keyword)
        keyword = re.sub(r'\s+', ' ', keyword).strip()
        if keyword:
            dto.title = keyword

    category_id = safe_int(request.args.get('categoryId'), None)
    if category_id:
        dto.category_id = category_id

    cache_key = None
    if not keyword and not category_id and page.page_num == 1:
        cache_key = f"{CACHE_ARTICLE_LIST_PREFIX}:page1_size{page.page_size}"

    from_cache = False
    rows_data = None
    if cache_key:
        try:
            cached = redis_cache.get(cache_key)
            if cached:
                rows_data = json.loads(cached)
                from_cache = True
        except Exception:
            pass

    if from_cache:
        if isinstance(rows_data, dict):
            rows = rows_data.get('rows', [])
            if 'total' in rows_data:
                page.total = rows_data['total']
        else:
            rows = rows_data
    else:
        rows = BlogArticleService.select_article_list(dto)

    if rows:
        try:
            all_pv = redis_cache.hgetall(PV_COUNTER_KEY) or {}
            pv_dict = {}
            for k, v in all_pv.items():
                try:
                    pv_dict[int(k)] = int(v)
                except (ValueError, TypeError):
                    pass
            for r in rows:
                aid = _get_article_id(r)
                if aid and aid in pv_dict:
                    current = _get_view_count(r) or 0
                    if pv_dict[aid] > current:
                        _set_view_count(r, pv_dict[aid])
        except Exception:
            pass

    if cache_key and rows and not from_cache:
        try:
            table_resp = TableResponse(rows=rows)
            serialized = table_resp.model_dump_json(by_alias=True)
            serialized_data = json.loads(serialized)
            cache_data = {"rows": serialized_data['rows'], "total": serialized_data.get('total', len(rows))}
            redis_cache.setex(cache_key, 1800, json.dumps(cache_data, default=str))
        except Exception:
            pass

    return TableResponse(rows=rows)


# ==================== 文章详情 ====================

@reg.api.route("/front/article/<int:id>", methods=["GET"])
@JsonSerializer()
def front_article_detail(id: int):
    """前台文章详情"""
    eo = BlogArticleMapper.select_article_by_id(id)
    if eo is None or getattr(eo, 'status', '0') != '1':
        from owl_common.exception import NotFoundException
        raise NotFoundException("文章不存在")

    anonymous_display = False
    try:
        from owl_common.owl.config import CONFIG_CACHE
        anonymous_display = CONFIG_CACHE.get('blog.anonymous_display', False)
        if isinstance(anonymous_display, str):
            anonymous_display = anonymous_display.lower() in ('true', '1', 'yes')
    except Exception:
        pass
    if anonymous_display:
        eo.author_name = None

    # 浏览量：直接写数据库持久化（移除 Redis 后，不再依赖定时任务同步）
    try:
        BlogArticleService.increment_view_count(id)
        if eo.view_count is not None:
            eo.view_count += 1
        _invalidate_article_cache()  # 清列表缓存，让首页封面浏览量实时更新
    except Exception:
        pass

    return AjaxResponse.from_success(data=eo)


# ==================== 热门文章 ====================

@reg.api.route("/front/hot-articles", methods=["GET"])
@JsonSerializer()
def front_hot_articles():
    """热门文章排行（按浏览量 view_count 降序）"""
    limit = min(safe_int(request.args.get('limit'), 5), 20)
    from sqlalchemy import select
    from owl_blog.domain.po import BlogArticlePo
    stmt = select(BlogArticlePo.article_id, BlogArticlePo.title, BlogArticlePo.view_count) \
        .where(BlogArticlePo.status == '1') \
        .order_by(BlogArticlePo.view_count.desc()).limit(limit)
    rows = db.session.execute(stmt).all()
    articles = [{"articleId": r.article_id, "title": r.title, "viewCount": r.view_count or 0} for r in rows]
    return AjaxResponse.from_success(data=articles)


# ==================== 分类/标签/专栏 ====================

@reg.api.route("/front/categories", methods=["GET"])
@JsonSerializer()
def front_categories():
    """前台分类列表（含文章数）- GROUP BY 优化"""
    from sqlalchemy import select, func
    from owl_blog.domain.po import BlogArticlePo
    categories = BlogCategoryMapper.select_category_list(None) or []
    count_stmt = select(BlogArticlePo.category_id, func.count(BlogArticlePo.article_id)) \
        .where(BlogArticlePo.status == '1', BlogArticlePo.category_id.in_([c.category_id for c in categories])) \
        .group_by(BlogArticlePo.category_id) if categories else None
    count_map = {}
    if count_stmt is not None:
        count_map = dict(db.session.execute(count_stmt).all())
    result = [{"categoryId": cat.category_id, "categoryName": cat.category_name, "articleCount": count_map.get(cat.category_id, 0)} for cat in categories]
    return AjaxResponse.from_success(data=result)


@reg.api.route("/front/tags", methods=["GET"])
@JsonSerializer()
def front_tags():
    tags = BlogTagMapper.select_tag_list(None) or []
    return AjaxResponse.from_success(data=tags)


@reg.api.route("/front/columns", methods=["GET"])
@JsonSerializer()
def front_columns():
    from owl_blog.mapper.column import BlogColumnMapper
    columns = BlogColumnMapper.select_public_list()
    return AjaxResponse.from_success(data=columns)


@reg.api.route("/front/column/<int:column_id>", methods=["GET"])
@JsonSerializer()
def front_column_detail(column_id: int):
    from owl_blog.mapper.column import BlogColumnMapper
    column = BlogColumnMapper.select_by_id(column_id)
    if not column or column.status != '1':
        from owl_common.exception import NotFoundException
        raise NotFoundException("专栏不存在或未公开")
    author_articles = BlogArticleMapper.select_article_list(BlogArticle(author_id=column.author_id, status='1'))
    return AjaxResponse.from_success(data={"column": column, "articles": author_articles})


@reg.api.route("/front/related-articles/<int:article_id>", methods=["GET"])
@JsonSerializer()
def front_related_articles(article_id: int):
    article = BlogArticleMapper.select_article_by_id(article_id)
    if not article:
        from owl_common.exception import NotFoundException
        raise NotFoundException("文章不存在")
    related = []
    if article.category_id:
        dto = BlogArticle(category_id=article.category_id, status='1')
        all_related = BlogArticleMapper.select_article_list(dto)
        related = [a for a in all_related if a.article_id != article_id][:5]
    if len(related) < 5 and article.tags:
        tag_ids = [t.tag_id for t in article.tags]
        if tag_ids:
            from sqlalchemy import select
            from owl_blog.domain.po import BlogArticleTagPo
            aid_rows = db.session.execute(
                select(BlogArticleTagPo.article_id).where(BlogArticleTagPo.tag_id.in_(tag_ids)).limit(10)
            ).scalars().all()
            exclude_ids = [article_id] + [a.article_id for a in related]
            for aid in aid_rows:
                if aid not in exclude_ids:
                    a = BlogArticleMapper.select_article_by_id(aid)
                    if a and a.status == '1':
                        related.append(a)
                        if len(related) >= 5:
                            break
    return AjaxResponse.from_success(data=related)


# ==================== 点赞 ====================

from owl_common.utils import security_util as SecurityUtil
from owl_blog.mapper.article import BlogArticleLikeMapper

@reg.api.route("/front/article/<int:id>/like", methods=["POST"])
@JsonSerializer()
def front_article_like(id: int):
    """点赞/取消点赞（切换）"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录后再点赞")

    article = BlogArticleMapper.select_article_by_id(id)
    if not article or article.status != '1':
        from owl_common.exception import NotFoundException
        raise NotFoundException("文章不存在")

    already_liked = BlogArticleLikeMapper.has_liked(id, user_id)
    if already_liked:
        BlogArticleLikeMapper.delete_like(id, user_id)
        article.like_count = max((article.like_count or 1) - 1, 0)
        BlogArticleMapper.decrement_like_count(id)
        _invalidate_article_cache()
        return AjaxResponse.from_success(data={"liked": False, "likeCount": article.like_count})
    else:
        ok = BlogArticleLikeMapper.insert_like(id, user_id)
        if not ok:
            return AjaxResponse.from_error(msg="点赞失败，请稍后重试")
        article.like_count = (article.like_count or 0) + 1
        BlogArticleMapper.increment_like_count(id)
        _invalidate_article_cache()
        return AjaxResponse.from_success(data={"liked": True, "likeCount": article.like_count})


@reg.api.route("/front/article/<int:id>/like/status", methods=["GET"])
@JsonSerializer()
def front_article_like_status(id: int):
    user_id = None
    try: user_id = SecurityUtil.get_user_id()
    except Exception: pass
    liked = False
    if user_id:
        try: liked = BlogArticleLikeMapper.has_liked(id, user_id)
        except Exception: pass
    article = BlogArticleMapper.select_article_by_id(id)
    like_count = article.like_count if article else 0
    return AjaxResponse.from_success(data={"liked": liked, "likeCount": like_count or 0})


@reg.api.route("/front/article/<int:id>/like/users", methods=["GET"])
@JsonSerializer()
def front_article_like_users(id: int):
    users = BlogArticleLikeMapper.get_like_users(id)
    return AjaxResponse.from_success(data=users)


# ==================== 收藏 ====================

from owl_blog.mapper.article import BlogArticleCollectMapper

@reg.api.route("/front/article/<int:id>/collect", methods=["POST"])
@JsonSerializer()
def front_article_collect(id: int):
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录后再收藏")
    article = BlogArticleMapper.select_article_by_id(id)
    if not article or article.status != '1':
        from owl_common.exception import NotFoundException
        raise NotFoundException("文章不存在")
    collected = BlogArticleCollectMapper.toggle_collect(id, user_id)
    return AjaxResponse.from_success(data={"collected": collected})


@reg.api.route("/front/article/<int:id>/collect/status", methods=["GET"])
@JsonSerializer()
def front_article_collect_status(id: int):
    user_id = None
    try: user_id = SecurityUtil.get_user_id()
    except Exception: pass
    collected = False
    if user_id:
        try: collected = BlogArticleCollectMapper.is_collected(id, user_id)
        except Exception: pass
    return AjaxResponse.from_success(data={"collected": collected})


# ==================== 个人中心 ====================

from owl_blog.mapper.article import BlogViewHistoryMapper

@reg.api.route("/front/user/collections", methods=["GET"])
@JsonSerializer()
def front_user_collections():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 10), 50)
    keyword = (request.args.get('keyword') or '').strip()
    items, total = BlogArticleCollectMapper.get_user_collections(user_id, page_num, page_size, keyword=keyword or None)
    return TableResponse(rows=items, total=total)


@reg.api.route("/front/user/history", methods=["GET"])
@JsonSerializer()
def front_user_history():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 10), 50)
    keyword = (request.args.get('keyword') or '').strip()
    items, total = BlogViewHistoryMapper.get_user_history(user_id, page_num, page_size, keyword=keyword or None)
    return TableResponse(rows=items, total=total)


@reg.api.route("/front/user/history/clear", methods=["POST"])
@JsonSerializer()
def front_user_clear_history():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    BlogViewHistoryMapper.clear_history(user_id)
    return AjaxResponse.from_success(msg="浏览历史已清空")


@reg.api.route("/front/user/article/list", methods=["GET"])
@JsonSerializer()
def front_user_article_list():
    """我的文章分页列表（支持标题搜索）"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 10), 50)
    keyword = (request.args.get('keyword') or '').strip()
    g.criterian_meta = CriterianMeta()
    g.criterian_meta.page = PageModel(page_num=page_num, page_size=page_size)
    dto = BlogArticle(author_id=user_id, title=keyword or None)
    rows = BlogArticleService.select_article_list(dto)
    return TableResponse(rows=rows)


@reg.api.route("/front/user/comment/list", methods=["GET"])
@JsonSerializer()
def front_user_comment_list():
    """我的评论分页列表"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 10), 50)
    keyword = (request.args.get('keyword') or '').strip()
    rows = BlogCommentMapper.select_comment_list_by_user(user_id, page_num, page_size, keyword=keyword or None)
    total = BlogCommentMapper.count_by_user(user_id)
    return TableResponse(rows=rows, total=total)


@reg.api.route("/front/user/info", methods=["GET"])
@JsonSerializer()
def front_user_info():
    """获取当前登录用户信息（前台个人中心用）"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    from owl_system.mapper import SysUserMapper
    user = SysUserMapper.select_user_detail_by_id(user_id)
    if not user:
        from owl_common.exception import NotFoundException
        raise NotFoundException("用户不存在")
    return AjaxResponse.from_success(data={
        "userId": user.user_id,
        "userName": user.user_name,
        "nickName": user.nick_name or user.user_name,
        "email": user.email or '',
        "phonenumber": user.phonenumber or '',
        "avatar": user.avatar or '',
        "remark": user.remark or ''
    })


@reg.api.route("/front/user/profile/update", methods=["PUT"])
@JsonSerializer()
def front_user_profile_update():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    data = request.get_json() or {}
    from owl_system.service import SysUserService
    SysUserService.update_profile(
        user_id,
        nick_name=data.get('nickName'),
        introduction=data.get('introduction'),
        email=data.get('email'),
        phonenumber=data.get('phonenumber'),
        avatar=data.get('avatar')
    )
    return AjaxResponse.from_success(msg="资料更新成功")


@reg.api.route("/front/user/avatar", methods=["POST"])
@JsonSerializer()
def front_user_avatar_upload():
    """前台用户头像上传"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    if 'avatarfile' not in request.files:
        return AjaxResponse.from_error(msg="没有上传文件")
    file = request.files['avatarfile']
    if file.filename == '':
        return AjaxResponse.from_error(msg="没有选择文件")
    import os
    import time
    from werkzeug.utils import secure_filename
    from owl_common.config import OWLConfig
    upload_dir = os.path.join(OWLConfig.profile, 'avatar')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    timestamp = str(int(time.time() * 1000))
    safe_name = secure_filename(file.filename)
    if '.' not in safe_name:
        safe_name += '.png'
    new_filename = f"{timestamp}_{safe_name}"
    file.save(os.path.join(upload_dir, new_filename))
    avatar_path = f"/uploads/avatar/{new_filename}"
    from owl_system.service import SysUserService
    SysUserService.update_profile(user_id, avatar=avatar_path)
    return AjaxResponse.from_success(data={"avatar": avatar_path}, msg="头像上传成功")


@reg.api.route("/front/user/password/update", methods=["PUT"])
@JsonSerializer()
def front_user_password_update():
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    data = request.get_json() or {}
    old_pwd = data.get('oldPassword', '')
    new_pwd = data.get('newPassword', '')
    if not old_pwd or not new_pwd:
        return AjaxResponse.from_error(msg="旧密码和新密码不能为空")
    from owl_system.service import SysUserService
    SysUserService.update_password(user_id, old_pwd, new_pwd)
    return AjaxResponse.from_success(msg="密码修改成功")


# ==================== 前台文章管理（发布/编辑/删除） ====================

@reg.api.route("/front/user/article", methods=["POST"])
@JsonSerializer()
def front_user_article_add():
    """前台用户发布文章"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    data = request.get_json() or {}
    from owl_blog.utils import sanitize_html
    dto = BlogArticle(
        title=data.get('title', '').strip(),
        content=sanitize_html(data.get('content', '')),
        summary=data.get('summary', '').strip() or None,
        cover_image=data.get('coverImage') or None,
        category_id=data.get('categoryId') or None,
        author_id=user_id,
        status=data.get('status', '1')
    )
    dto.create_by_user(str(user_id))
    BlogArticleService.insert_article(dto)
    return AjaxResponse.from_success(msg="文章发布成功")


@reg.api.route("/front/user/article/<int:article_id>", methods=["PUT"])
@JsonSerializer()
def front_user_article_update(article_id: int):
    """前台用户编辑文章"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    old = BlogArticleMapper.select_article_by_id(article_id)
    if not old or old.author_id != user_id:
        return AjaxResponse.from_error(msg="只能修改自己的文章")
    data = request.get_json() or {}
    from owl_blog.utils import sanitize_html
    dto = BlogArticle(
        article_id=article_id,
        title=data.get('title', '').strip(),
        content=sanitize_html(data.get('content', '')),
        summary=data.get('summary', '').strip() or None,
        cover_image=data.get('coverImage') or None,
        category_id=data.get('categoryId') or None,
        status=data.get('status', '1')
    )
    dto.update_by_user(str(user_id))
    BlogArticleService.update_article(dto)
    return AjaxResponse.from_success(msg="文章更新成功")


@reg.api.route("/front/user/article/<int:article_id>", methods=["DELETE"])
@JsonSerializer()
def front_user_article_delete(article_id: int):
    """前台用户删除文章"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    old = BlogArticleMapper.select_article_by_id(article_id)
    if not old or old.author_id != user_id:
        return AjaxResponse.from_error(msg="只能删除自己的文章")
    BlogArticleMapper.delete_article_by_id(article_id)
    return AjaxResponse.from_success(msg="文章已删除")


# ==================== 前台评论管理 ====================

@reg.api.route("/front/user/comment/<int:comment_id>/status", methods=["PUT"])
@JsonSerializer()
def front_user_comment_update_status(comment_id: int):
    """前台作者审核/驳回自己文章下的评论"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    comment = BlogCommentMapper.select_comment_by_id(comment_id)
    if not comment:
        from owl_common.exception import NotFoundException
        raise NotFoundException("评论不存在")
    article = BlogArticleMapper.select_article_by_id(comment.article_id)
    if not article or article.author_id != user_id:
        return AjaxResponse.from_error(msg="只能管理自己文章下的评论")
    data = request.get_json() or {}
    new_status = str(data.get('status', '1'))
    BlogCommentService.update_comment_status(comment_id, new_status)
    return AjaxResponse.from_success(msg="评论状态已更新")


@reg.api.route("/front/user/comment/<int:comment_id>", methods=["DELETE"])
@JsonSerializer()
def front_user_comment_delete(comment_id: int):
    """前台删除评论：作者删自己文章下的，或用户删自己发的"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    comment = BlogCommentMapper.select_comment_by_id(comment_id)
    if not comment:
        from owl_common.exception import NotFoundException
        raise NotFoundException("评论不存在")
    if comment.user_id == user_id:
        BlogCommentService.delete_comment_by_id(comment_id)
        return AjaxResponse.from_success(msg="评论已删除")
    article = BlogArticleMapper.select_article_by_id(comment.article_id)
    if article and article.author_id == user_id:
        BlogCommentService.delete_comment_by_id(comment_id)
        return AjaxResponse.from_success(msg="评论已删除")
    return AjaxResponse.from_error(msg="无权删除此评论")

@reg.api.route("/front/article/<int:id>/history", methods=["POST"])
@JsonSerializer()
def front_article_record_history(id: int):
    """记录浏览历史（登录用户打开文章详情时调用）"""
    user_id = None
    try: user_id = SecurityUtil.get_user_id()
    except Exception: pass
    if user_id:
        BlogViewHistoryMapper.add_history(user_id, id)
    return AjaxResponse.from_success()


# ==================== 友链接口 ====================

from owl_blog.domain.po import BlogFriendLinkPo

@reg.api.route("/front/friend-links", methods=["GET"])
@JsonSerializer()
def front_friend_links():
    """前台公开友链列表"""
    stmt = select(BlogFriendLinkPo).where(BlogFriendLinkPo.status == '1').order_by(BlogFriendLinkPo.order_num)
    rows = db.session.execute(stmt).scalars().all()
    result = [{"linkId": r.link_id, "linkName": r.link_name, "linkUrl": r.link_url, "linkDesc": r.link_desc or ''} for r in rows]
    return AjaxResponse.from_success(data=result)


# ==================== 站点公告 ====================

from owl_system.service import SysNoticeService

@reg.api.route("/front/notice", methods=["GET"])
@JsonSerializer()
def front_notice():
    """前台公告列表（仅公告类型 notice_type='2'）"""
    from owl_system.domain.po import SysNoticePo
    stmt = select(SysNoticePo).where(
        SysNoticePo.status == '0',
        SysNoticePo.notice_type == '2'
    ).order_by(SysNoticePo.create_time.desc())
    rows = db.session.execute(stmt).scalars().all()
    result = [{
        "noticeId": r.notice_id,
        "noticeTitle": r.notice_title or '',
        "noticeContent": r.notice_content or '',
        "createTime": str(r.create_time) if r.create_time else ''
    } for r in rows]
    return AjaxResponse.from_success(data=result)


# ==================== 站内通知接口 ====================

from owl_blog.mapper.notice import BlogNoticeMapper

@reg.api.route("/front/user/notices", methods=["GET"])
@JsonSerializer()
def front_user_notices():
    """获取我的通知列表（分页）"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 10), 50)
    items, total = BlogNoticeMapper.get_user_notices(user_id, page_num, page_size)
    return TableResponse(rows=items, total=total)


@reg.api.route("/front/user/notices/unread-count", methods=["GET"])
@JsonSerializer()
def front_user_notices_unread():
    """未读通知数量（未登录返回0）"""
    try:
        user_id = SecurityUtil.get_user_id()
    except Exception:
        return AjaxResponse.from_success(data={"count": 0})
    if not user_id:
        return AjaxResponse.from_success(data={"count": 0})
    count = BlogNoticeMapper.get_unread_count(user_id)
    return AjaxResponse.from_success(data={"count": count})


@reg.api.route("/front/user/notice/<int:notice_id>/read", methods=["PUT"])
@JsonSerializer()
def front_user_notice_read(notice_id: int):
    """标记单条通知已读"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    BlogNoticeMapper.mark_as_read(notice_id, user_id)
    return AjaxResponse.from_success(msg="已读")


@reg.api.route("/front/user/notices/read-all", methods=["POST"])
@JsonSerializer()
def front_user_notices_read_all():
    """一键全部已读"""
    user_id = SecurityUtil.get_user_id()
    if not user_id:
        from owl_common.exception import UnauthorizedException
        raise UnauthorizedException("请先登录")
    BlogNoticeMapper.mark_all_read(user_id)
    return AjaxResponse.from_success(msg="已全部标记为已读")
