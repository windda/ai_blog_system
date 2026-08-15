# -*- coding: utf-8 -*-

from typing import List
from sqlalchemy import select, insert, update, func

from owl_blog.domain.po import BlogNoticePo
from owl_admin.ext import db


class BlogNoticeMapper:

    @classmethod
    def insert_notice(cls, receive_user_id: int, article_id: int, notice_type: str, message: str):
        """插入通知"""
        stmt = insert(BlogNoticePo).values(
            receive_user_id=receive_user_id,
            article_id=article_id,
            notice_type=notice_type,
            message=message
        )
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def get_user_notices(cls, user_id: int, page_num: int = 1, page_size: int = 10) -> tuple:
        """分页获取用户通知列表"""
        stmt = select(BlogNoticePo).where(
            BlogNoticePo.receive_user_id == user_id
        ).order_by(BlogNoticePo.create_time.desc())
        total = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar() or 0
        rows = db.session.execute(
            stmt.limit(page_size).offset((page_num - 1) * page_size)
        ).scalars().all()
        items = [{
            "noticeId": r.notice_id,
            "articleId": r.article_id,
            "noticeType": r.notice_type,
            "message": r.message,
            "isRead": r.is_read == '1',
            "createTime": str(r.create_time) if r.create_time else ''
        } for r in rows]
        return items, total

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """未读通知数量"""
        stmt = select(func.count(BlogNoticePo.notice_id)).where(
            BlogNoticePo.receive_user_id == user_id,
            BlogNoticePo.is_read == '0'
        )
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def mark_as_read(cls, notice_id: int, user_id: int):
        """标记单条已读"""
        stmt = update(BlogNoticePo).where(
            BlogNoticePo.notice_id == notice_id,
            BlogNoticePo.receive_user_id == user_id
        ).values(is_read='1')
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def mark_all_read(cls, user_id: int):
        """一键全部已读"""
        stmt = update(BlogNoticePo).where(
            BlogNoticePo.receive_user_id == user_id,
            BlogNoticePo.is_read == '0'
        ).values(is_read='1')
        db.session.execute(stmt)
        db.session.commit()