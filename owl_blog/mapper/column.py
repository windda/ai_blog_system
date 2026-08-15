# -*- coding: utf-8 -*-
"""
博客专栏 Mapper — 专栏数据访问层。

专栏与文章通过 author_id 关联；后台查询按权限隔离，
用户只能管理自己创建的专栏；前台仅返回正常状态的专栏。
"""

from typing import List, Optional
from flask import g
from sqlalchemy import select, func, insert, update, delete

from owl_blog.domain.entity import BlogColumn
from owl_blog.domain.po import BlogColumnPo, BlogArticlePo
from owl_system.domain.po import SysUserPo
from owl_admin.ext import db


class BlogColumnMapper:
    """专栏数据访问层"""

    @classmethod
    def select_by_id(cls, column_id: int) -> Optional[BlogColumn]:
        """按ID查询专栏（联表查询作者昵称）"""
        stmt = select(
            BlogColumnPo,
            SysUserPo.nick_name.label('author_name'),
        ).outerjoin(
            SysUserPo, BlogColumnPo.author_id == SysUserPo.user_id
        ).where(
            BlogColumnPo.column_id == column_id
        )
        row = db.session.execute(stmt).one_or_none()
        if not row:
            return None
        return cls._row_to_entity(row)

    @classmethod
    def select_list(cls, dto: Optional[BlogColumn] = None) -> List[BlogColumn]:
        """查询专栏列表（后台用，支持条件过滤 + 分页）"""
        stmt = select(
            BlogColumnPo,
            SysUserPo.nick_name.label('author_name'),
        ).outerjoin(
            SysUserPo, BlogColumnPo.author_id == SysUserPo.user_id
        )

        if dto:
            if dto.column_name:
                stmt = stmt.where(BlogColumnPo.column_name.like(f'%{dto.column_name}%'))
            if dto.status:
                stmt = stmt.where(BlogColumnPo.status == dto.status)
            if dto.author_id:
                stmt = stmt.where(BlogColumnPo.author_id == dto.author_id)

        stmt = stmt.order_by(BlogColumnPo.order_num.asc(), BlogColumnPo.create_time.desc())

        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt

        rows = db.session.execute(stmt).all()
        result = []
        for r in rows:
            col = cls._row_to_entity(r)
            # 统计该专栏下的文章数
            count = db.session.execute(
                select(func.count(BlogArticlePo.article_id))
                .where(BlogArticlePo.author_id == r[0].author_id)
                .where(BlogArticlePo.status == '1')
            ).scalar() or 0
            col.article_count = count
            result.append(col)
        return result

    @classmethod
    def select_public_list(cls) -> List[BlogColumn]:
        """查询公开专栏列表（前台用，只返回 status='1'）"""
        stmt = select(
            BlogColumnPo,
            SysUserPo.nick_name.label('author_name'),
        ).outerjoin(
            SysUserPo, BlogColumnPo.author_id == SysUserPo.user_id
        ).where(
            BlogColumnPo.status == '1'
        ).order_by(
            BlogColumnPo.order_num.asc(),
            BlogColumnPo.create_time.desc()
        )
        rows = db.session.execute(stmt).all()
        result = []
        for r in rows:
            col = cls._row_to_entity(r)
            count = db.session.execute(
                select(func.count(BlogArticlePo.article_id))
                .where(BlogArticlePo.author_id == r[0].author_id)
                .where(BlogArticlePo.status == '1')
            ).scalar() or 0
            col.article_count = count
            result.append(col)
        return result

    @classmethod
    def insert(cls, column: BlogColumn) -> int:
        """插入专栏"""
        stmt = insert(BlogColumnPo).values(
            column_name=column.column_name,
            description=column.description or '',
            cover_image=column.cover_image or '',
            author_id=column.author_id,
            status=column.status or '0',
            order_num=column.order_num or 0,
            create_by=column.create_by or '',
            create_time=column.create_time,
        )
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    def update(cls, column: BlogColumn) -> int:
        """更新专栏"""
        stmt = update(BlogColumnPo).where(
            BlogColumnPo.column_id == column.column_id
        ).values(
            column_name=column.column_name,
            description=column.description or '',
            cover_image=column.cover_image or '',
            status=column.status,
            order_num=column.order_num,
            update_by=column.update_by or '',
            update_time=column.update_time,
        )
        return db.session.execute(stmt).rowcount

    @classmethod
    def delete_by_id(cls, column_id: int) -> int:
        """删除专栏"""
        stmt = delete(BlogColumnPo).where(BlogColumnPo.column_id == column_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    def _row_to_entity(cls, row) -> BlogColumn:
        """将查询行转为实体"""
        po = row[0]
        author_name = row[1] if len(row) > 1 else None
        return BlogColumn(
            column_id=po.column_id,
            column_name=po.column_name,
            description=po.description,
            cover_image=po.cover_image,
            author_id=po.author_id,
            status=po.status,
            order_num=po.order_num,
            create_by=po.create_by,
            create_time=po.create_time,
            update_by=po.update_by,
            update_time=po.update_time,
            remark=po.remark,
            author_name=author_name,
        )