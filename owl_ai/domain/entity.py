# -*- coding: utf-8 -*-
"""
AI 对话记忆模块 — Pydantic 实体模型。

使用 Pydantic V2 对会话与消息进行入参校验，
role 字段限定为 user/assistant/system，消息按 seq 保证时序。
"""

from datetime import datetime
from typing import List, Optional, Literal
from typing_extensions import Annotated
from pydantic import BaseModel, Field, field_validator


class AiSession(BaseModel):
    """AI 对话会话"""
    session_id: Optional[int] = Field(default=None, description='会话ID')
    user_id: int = Field(..., description='用户ID')
    title: Optional[str] = Field(default=None, max_length=200, description='会话标题')
    model: str = Field(default='deepseek-chat', description='AI 模型名称')
    message_count: int = Field(default=0, ge=0, description='消息总数')
    total_tokens: int = Field(default=0, ge=0, description='累计 token 数')
    summary_content: Optional[str] = Field(default=None, description='远期消息压缩摘要')
    status: Literal['0', '1'] = Field(default='1', description='状态：1=活跃 0=归档')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

    @field_validator('title')
    @classmethod
    def trim_title(cls, v: str) -> str:
        if v:
            return v[:200]
        return v


class AiMessage(BaseModel):
    """AI 对话消息"""
    message_id: Optional[int] = Field(default=None, description='消息ID')
    session_id: int = Field(..., description='会话ID')
    seq: int = Field(..., ge=0, description='消息序号')
    role: Literal['user', 'assistant', 'system'] = Field(..., description='角色')
    content: str = Field(..., min_length=1, description='消息内容')
    token_count: int = Field(default=0, ge=0, description='token 估算数')
    is_compressed: Literal['0', '1'] = Field(default='0', description='是否已压缩')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class ChatRequest(BaseModel):
    """用户发送的聊天请求"""
    session_id: Optional[int] = Field(default=None, description='会话ID（新会话可不传）')
    message: str = Field(..., min_length=1, max_length=10000, description='用户消息')
    model: str = Field(default='deepseek-chat', description='模型名称')


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: int = Field(..., description='会话ID')
    message: str = Field(..., description='AI 回复内容')
    tokens_used: int = Field(default=0, description='本次消耗 token 数')


class SessionListItem(BaseModel):
    """会话列表项（精简信息）"""
    session_id: int
    title: Optional[str] = None
    model: str
    message_count: int
    create_time: Optional[datetime] = None


class MessageHistoryItem(BaseModel):
    """消息历史项"""
    message_id: int
    seq: int
    role: str
    content: str
    token_count: int
    create_time: Optional[datetime] = None