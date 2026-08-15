# -*- coding: utf-8 -*-

from typing import List, Optional

from owl_common.sqlalchemy.transaction import Transactional
from owl_blog.domain.entity import BlogTag
from owl_blog.mapper.tag import BlogTagMapper
from owl_admin.ext import db


class BlogTagService:
    
    @classmethod
    def select_tag_by_id(cls, id: int) -> Optional[BlogTag]:
        return BlogTagMapper.select_tag_by_id(id)
    
    @classmethod
    def select_tag_list(cls, query: BlogTag) -> List[BlogTag]:
        return BlogTagMapper.select_tag_list(query)
    
    @classmethod
    @Transactional(db.session)
    def insert_tag(cls, body: BlogTag) -> bool:
        return BlogTagMapper.insert_tag(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def update_tag(cls, body: BlogTag) -> bool:
        return BlogTagMapper.update_tag(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_tag_by_id(cls, id: int) -> bool:
        return BlogTagMapper.delete_tag_by_id(id) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_tag_by_ids(cls, ids: List[int]) -> bool:
        return BlogTagMapper.delete_tag_by_ids(ids) > 0
