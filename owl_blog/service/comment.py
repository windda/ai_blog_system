# -*- coding: utf-8 -*-

from typing import List, Optional
from flask import g

from owl_common.sqlalchemy.transaction import Transactional
from owl_blog.domain.entity import BlogComment
from owl_blog.mapper.comment import BlogCommentMapper
from owl_blog.mapper.article import BlogArticleMapper
from owl_admin.ext import db


class BlogCommentService:
    
    @classmethod
    def select_comment_by_id(cls, id: int) -> Optional[BlogComment]:
        return BlogCommentMapper.select_comment_by_id(id)
    
    @classmethod
    def select_comments_by_article(cls, article_id: int) -> List[BlogComment]:
        return BlogCommentMapper.select_comments_by_article(article_id)
    
    @classmethod
    def select_comment_page(cls, article_ids: Optional[List[int]] = None,
                           content: Optional[str] = None,
                           status: Optional[str] = None) -> List[BlogComment]:
        """分页查询评论，支持按文章ID列表、内容、状态过滤"""
        return BlogCommentMapper.select_comment_page(
            article_ids=article_ids,
            content=content,
            status=status
        )
    
    @classmethod
    def select_comments_by_article_ids(cls, article_ids: List[int],
                                      content: Optional[str] = None,
                                      status: Optional[str] = None) -> List[BlogComment]:
        return BlogCommentMapper.select_comments_by_article_ids(
            article_ids=article_ids,
            content=content,
            status=status
        )
    
    @classmethod
    @Transactional(db.session)
    def insert_comment(cls, body: BlogComment) -> bool:
        return BlogCommentMapper.insert_comment(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def update_comment_status(cls, comment_id: int, status: str) -> bool:
        return BlogCommentMapper.update_comment_status(comment_id, status) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_comment_by_id(cls, id: int) -> bool:
        return BlogCommentMapper.delete_comment_by_id(id) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_comments_by_article(cls, article_id: int) -> bool:
        return BlogCommentMapper.delete_comments_by_article(article_id) > 0
