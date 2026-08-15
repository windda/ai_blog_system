# -*- coding: utf-8 -*-

from typing import List, Optional

from owl_common.sqlalchemy.transaction import Transactional
from owl_blog.domain.entity import BlogCategory
from owl_blog.mapper.category import BlogCategoryMapper
from owl_admin.ext import db


class BlogCategoryService:
    
    @classmethod
    def select_category_by_id(cls, id: int) -> Optional[BlogCategory]:
        return BlogCategoryMapper.select_category_by_id(id)
    
    @classmethod
    def select_category_list(cls, query: BlogCategory) -> List[BlogCategory]:
        return BlogCategoryMapper.select_category_list(query)
    
    @classmethod
    @Transactional(db.session)
    def insert_category(cls, body: BlogCategory) -> bool:
        return BlogCategoryMapper.insert_category(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def update_category(cls, body: BlogCategory) -> bool:
        return BlogCategoryMapper.update_category(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_category_by_id(cls, id: int) -> bool:
        return BlogCategoryMapper.delete_category_by_id(id) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_category_by_ids(cls, ids: List[int]) -> bool:
        return BlogCategoryMapper.delete_category_by_ids(ids) > 0
