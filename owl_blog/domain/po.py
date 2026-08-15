# -*- coding: utf-8 -*-

from typing import Optional
from sqlalchemy import CHAR, DateTime, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from owl_admin.ext import db


class BlogCategoryPo(db.Model):
    __tablename__ = 'blog_category'
    __table_args__ = {'comment': '博客分类表'}
    category_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    category_name: Mapped[str] = mapped_column(String(50))
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"))
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"))
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))


class BlogTagPo(db.Model):
    __tablename__ = 'blog_tag'
    __table_args__ = {'comment': '博客标签表'}
    tag_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    tag_name: Mapped[str] = mapped_column(String(50))
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"))
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))


class BlogArticlePo(db.Model):
    __tablename__ = 'blog_article'
    __table_args__ = {'comment': '博客文章表'}
    article_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(LONGTEXT)
    summary: Mapped[Optional[str]] = mapped_column(String(500))
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), server_default=text("''"))
    category_id: Mapped[Optional[int]] = mapped_column(BIGINT(20))
    author_id: Mapped[Optional[int]] = mapped_column(BIGINT(20))
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"))
    is_top: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'N'"))
    view_count: Mapped[Optional[int]] = mapped_column(INTEGER(11), server_default=text("'0'"))
    like_count: Mapped[Optional[int]] = mapped_column(INTEGER(11), server_default=text("'0'"))
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))


class BlogArticleTagPo(db.Model):
    __tablename__ = 'blog_article_tag'
    __table_args__ = {'comment': '博客文章标签关联表'}
    article_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    tag_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)


class BlogColumnPo(db.Model):
    __tablename__ = 'blog_column'
    __table_args__ = {'comment': '博客专栏表'}
    column_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    column_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), server_default=text("''"))
    author_id: Mapped[int] = mapped_column(BIGINT(20))
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"))
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"))
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"))
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))


class BlogArticleCollectPo(db.Model):
    __tablename__ = 'blog_article_collect'
    __table_args__ = {'comment': '文章收藏记录表'}
    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(BIGINT(20))
    user_id: Mapped[int] = mapped_column(BIGINT(20))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class BlogViewHistoryPo(db.Model):
    __tablename__ = 'blog_view_history'
    __table_args__ = {'comment': '用户浏览历史表'}
    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT(20))
    article_id: Mapped[int] = mapped_column(BIGINT(20))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class BlogArticleLikePo(db.Model):
    __tablename__ = 'blog_article_like'
    __table_args__ = {'comment': '文章点赞记录表'}
    id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(BIGINT(20))
    user_id: Mapped[int] = mapped_column(BIGINT(20))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class BlogFriendLinkPo(db.Model):
    __tablename__ = 'blog_friend_link'
    __table_args__ = {'comment': '友情链接表'}
    link_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, autoincrement=True)
    link_name: Mapped[str] = mapped_column(String(100))
    link_url: Mapped[str] = mapped_column(String(500))
    link_desc: Mapped[Optional[str]] = mapped_column(String(500), default='')
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), default=0)
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), default='1')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), default='')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_by: Mapped[Optional[str]] = mapped_column(String(64), default='')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))


class BlogNoticePo(db.Model):
    __tablename__ = 'blog_notice'
    __table_args__ = {'comment': '站内通知表'}
    notice_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, autoincrement=True)
    receive_user_id: Mapped[int] = mapped_column(BIGINT(20))
    article_id: Mapped[Optional[int]] = mapped_column(BIGINT(20))
    notice_type: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[Optional[str]] = mapped_column(CHAR(1), default='0')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class BlogCommentPo(db.Model):
    __tablename__ = 'blog_comment'
    __table_args__ = {'comment': '博客评论表'}
    comment_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True)
    article_id: Mapped[int] = mapped_column(BIGINT(20))
    parent_id: Mapped[Optional[int]] = mapped_column(BIGINT(20), server_default=text("'0'"))
    content: Mapped[Optional[str]] = mapped_column(Text)
    author_name: Mapped[Optional[str]] = mapped_column(String(50))
    author_email: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[int]] = mapped_column(BIGINT(20))
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"))
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)