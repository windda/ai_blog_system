# -*- coding: utf-8 -*-
"""博客专栏 Service"""

import datetime
from typing import List, Optional
from owl_blog.domain.entity import BlogColumn
from owl_blog.mapper.column import BlogColumnMapper


class BlogColumnService:

    @classmethod
    def select_public_list(cls) -> List[BlogColumn]:
        return BlogColumnMapper.select_public_list()

    @classmethod
    def select_column_list(cls, dto: Optional[BlogColumn] = None) -> List[BlogColumn]:
        return BlogColumnMapper.select_list(dto)

    @classmethod
    def select_column_by_id(cls, column_id: int) -> Optional[BlogColumn]:
        return BlogColumnMapper.select_by_id(column_id)

    @classmethod
    def insert_column(cls, column: BlogColumn) -> int:
        column.create_time = datetime.datetime.now()
        return BlogColumnMapper.insert(column)

    @classmethod
    def update_column(cls, column: BlogColumn) -> int:
        column.update_time = datetime.datetime.now()
        return BlogColumnMapper.update(column)

    @classmethod
    def delete_by_id(cls, column_id: int) -> int:
        return BlogColumnMapper.delete_by_id(column_id)