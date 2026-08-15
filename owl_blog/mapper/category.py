# -*- coding: utf-8 -*-

from types import NoneType
from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_blog.domain.entity import BlogCategory
from owl_blog.domain.po import BlogCategoryPo
from owl_admin.ext import db


class BlogCategoryMapper:
    
    default_fields = {
        "category_id", "category_name", "order_num", "status",
        "create_time", "update_time", "create_by", "update_by", "remark"
    }
    
    default_columns = ColumnEntityList(BlogCategoryPo, default_fields, False)
    
    @classmethod
    def select_category_by_id(cls, id: int) -> Optional[BlogCategory]:
        stmt = select(*cls.default_columns) \
            .where(BlogCategoryPo.category_id == id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, BlogCategory) if row else None
    
    @classmethod
    def select_category_list(cls, category: BlogCategory | NoneType) -> List[BlogCategory]:
        if category is None:
            stmt = select(*cls.default_columns).order_by(BlogCategoryPo.order_num)
        else:
            criterions = []
            if category.category_name:
                criterions.append(
                    BlogCategoryPo.category_name.like(f'%{category.category_name}%')
                )
            if category.status:
                criterions.append(BlogCategoryPo.status == category.status)
            stmt = select(*cls.default_columns) \
                .where(*criterions) \
                .order_by(BlogCategoryPo.order_num)
            if "criterian_meta" in g and g.criterian_meta.page:
                g.criterian_meta.page.stmt = stmt
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, BlogCategory) for row in rows]
    
    @classmethod
    def insert_category(cls, category: BlogCategory) -> int:
        fields = {
            "category_name", "order_num", "status",
            "create_by", "create_time", "remark"
        }
        data = category.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = insert(BlogCategoryPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
    
    @classmethod
    def update_category(cls, category: BlogCategory) -> int:
        fields = {
            "category_name", "order_num", "status",
            "update_by", "update_time", "remark"
        }
        data = category.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = update(BlogCategoryPo) \
            .where(BlogCategoryPo.category_id == category.category_id) \
            .values(data)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_category_by_id(cls, id: int) -> int:
        stmt = delete(BlogCategoryPo).where(BlogCategoryPo.category_id == id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_category_by_ids(cls, ids: List[int]) -> int:
        stmt = delete(BlogCategoryPo).where(BlogCategoryPo.category_id.in_(ids))
        return db.session.execute(stmt).rowcount
