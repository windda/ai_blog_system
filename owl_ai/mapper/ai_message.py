# -*- coding: utf-8 -*-

from typing import List
from sqlalchemy import select, insert, update, delete, desc

from owl_ai.domain.po import BowlAiMessage
from owl_admin.ext import db


class AiMessageMapper:

    @classmethod
    def select_by_session(cls, session_id: int, limit: int = 100) -> List[BowlAiMessage]:
        """按会话ID查询消息（按 seq 升序）"""
        stmt = select(BowlAiMessage).where(
            BowlAiMessage.session_id == session_id
        ).order_by(BowlAiMessage.seq.asc()).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    @classmethod
    def select_by_session_recent(cls, session_id: int, limit: int = 20) -> List[BowlAiMessage]:
        """查询最近 N 条消息（按 seq 降序取，内存反转）"""
        stmt = select(BowlAiMessage).where(
            BowlAiMessage.session_id == session_id
        ).order_by(BowlAiMessage.seq.desc()).limit(limit)
        rows = list(db.session.execute(stmt).scalars().all())
        return rows[::-1]  # 反转回升序

    @classmethod
    def insert_message(cls, msg: BowlAiMessage) -> int:
        """插入消息，返回 message_id"""
        stmt = insert(BowlAiMessage).values(
            session_id=msg.session_id,
            seq=msg.seq,
            role=msg.role,
            content=msg.content,
            token_count=msg.token_count,
            is_compressed=msg.is_compressed,
        )
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    def update_compressed_flag(cls, message_ids: List[int]):
        """批量标记消息为已压缩"""
        if not message_ids:
            return
        stmt = update(BowlAiMessage).where(
            BowlAiMessage.message_id.in_(message_ids)
        ).values(is_compressed='1')
        db.session.execute(stmt)

    @classmethod
    def update_content(cls, message_id: int, content: str) -> int:
        """更新消息内容（流式回复完成后回写）"""
        from owl_ai.domain.po import BowlAiMessage
        from sqlalchemy import update
        from owl_admin.ext import db
        stmt = update(BowlAiMessage).where(
            BowlAiMessage.message_id == message_id
        ).values(content=content)
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount

    @classmethod
    def delete_by_session(cls, session_id: int) -> int:
        """删除会话下所有消息"""
        stmt = delete(BowlAiMessage).where(
            BowlAiMessage.session_id == session_id
        )
        return db.session.execute(stmt).rowcount