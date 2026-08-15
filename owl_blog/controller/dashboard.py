# -*- coding: utf-8 -*-

"""
仪表盘控制器。

提供统计数据、文章发布趋势、最新评论动态等仪表盘接口，
文章列表支持分页与按分类筛选。
"""

from flask import request

from owl_common.base.model import AjaxResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_blog.service.dashboard import DashboardService
from owl_blog.utils import get_current_user, safe_int, is_admin
from owl_admin import reg


@reg.api.route("/blog/dashboard", methods=["GET"])
@JsonSerializer()
def blog_dashboard():
    """
    博客仪表盘数据

    返回聚合统计数据 + 最新文章列表（分页）+ 发布趋势 + 最新评论

    Query Parameters:
        pageNum (int): 页码，默认1
        pageSize (int): 每页条数，默认5
        categoryId (int): 分类筛选（可选）
    """
    current_user = get_current_user()
    user_id = None
    if not is_admin(current_user):
        user_id = getattr(current_user, 'user_id', None)

    # 参数解析
    page_num = safe_int(request.args.get('pageNum'), 1)
    page_size = min(safe_int(request.args.get('pageSize'), 5), 20)
    category_id = safe_int(request.args.get('categoryId'), None)

    # 1. 统计卡片数据（按角色隔离）
    statistics = DashboardService.get_statistics(user_id=user_id)

    # 2. 最新文章列表（分页，按分类筛选）
    articles = DashboardService.get_latest_articles(
        page_num=page_num,
        page_size=page_size,
        category_id=category_id
    )
    total = DashboardService.count_articles(category_id=category_id)

    # 3. 文章发布趋势（近7天）
    trend = DashboardService.get_article_trend(days=7)

    # 4. 最新评论动态（按角色隔离）
    recent_comments = DashboardService.get_recent_comments(limit=5, user_id=user_id)

    return AjaxResponse.from_success(data={
        # 统计卡片
        "totalArticles": statistics["totalArticles"],
        "totalComments": statistics["totalComments"],
        "totalCategories": statistics["totalCategories"],
        "totalTags": statistics["totalTags"],
        "todayViews": statistics["todayViews"],
        "pendingComments": statistics["pendingComments"],
        # 文章列表（分页）
        "articleList": articles,
        "total": total,
        # 趋势数据
        "trend": trend,
        # 最新动态
        "recentComments": recent_comments
    })
