# -*- coding: utf-8 -*-

from typing import List, Optional
from sqlalchemy import select, insert, update, delete, desc

from owl_ai.domain.po import BowlAiSession
from owl_admin.ext import db


class AiSessionMapper:

    @classmethod
    def select_by_id(cls, session_id: int) -> Optional[BowlAiSession]:
        stmt = select(BowlAiSession).where(BowlAiSession.session_id == session_id)
        return db.session.execute(stmt).scalar_one_or_none()

    @classmethod
    def select_by_user(cls, user_id: int, status: str = '1') -> List[BowlAiSession]:
        stmt = select(BowlAiSession).where(
            BowlAiSession.user_id == user_id,
            BowlAiSession.status == status
        ).order_by(desc(BowlAiSession.update_time))
        return list(db.session.execute(stmt).scalars().all())

    @classmethod
    def insert_session(cls, session: BowlAiSession) -> int:
        """新增会话，返回 session_id"""
        stmt = insert(BowlAiSession).values(
            user_id=session.user_id,
            title=session.title,
            model=session.model,
            message_count=session.message_count,
            total_tokens=session.total_tokens,
            status=session.status,
        )
        out = db.session.execute(stmt).inserted_primary_key
        db.session.commit()
        return out[0] if out else 0

    @classmethod
    def update_session(cls, session_id: int, **kwargs):
        if not kwargs:
            return
        stmt = update(BowlAiSession).where(
            BowlAiSession.session_id == session_id
        ).values(**kwargs)
        db.session.execute(stmt)
        db.session.commit()

    @classmethod
    def delete_session(cls, session_id: int) -> int:
        stmt = delete(BowlAiSession).where(BowlAiSession.session_id == session_id)
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount
    @classmethod
    def select_all(cls) -> List[BowlAiSession]:
        stmt = select(BowlAiSession).order_by(desc(BowlAiSession.update_time))
        return list(db.session.execute(stmt).scalars().all())
