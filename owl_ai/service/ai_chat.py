# -*- coding: utf-8 -*-
"""
AI 对话核心服务 — 多轮对话记忆管理与上下文组装。

负责会话的创建、消息持久化、上下文构建，
并保证每个用户只能访问自己的会话数据。
"""

import re
from datetime import datetime
from typing import List, Dict, Optional

from owl_ai.domain.po import BowlAiSession, BowlAiMessage
from owl_ai.domain.entity import AiSession, AiMessage
from owl_ai.mapper import AiSessionMapper, AiMessageMapper


MAX_MESSAGES_IN_CONTEXT = 20
MAX_SUMMARY_MESSAGES = 10


class AiChatService:

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return max(1, int(len(text) * 0.25))

    @classmethod
    def strip_html(cls, text: str) -> str:
        return re.sub(r'<[^>]+>', '', text) if text else text

    # ==================== Controller 调用的适配方法 ====================

    @classmethod
    def build_context(cls, user_id: int, session_id: Optional[int], msg: str) -> List[Dict]:
        """构建 API 调用上下文（Controller 层直接调用）"""
        session = cls.get_or_create_session(user_id, session_id)

        # 保存用户消息
        usr_msg = cls.add_message(session.session_id, "user", msg)

        # 构建 context
        context = []
        # 远期摘要
        if session.summary_content:
            context.append({"role": "system", "content": f"[历史摘要]\n{session.summary_content}"})
        # 近期消息
        recent = cls.get_recent_messages(session.session_id)
        for r in recent:
            context.append({"role": r["role"], "content": r["content"]})
        return context, session.session_id

    @classmethod
    def save_reply(cls, user_id: int, session_id: Optional[int], user_msg: str, ai_reply: str) -> int:
        """保存 AI 回复，返回 session_id"""
        session = cls.get_or_create_session(user_id, session_id)
        # 首次自动生成标题
        if not session.title or session.title == "新对话":
            new_title = user_msg[:20] + ("..." if len(user_msg) > 20 else "")
            AiSessionMapper.update_session(session.session_id, title=new_title, update_time=datetime.now())
        cls.add_message(session.session_id, "assistant", ai_reply)
        return session.session_id

    @classmethod
    def get_user_sessions(cls, user_id: int) -> List[Dict]:
        """获取用户会话列表"""
        sessions = AiSessionMapper.select_by_user(user_id)
        return [{"sessionId": s.session_id, "title": s.title, "messageCount": s.message_count, "createTime": s.create_time.isoformat() if s.create_time else None} for s in sessions]

    @classmethod
    def get_session_messages(cls, session_id: int, user_id: int) -> List[Dict]:
        session = AiSessionMapper.select_by_id(session_id)
        if not session or session.user_id != user_id:
            raise PermissionError("会话不存在")
        msgs = AiMessageMapper.select_by_session(session_id)
        return [{"role": m.role, "content": m.content, "createTime": m.create_time.isoformat() if m.create_time else None} for m in msgs]

    @classmethod
    def delete_session(cls, session_id: int, user_id: int):
        session = AiSessionMapper.select_by_id(session_id)
        if not session or session.user_id != user_id:
            raise PermissionError("会话不存在")
        AiMessageMapper.delete_by_session(session_id)
        AiSessionMapper.delete_session(session_id)

    @classmethod
    def clear_all_sessions(cls, user_id: int):
        sessions = AiSessionMapper.select_by_user(user_id)
        for s in sessions:
            AiMessageMapper.delete_by_session(s.session_id)
            AiSessionMapper.delete_session(s.session_id)

    # ==================== 基础方法 ====================

    @classmethod
    def get_or_create_session(cls, user_id: int, session_id: Optional[int] = None) -> AiSession:
        if session_id:
            sp = AiSessionMapper.select_by_id(session_id)
            if sp and sp.user_id == user_id:
                return AiSession(session_id=sp.session_id, user_id=sp.user_id, title=sp.title, model=sp.model, message_count=sp.message_count, total_tokens=sp.total_tokens, summary_content=sp.summary_content, status=sp.status, create_time=sp.create_time, update_time=sp.update_time)
        sp = BowlAiSession(user_id=user_id, title="新对话", model="deepseek-chat", message_count=0, total_tokens=0, status='1', create_time=datetime.now(), update_time=datetime.now())
        new_id = AiSessionMapper.insert_session(sp)
        return AiSession(session_id=new_id, user_id=user_id, title="新对话", model="deepseek-chat", message_count=0, total_tokens=0, status='1', create_time=datetime.now(), update_time=datetime.now())

    @classmethod
    def add_message(cls, session_id: int, role: str, content: str) -> AiMessage:
        msgs = AiMessageMapper.select_by_session(session_id)
        max_seq = max([m.seq for m in msgs], default=-1) + 1
        mp = BowlAiMessage(session_id=session_id, seq=max_seq, role=role, content=content, token_count=cls.estimate_tokens(content), is_compressed='0', create_time=datetime.now())
        new_id = AiMessageMapper.insert_message(mp)
        sp = AiSessionMapper.select_by_id(session_id)
        AiSessionMapper.update_session(session_id, message_count=len(msgs)+1, total_tokens=(sp.total_tokens or 0)+cls.estimate_tokens(content), update_time=datetime.now())
        return AiMessage(message_id=new_id, session_id=session_id, seq=max_seq, role=role, content=content, token_count=cls.estimate_tokens(content), is_compressed='0', create_time=datetime.now())

    @classmethod
    def get_recent_messages(cls, session_id: int) -> List[Dict]:
        msgs = AiMessageMapper.select_by_session_recent(session_id, MAX_MESSAGES_IN_CONTEXT)
        return [{"role": m.role, "content": m.content} for m in msgs]

    @classmethod
    def get_message_history(cls, session_id: int) -> List[Dict]:
        msgs = AiMessageMapper.select_by_session(session_id)
        return [{"message_id": m.message_id, "seq": m.seq, "role": m.role, "content": m.content, "create_time": m.create_time.isoformat() if m.create_time else None} for m in msgs]

    @classmethod
    def delete_session(cls, session_id: int, user_id: int):
        s = AiSessionMapper.select_by_id(session_id)
        if not s or s.user_id != user_id: raise PermissionError("无权操作")
        AiMessageMapper.delete_by_session(session_id)
        AiSessionMapper.delete_session(session_id)

    @classmethod
    def clear_all_sessions(cls, user_id: int):
        for s in AiSessionMapper.select_by_user(user_id):
            AiMessageMapper.delete_by_session(s.session_id)
            AiSessionMapper.delete_session(s.session_id)

    @classmethod
    def delete_session_admin(cls, session_id: int):
        """后台删除任意会话（不校验用户）"""
        AiMessageMapper.delete_by_session(session_id)
        AiSessionMapper.delete_session(session_id)
