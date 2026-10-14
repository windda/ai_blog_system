# -*- coding: utf-8 -*-

from typing import Optional
from sqlalchemy import CHAR, DateTime, String, Text, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from owl_admin.ext import db


class BowlAiSession(db.Model):
    __tablename__ = 'bowl_ai_session'
    __table_args__ = {'comment': 'AI 对话会话表'}

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, comment='用户ID')
    title: Mapped[Optional[str]] = mapped_column(String(200), default='新对话', comment='会话标题')
    model: Mapped[Optional[str]] = mapped_column(String(50), default='deepseek-chat', comment='模型名称')
    message_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='消息数量')
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='累计Token数')
    summary_content: Mapped[Optional[str]] = mapped_column(Text, comment='远期摘要')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), default='1', comment='状态')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)


class BowlAiMessage(db.Model):
    __tablename__ = 'bowl_ai_message'
    __table_args__ = {'comment': 'AI 对话消息表'}

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, comment='会话ID')
    seq: Mapped[int] = mapped_column(Integer, default=0, comment='消息序号')
    role: Mapped[str] = mapped_column(String(20), comment='角色（user/assistant/system）')
    content: Mapped[Optional[str]] = mapped_column(Text, comment='消息内容')
    token_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='Token估算数')
    is_compressed: Mapped[Optional[str]] = mapped_column(CHAR(1), default='0', comment='是否已压缩')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class AiTokenRecordPo(db.Model):
    __tablename__ = 'ai_token_record'
    __table_args__ = {'comment': 'AI Token 消耗统计表'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, comment='用户ID')
    session_id: Mapped[Optional[int]] = mapped_column(Integer, comment='会话ID')
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='提示Token数')
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='回复Token数')
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='总Token数')
    model: Mapped[Optional[str]] = mapped_column(String(50), default='deepseek-chat', comment='模型名称')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))