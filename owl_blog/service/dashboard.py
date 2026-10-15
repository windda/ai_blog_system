# -*- coding: utf-8 -*-

"""
仪表盘服务层。

使用 SQL 聚合查询统计关键指标，按日分组统计文章发布趋势，
最新评论动态使用联表查询，文章列表分页返回。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select, func, text
from owl_blog.domain.entity import BlogArticle
from owl_blog.domain.po import BlogArticlePo, BlogCategoryPo, BlogTagPo, BlogCommentPo
from owl_system.domain.po import SysUserPo
from owl_admin.ext import db


class DashboardService:
    """仪表盘数据聚合服务"""

    @classmethod
    def get_statistics(cls, user_id: Optional[int] = None) -> Dict:
        """
        获取统计卡片数据（全部使用COUNT聚合查询）
        
        数据隔离：
        - user_id=None（管理员）：看全局数据
        - user_id 不为空（普通用户）：只看自己文章的数据

        Returns:
            Dict: {
                "totalArticles": int,
                "totalComments": int,
                "totalCategories": int,
                "totalTags": int,
                "todayViews": int,
                "pendingComments": int
            }
        """
        stats = {}

        # 1. 已发布文章数
        article_base = select(func.count(BlogArticlePo.article_id)).where(BlogArticlePo.status == '1')
        if user_id:
            article_base = article_base.where(BlogArticlePo.author_id == user_id)
        stats["totalArticles"] = db.session.execute(article_base).scalar() or 0

        # 2. 评论总数
        comment_base = select(func.count(BlogCommentPo.comment_id))
        if user_id:
            # 普通用户：只看自己文章的评论
            own_article_ids = db.session.execute(
                select(BlogArticlePo.article_id).where(BlogArticlePo.author_id == user_id)
            ).scalars().all()
            if own_article_ids:
                comment_base = comment_base.where(BlogCommentPo.article_id.in_(own_article_ids))
            else:
                comment_base = comment_base.where(BlogCommentPo.comment_id < 0)  # 无文章则显示0
        stats["totalComments"] = db.session.execute(comment_base).scalar() or 0

        # 3. 分类数
        stats["totalCategories"] = db.session.execute(
            select(func.count(BlogCategoryPo.category_id))
        ).scalar() or 0

        # 4. 标签数
        stats["totalTags"] = db.session.execute(
            select(func.count(BlogTagPo.tag_id))
        ).scalar() or 0

        # 5. 总浏览量
        view_base = select(func.coalesce(func.sum(BlogArticlePo.view_count), 0)).where(BlogArticlePo.status == '1')
        if user_id:
            view_base = view_base.where(BlogArticlePo.author_id == user_id)
        stats["todayViews"] = db.session.execute(view_base).scalar() or 0

        # 6. 待审核评论
        pending_base = select(func.count(BlogCommentPo.comment_id)).where(BlogCommentPo.status == '0')
        if user_id:
            if own_article_ids:
                pending_base = pending_base.where(BlogCommentPo.article_id.in_(own_article_ids))
            else:
                pending_base = pending_base.where(BlogCommentPo.comment_id < 0)
        stats["pendingComments"] = db.session.execute(pending_base).scalar() or 0

        return stats

    @classmethod
    def get_article_trend(cls, days: int = 7) -> List[Dict]:
        """
        获取文章发布趋势（近N天每日发布量）。

        使用 DATE_FORMAT 按天分组聚合，保证 MySQL 兼容性。

        Args:
            days: 近几天，默认7

        Returns:
            List[Dict]: [{"date": "2024-01-01", "count": 3}, ...]
        """
        start_date = datetime.now() - timedelta(days=days - 1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # 按天分组统计文章发布数
        # 按天分组的日期表达式：SQLite 用 strftime，MySQL 用 date_format（双兼容）
        if db.engine.dialect.name == 'sqlite':
            date_expr = func.strftime('%Y-%m-%d', BlogArticlePo.create_time)
        else:
            date_expr = func.date_format(BlogArticlePo.create_time, '%Y-%m-%d')

        rows = db.session.execute(
            select(
                date_expr.label('date'),
                func.count(BlogArticlePo.article_id).label('count')
            )
            .where(BlogArticlePo.create_time >= start_date)
            .where(BlogArticlePo.status == '1')
            .group_by(date_expr)
            .order_by(date_expr)
        ).all()

        # 填充空白日期（没有发布的日期补0）
        trend_map = {row.date: row.count for row in rows}
        result = []
        for i in range(days):
            day = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            result.append({
                "date": day,
                "count": trend_map.get(day, 0)
            })
        return result

    @classmethod
    def get_recent_comments(cls, limit: int = 5, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取最新评论动态（联表查询文章标题和用户昵称）

        数据隔离：
        - user_id=None（管理员）：看全部最新评论
        - user_id 不为空（普通用户）：只看自己文章的评论

        Args:
            limit: 返回条数，默认5
            user_id: 用户ID（可选，用于数据隔离）

        Returns:
            List[Dict]: [{
                "commentId": int,
                "content": str,
                "authorName": str,
                "articleId": int,
                "articleTitle": str,
                "status": str,
                "createTime": datetime
            }, ...]
        """
        base = select(
            BlogCommentPo.comment_id,
            BlogCommentPo.content,
            BlogCommentPo.author_name,
            BlogCommentPo.article_id,
            BlogArticlePo.title.label('article_title'),
            BlogCommentPo.status,
            BlogCommentPo.create_time
        ).outerjoin(
            BlogArticlePo,
            BlogCommentPo.article_id == BlogArticlePo.article_id
        )

        if user_id:
            # 普通用户：只看自己文章的评论
            own_article_ids = db.session.execute(
                select(BlogArticlePo.article_id).where(BlogArticlePo.author_id == user_id)
            ).scalars().all()
            if own_article_ids:
                base = base.where(BlogCommentPo.article_id.in_(own_article_ids))
            else:
                # 没有文章，返回空结果
                return []

        rows = db.session.execute(
            base.order_by(BlogCommentPo.create_time.desc()).limit(limit)
        ).all()

        return [
            {
                "commentId": r.comment_id,
                "content": r.content[:50] + ('...' if len(r.content or '') > 50 else ''),
                "authorName": r.author_name,
                "articleId": r.article_id,
                "articleTitle": r.article_title or '（已删除）',
                "status": r.status,
                "createTime": r.create_time.strftime('%Y-%m-%d %H:%M') if r.create_time else ''
            }
            for r in rows
        ]

    @classmethod
    def get_latest_articles(cls, page_num: int = 1, page_size: int = 5,
                            category_id: Optional[int] = None) -> List[BlogArticle]:
        """
        获取最新文章列表（分页）。

        支持分页查询、条件过滤，并联表查询分类名和作者名。

        Args:
            page_num: 页码
            page_size: 每页条数
            category_id: 分类筛选（可选）

        Returns:
            List[BlogArticle]: 文章列表（不含content字段，减少传输量）
        """
        base_columns = [
            BlogArticlePo.article_id,
            BlogArticlePo.title,
            BlogArticlePo.summary,
            BlogArticlePo.cover_image,
            BlogArticlePo.category_id,
            BlogArticlePo.author_id,
            BlogArticlePo.status,
            BlogArticlePo.is_top,
            BlogArticlePo.view_count,
            BlogArticlePo.like_count,
            BlogArticlePo.create_time,
            BlogArticlePo.update_time,
        ]

        stmt = select(
            *base_columns,
            BlogCategoryPo.category_name,
            SysUserPo.nick_name,
        ).outerjoin(
            BlogCategoryPo, BlogArticlePo.category_id == BlogCategoryPo.category_id
        ).outerjoin(
            SysUserPo, BlogArticlePo.author_id == SysUserPo.user_id
        ).where(
            BlogArticlePo.status == '1'
        )

        if category_id:
            stmt = stmt.where(BlogArticlePo.category_id == category_id)

        stmt = stmt.order_by(
            BlogArticlePo.is_top.desc(),
            BlogArticlePo.create_time.desc()
        )

        # 分页
        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        rows = db.session.execute(stmt).all()
        articles = []
        for row in rows:
            article = BlogArticle(
                article_id=row.article_id,
                title=row.title,
                summary=row.summary,
                cover_image=row.cover_image,
                category_id=row.category_id,
                author_id=row.author_id,
                status=row.status,
                is_top=row.is_top,
                view_count=row.view_count,
                like_count=row.like_count,
                create_time=row.create_time,
                update_time=row.update_time,
                category_name=row.category_name,
                author_name=row.nick_name,
            )
            articles.append(article)
        return articles

    @classmethod
    def count_articles(cls, category_id: Optional[int] = None) -> int:
        """获取文章总数（支持按分类筛选）"""
        stmt = select(func.count(BlogArticlePo.article_id)).where(
            BlogArticlePo.status == '1'
        )
        if category_id:
            stmt = stmt.where(BlogArticlePo.category_id == category_id)
        return db.session.execute(stmt).scalar() or 0