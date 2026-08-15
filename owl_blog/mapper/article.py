# -*- coding: utf-8 -*-

from types import NoneType
from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update, func, text

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_blog.domain.entity import BlogArticle, BlogTag
from owl_blog.domain.po import BlogArticlePo, BlogCategoryPo, BlogTagPo, BlogArticleTagPo
from owl_system.domain.po import SysUserPo
from owl_admin.ext import db


class BlogArticleMapper:
    
    article_fields = {
        "article_id", "title", "content", "summary", "cover_image", "category_id", "author_id",
        "status", "is_top", "view_count", "like_count",
        "create_time", "update_time", "create_by", "update_by", "remark"
    }
    
    article_columns = ColumnEntityList(BlogArticlePo, article_fields, False)
    
    @classmethod
    def select_article_by_id(cls, id: int) -> Optional[BlogArticle]:
        """查询文章详情，连带分类名称和作者昵称"""
        stmt = select(
            *cls.article_columns,
            BlogCategoryPo.category_name,
            SysUserPo.nick_name,
        ).outerjoin(
            BlogCategoryPo, BlogArticlePo.category_id == BlogCategoryPo.category_id
        ).outerjoin(
            SysUserPo, BlogArticlePo.author_id == SysUserPo.user_id
        ).where(
            BlogArticlePo.article_id == id
        )
        row = db.session.execute(stmt).one_or_none()
        if not row:
            return None
        
        article = cls.article_columns.cast(row, BlogArticle)
        article.category_name = row.category_name
        article.author_name = row.nick_name
        
        # 查询标签
        tag_stmt = select(BlogTagPo.tag_id, BlogTagPo.tag_name, BlogTagPo.order_num) \
            .join(BlogArticleTagPo, BlogTagPo.tag_id == BlogArticleTagPo.tag_id) \
            .where(BlogArticleTagPo.article_id == id)
        tag_rows = db.session.execute(tag_stmt).all()
        article.tags = [
            BlogTag(tag_id=r.tag_id, tag_name=r.tag_name, order_num=r.order_num)
            for r in tag_rows
        ]
        return article
    
    @classmethod
    def select_article_list(cls, article: BlogArticle | NoneType) -> List[BlogArticle]:
        """查询文章列表"""
        stmt = select(
            *cls.article_columns,
            BlogCategoryPo.category_name,
            SysUserPo.nick_name,
        ).outerjoin(
            BlogCategoryPo, BlogArticlePo.category_id == BlogCategoryPo.category_id
        ).outerjoin(
            SysUserPo, BlogArticlePo.author_id == SysUserPo.user_id
        )
        
        if article is not None:
            from sqlalchemy import or_, and_
            
            criterions = []
            search_keywords = []  # 搜索关键词列表
            
            if article.title:
                # 按空格分词，多个关键词任意匹配
                raw_keyword = article.title.strip()
                search_keywords = [kw.strip() for kw in raw_keyword.split() if kw.strip()]
            
            # 搜索条件：title OR summary OR content 匹配任一关键词
            if search_keywords:
                search_conditions = []
                for kw in search_keywords:
                    # SQLAlchemy 参数化查询自动防注入
                    word_condition = or_(
                        BlogArticlePo.title.like(f'%{kw}%'),
                        BlogArticlePo.summary.like(f'%{kw}%'),
                        BlogArticlePo.content.like(f'%{kw}%')
                    )
                    search_conditions.append(word_condition)
                # 所有关键词必须同时匹配（AND 关系）
                criterions.append(and_(*search_conditions))
            
            if article.status:
                criterions.append(BlogArticlePo.status == article.status)
            if article.category_id:
                criterions.append(BlogArticlePo.category_id == article.category_id)
            if article.author_id:
                criterions.append(BlogArticlePo.author_id == article.author_id)
            
            stmt = stmt.where(*criterions)
        
        stmt = stmt.order_by(BlogArticlePo.is_top.desc(), BlogArticlePo.create_time.desc())
        
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        articles = []
        for row in rows:
            a = cls.article_columns.cast(row, BlogArticle)
            a.category_name = row.category_name
            a.author_name = row.nick_name
            articles.append(a)
        return articles
    
    @classmethod
    def insert_article(cls, article: BlogArticle) -> int:
        fields = {
            "title", "content", "summary", "cover_image", "category_id", "author_id",
            "status", "is_top", "view_count", "like_count",
            "create_by", "create_time", "remark"
        }
        data = article.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = insert(BlogArticlePo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
    
    @classmethod
    def update_article(cls, article: BlogArticle) -> int:
        fields = {
            "title", "content", "summary", "cover_image", "category_id", "author_id",
            "status", "is_top",
            "update_by", "update_time", "remark"
        }
        data = article.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = update(BlogArticlePo) \
            .where(BlogArticlePo.article_id == article.article_id) \
            .values(data)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_article_by_id(cls, id: int) -> int:
        stmt = delete(BlogArticlePo).where(BlogArticlePo.article_id == id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_article_by_ids(cls, ids: List[int]) -> int:
        stmt = delete(BlogArticlePo).where(BlogArticlePo.article_id.in_(ids))
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def insert_article_tags(cls, article_id: int, tag_ids: List[int]):
        """插入文章标签关联"""
        if not tag_ids:
            return
        stmt = insert(BlogArticleTagPo).values([
            {"article_id": article_id, "tag_id": tid}
            for tid in tag_ids
        ])
        db.session.execute(stmt)
    
    @classmethod
    def delete_article_tags(cls, article_id: int):
        """删除文章的所有标签关联"""
        stmt = delete(BlogArticleTagPo).where(
            BlogArticleTagPo.article_id == article_id
        )
        db.session.execute(stmt)
    
    @classmethod
    def increment_view_count(cls, article_id: int):
        """增加浏览次数"""
        stmt = update(BlogArticlePo) \
            .where(BlogArticlePo.article_id == article_id) \
            .values(view_count=BlogArticlePo.view_count + 1)
        db.session.execute(stmt)

    @classmethod
    def increment_like_count(cls, article_id: int):
        """增加点赞次数（持久化到 MySQL）"""
        stmt = update(BlogArticlePo) \
            .where(BlogArticlePo.article_id == article_id) \
            .values(like_count=BlogArticlePo.like_count + 1)
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def decrement_like_count(cls, article_id: int):
        """减少点赞次数（持久化到 MySQL），不低于 0"""
        stmt = update(BlogArticlePo) \
            .where(BlogArticlePo.article_id == article_id) \
            .where(BlogArticlePo.like_count > 0) \
            .values(like_count=BlogArticlePo.like_count - 1)
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def select_article_ids_by_author(cls, author_id: int) -> List[int]:
        """查询某个作者的所有文章ID"""
        stmt = select(BlogArticlePo.article_id).where(
            BlogArticlePo.author_id == author_id
        )
        rows = db.session.execute(stmt).scalars().all()
        return list(rows)


# ==================== 点赞记录 Mapper ====================

from owl_blog.domain.po import BlogArticleLikePo

class BlogArticleLikeMapper:

    @classmethod
    def insert_like(cls, article_id: int, user_id: int) -> bool:
        """插入点赞记录，重复返回False"""
        try:
            stmt = insert(BlogArticleLikePo).values(
                article_id=article_id, user_id=user_id
            )
            db.session.execute(stmt)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @classmethod
    def delete_like(cls, article_id: int, user_id: int) -> int:
        """取消点赞，返回删除行数"""
        stmt = delete(BlogArticleLikePo).where(
            BlogArticleLikePo.article_id == article_id,
            BlogArticleLikePo.user_id == user_id
        )
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount

    @classmethod
    def has_liked(cls, article_id: int, user_id: int) -> bool:
        """检查用户是否已点赞"""
        stmt = select(BlogArticleLikePo.id).where(
            BlogArticleLikePo.article_id == article_id,
            BlogArticleLikePo.user_id == user_id
        ).limit(1)
        return db.session.execute(stmt).scalar() is not None

    @classmethod
    def get_like_users(cls, article_id: int) -> list:
        """获取点赞用户列表（含昵称）"""
        stmt = select(
            BlogArticleLikePo.user_id,
            SysUserPo.nick_name,
            BlogArticleLikePo.create_time
        ).join(
            SysUserPo, BlogArticleLikePo.user_id == SysUserPo.user_id
        ).where(
            BlogArticleLikePo.article_id == article_id
        ).order_by(BlogArticleLikePo.create_time.desc())
        rows = db.session.execute(stmt).all()
        return [
            {"userId": r.user_id, "nickName": r.nick_name or "", "createTime": str(r.create_time)}
            for r in rows
        ]


# ==================== 收藏/浏览历史 Mapper ====================

from owl_blog.domain.po import BlogArticleCollectPo, BlogViewHistoryPo

class BlogArticleCollectMapper:

    @classmethod
    def toggle_collect(cls, article_id: int, user_id: int) -> bool:
        """切换收藏状态，返回True=已收藏 False=已取消"""
        existing = db.session.execute(
            select(BlogArticleCollectPo.id).where(
                BlogArticleCollectPo.article_id == article_id,
                BlogArticleCollectPo.user_id == user_id
            ).limit(1)
        ).scalar()
        if existing:
            db.session.execute(delete(BlogArticleCollectPo).where(
                BlogArticleCollectPo.article_id == article_id,
                BlogArticleCollectPo.user_id == user_id
            ))
            db.session.commit()
            return False
        else:
            db.session.execute(insert(BlogArticleCollectPo).values(
                article_id=article_id, user_id=user_id
            ))
            db.session.commit()
            return True

    @classmethod
    def is_collected(cls, article_id: int, user_id: int) -> bool:
        stmt = select(BlogArticleCollectPo.id).where(
            BlogArticleCollectPo.article_id == article_id,
            BlogArticleCollectPo.user_id == user_id
        ).limit(1)
        return db.session.execute(stmt).scalar() is not None

    @classmethod
    def get_user_collections(cls, user_id: int, page_num: int = 1, page_size: int = 10, keyword: str = None) -> tuple:
        stmt = select(
            BlogArticleCollectPo.article_id, BlogArticleCollectPo.create_time,
            BlogArticlePo.title, BlogArticlePo.summary, BlogArticlePo.view_count
        ).join(
            BlogArticlePo, BlogArticleCollectPo.article_id == BlogArticlePo.article_id
        ).where(
            BlogArticleCollectPo.user_id == user_id,
            BlogArticlePo.status == '1'
        )
        if keyword:
            stmt = stmt.where(BlogArticlePo.title.like(f'%{keyword}%'))
        stmt = stmt.order_by(BlogArticleCollectPo.create_time.desc())
        total = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar() or 0
        rows = db.session.execute(
            stmt.limit(page_size).offset((page_num - 1) * page_size)
        ).all()
        items = [
            {"articleId": r.article_id, "title": r.title, "summary": r.summary or "",
             "viewCount": r.view_count or 0, "createTime": str(r.create_time)}
            for r in rows
        ]
        return items, total

class BlogViewHistoryMapper:

    @classmethod
    def add_history(cls, user_id: int, article_id: int):
        """记录浏览历史，5分钟内不重复"""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        recent = db.session.execute(
            select(BlogViewHistoryPo.id).where(
                BlogViewHistoryPo.user_id == user_id,
                BlogViewHistoryPo.article_id == article_id,
                BlogViewHistoryPo.create_time >= cutoff
            ).limit(1)
        ).scalar()
        if not recent:
            db.session.execute(insert(BlogViewHistoryPo).values(
                user_id=user_id, article_id=article_id
            ))
            db.session.commit()

    @classmethod
    def get_user_history(cls, user_id: int, page_num: int = 1, page_size: int = 10, keyword: str = None) -> tuple:
        stmt = select(
            BlogViewHistoryPo.article_id, BlogViewHistoryPo.create_time,
            BlogArticlePo.title, BlogArticlePo.summary, BlogArticlePo.view_count
        ).join(
            BlogArticlePo, BlogViewHistoryPo.article_id == BlogArticlePo.article_id
        ).where(
            BlogViewHistoryPo.user_id == user_id,
            BlogArticlePo.status == '1'
        )
        if keyword:
            stmt = stmt.where(BlogArticlePo.title.like(f'%{keyword}%'))
        stmt = stmt.order_by(BlogViewHistoryPo.create_time.desc())
        total = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar() or 0
        rows = db.session.execute(
            stmt.limit(page_size).offset((page_num - 1) * page_size)
        ).all()
        items = [
            {"articleId": r.article_id, "title": r.title, "summary": r.summary or "",
             "viewCount": r.view_count or 0, "createTime": str(r.create_time)}
            for r in rows
        ]
        return items, total

    @classmethod
    def clear_history(cls, user_id: int):
        db.session.execute(delete(BlogViewHistoryPo).where(
            BlogViewHistoryPo.user_id == user_id
        ))
        db.session.commit()
