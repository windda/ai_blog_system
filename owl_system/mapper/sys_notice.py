# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from types import NoneType
from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_system.domain.entity import SysNotice
from owl_system.domain.po import SysNoticePo
from owl_admin.ext import db


class SysNoticeMapper:
    
    """
    公告的数据访问层
    """

    default_fields = {
        "notice_id", "notice_title", "notice_type", "notice_content", "status",
        "create_time", "update_time", "create_by", "update_by", "remark"
    }
    
    default_columns = ColumnEntityList(SysNoticePo, default_fields, False)
    
    @classmethod
    def select_notice_by_id(cls, id: int) -> Optional[SysNotice]:
        """
        根据公告ID，查询公告信息

        Args:
            id (int): 公告ID

        Returns:
            Optional[SysNotice]: 公告信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysNoticePo.notice_id == id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysNotice) if row else None

    @classmethod
    def select_notice_list(cls, notice: SysNotice|NoneType) -> List[SysNotice]:
        """
        根据条件，查询公告列表

        Args:
            notice (SysNotice|NoneType): 公告信息

        Returns:
            List[SysNotice]: 公告列表
        """
        if notice is None:
            stmt = select(*cls.default_columns)
        else:
            criterions = []
            if notice.notice_title:
                criterions.append(
                    SysNoticePo.notice_title.like(f'%{notice.notice_title}%')
                )
            if notice.notice_type:
                criterions.append(
                    SysNoticePo.notice_type == notice.notice_type
                )
            if notice.create_by:
                criterions.append(
                    SysNoticePo.create_by.like(f'%{notice.create_by}%')
                )
            stmt = select(*cls.default_columns) \
                .where(*criterions)
            if "criterian_meta" in g and g.criterian_meta.page:
                g.criterian_meta.page.stmt = stmt
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysNotice) for row in rows]
        
    @classmethod
    def insert_notice(cls, notice: SysNotice) -> int:
        """
        新增一条公告记录

        Args:
            notice (SysNotice): 公告信息

        Returns:
            int: 新增记录的ID
        """
        fields = {
            "notice_title", "notice_type", "notice_content", "status",
            "create_by", "create_time", "remark"
        }
        data = notice.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = insert(SysNoticePo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    def update_notice(cls, notice: SysNotice) -> int:
        """
        修改公告信息

        Args:
            notice (SysNotice): 公告信息

        Returns:
            int: 修改数据量
        """
        fields = {
            "notice_title", "notice_type", "notice_content", "status",
            "update_by", "update_time", "remark"
        }
        data = notice.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = update(SysNoticePo) \
            .where(SysNoticePo.notice_id == notice.notice_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    def delete_notice_by_id(cls, id: int) -> int:
        """
        根据公告ID，删除公告

        Args:
            id (int): 公告ID

        Returns:
            int: 删除数据量
        """
        stmt = delete(SysNoticePo) \
            .where(SysNoticePo.notice_id == id)
        return db.session.execute(stmt).rowcount

    @classmethod
    def delete_notice_by_ids(cls, ids: List[int]) -> int:
        """
        批量删除公告

        Args:
            ids (List[int]): 公告ID列表

        Returns:
            int: 删除数据量
        """
        stmt = delete(SysNoticePo) \
            .where(SysNoticePo.notice_id.in_(ids))
        return db.session.execute(stmt).rowcount
