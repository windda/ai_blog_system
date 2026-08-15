# -*- coding: utf-8 -*-

from types import NoneType
from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_blog.domain.entity import BlogTag
from owl_blog.domain.po import BlogTagPo
from owl_admin.ext import db


class BlogTagMapper:
    
    default_fields = {
        "tag_id", "tag_name", "order_num",
        "create_time", "update_time", "create_by", "update_by", "remark"
    }
    
    default_columns = ColumnEntityList(BlogTagPo, default_fields, False)
    
    @classmethod
    def select_tag_by_id(cls, id: int) -> Optional[BlogTag]:
        stmt = select(*cls.default_columns) \
            .where(BlogTagPo.tag_id == id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, BlogTag) if row else None
    
    @classmethod
    def select_tag_list(cls, tag: BlogTag | NoneType) -> List[BlogTag]:
        if tag is None:
            stmt = select(*cls.default_columns).order_by(BlogTagPo.order_num)
        else:
            criterions = []
            if tag.tag_name:
                criterions.append(
                    BlogTagPo.tag_name.like(f'%{tag.tag_name}%')
                )
            stmt = select(*cls.default_columns) \
                .where(*criterions) \
                .order_by(BlogTagPo.order_num)
            if "criterian_meta" in g and g.criterian_meta.page:
                g.criterian_meta.page.stmt = stmt
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, BlogTag) for row in rows]
    
    @classmethod
    def insert_tag(cls, tag: BlogTag) -> int:
        fields = {
            "tag_name", "order_num", "create_by", "create_time", "remark"
        }
        data = tag.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = insert(BlogTagPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
    
    @classmethod
    def update_tag(cls, tag: BlogTag) -> int:
        fields = {
            "tag_name", "order_num", "update_by", "update_time", "remark"
        }
        data = tag.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = update(BlogTagPo) \
            .where(BlogTagPo.tag_id == tag.tag_id) \
            .values(data)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_tag_by_id(cls, id: int) -> int:
        stmt = delete(BlogTagPo).where(BlogTagPo.tag_id == id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_tag_by_ids(cls, ids: List[int]) -> int:
        stmt = delete(BlogTagPo).where(BlogTagPo.tag_id.in_(ids))
        return db.session.execute(stmt).rowcount
