# -*- coding: utf-8 -*-

from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update, or_

from owl_blog.domain.entity import BlogComment
from owl_blog.domain.po import BlogCommentPo, BlogArticlePo
from owl_admin.ext import db


class BlogCommentMapper:
    
    @classmethod
    def select_comment_by_id(cls, id: int) -> Optional[BlogComment]:
        stmt = select(BlogCommentPo).where(BlogCommentPo.comment_id == id)
        row = db.session.execute(stmt).scalar_one_or_none()
        if row:
            return BlogComment(**{
                c.name: getattr(row, c.name)
                for c in row.__table__.columns
            })
        return None
    
    @classmethod
    def _build_criterions(cls, article_ids: Optional[List[int]] = None,
                         content: Optional[str] = None,
                         status: Optional[str] = None) -> list:
        criterions = []
        if content:
            criterions.append(BlogCommentPo.content.like(f'%{content}%'))
        if status:
            criterions.append(BlogCommentPo.status == status)
        if article_ids is not None:
            criterions.append(BlogCommentPo.article_id.in_(article_ids))
        return criterions
    
    @classmethod
    def _rows_to_list(cls, rows) -> List[BlogComment]:
        """将查询结果转换为BlogComment列表"""
        result = []
        for r in rows:
            comment = BlogComment(**{c.name: getattr(r, c.name) for c in r.__table__.columns})
            result.append(comment)
        return result
    
    @classmethod
    def select_comments_by_article_ids(cls, article_ids: List[int],
                                      content: Optional[str] = None,
                                      status: Optional[str] = None) -> List[BlogComment]:
        """按文章ID列表查询评论（带内容/状态过滤）"""
        if not article_ids:
            return []
        stmt = select(BlogCommentPo)
        criterions = cls._build_criterions(article_ids=article_ids, content=content, status=status)
        if criterions:
            stmt = stmt.where(*criterions)
        stmt = stmt.order_by(BlogCommentPo.create_time.desc())
        
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).scalars().all()
        return cls._rows_to_list(rows)
    
    @classmethod
    def select_comment_page(cls, article_ids: Optional[List[int]] = None,
                           content: Optional[str] = None,
                           status: Optional[str] = None) -> List[BlogComment]:
        """后台评论分页查询（联表查询文章标题）"""
        stmt = select(
            BlogCommentPo,
            BlogArticlePo.title.label('article_title')
        ).outerjoin(
            BlogArticlePo, BlogCommentPo.article_id == BlogArticlePo.article_id
        )
        criterions = cls._build_criterions(article_ids=article_ids, content=content, status=status)
        if criterions:
            stmt = stmt.where(*criterions)
        stmt = stmt.order_by(BlogCommentPo.create_time.desc())
        
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        result = []
        for r in rows:
            comment_po = r[0]
            comment = BlogComment(**{c.name: getattr(comment_po, c.name) for c in comment_po.__table__.columns})
            comment.article_title = r[1] or ''
            result.append(comment)
        return result
    
    @classmethod
    def select_comments_by_article(cls, article_id: int) -> List[BlogComment]:
        """查询文章的所有评论（前台用，只返回已通过的）"""
        stmt = select(BlogCommentPo) \
            .where(BlogCommentPo.article_id == article_id) \
            .where(BlogCommentPo.status == "1") \
            .order_by(BlogCommentPo.create_time)
        rows = db.session.execute(stmt).scalars().all()
        return cls._rows_to_list(rows)
    
    @classmethod
    def insert_comment(cls, comment: BlogComment) -> int:
        fields = {
            "article_id", "parent_id", "content",
            "author_name", "author_email", "user_id", "status",
            "create_time"
        }
        data = {k: getattr(comment, k) for k in fields if getattr(comment, k, None) is not None}
        stmt = insert(BlogCommentPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
    
    @classmethod
    def update_comment_status(cls, comment_id: int, status: str) -> int:
        stmt = update(BlogCommentPo) \
            .where(BlogCommentPo.comment_id == comment_id) \
            .values(status=status)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_comment_by_id(cls, id: int) -> int:
        stmt = delete(BlogCommentPo).where(BlogCommentPo.comment_id == id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_comments_by_article(cls, article_id: int) -> int:
        stmt = delete(BlogCommentPo).where(
            BlogCommentPo.article_id == article_id
        )
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def count_all(cls) -> int:
        """查询评论总数"""
        from sqlalchemy import func
        stmt = select(func.count(BlogCommentPo.comment_id))
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def select_comment_list_by_user(cls, user_id: int, page_num: int = 1, page_size: int = 10, keyword: str = None) -> list:
        """分页查询当前用户发表的评论（联查文章标题），返回驼峰字段名"""
        stmt = select(
            BlogCommentPo,
            BlogArticlePo.title.label('article_title')
        ).outerjoin(
            BlogArticlePo, BlogCommentPo.article_id == BlogArticlePo.article_id
        ).where(
            BlogCommentPo.user_id == user_id
        )
        if keyword:
            stmt = stmt.where(BlogCommentPo.content.like(f'%{keyword}%'))
        stmt = stmt.order_by(BlogCommentPo.create_time.desc())
        rows = db.session.execute(
            stmt.limit(page_size).offset((page_num - 1) * page_size)
        ).all()
        result = []
        for r in rows:
            po = r[0]
            d = {
                'commentId': po.comment_id,
                'articleId': po.article_id,
                'parentId': po.parent_id,
                'content': po.content,
                'authorName': po.author_name,
                'authorEmail': po.author_email,
                'userId': po.user_id,
                'status': po.status,
                'createTime': str(po.create_time) if po.create_time else '',
                'updateTime': str(po.update_time) if po.update_time else '',
                'articleTitle': r[1] or ''
            }
            result.append(d)
        return result

    @classmethod
    def count_by_user(cls, user_id: int) -> int:
        """统计用户评论总数"""
        from sqlalchemy import func
        stmt = select(func.count(BlogCommentPo.comment_id)).where(
            BlogCommentPo.user_id == user_id
        )
        return db.session.execute(stmt).scalar() or 0