# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysPost
from owl_admin.ext import db
from owl_system.domain.po import SysPostPo, SysUserPo, SysUserPostPo


class SysPostMapper:
    
    """
    岗位的数据访问层
    """
    
    default_fields = {
        'post_id', 'post_name', 'post_code', 'post_sort', 'status', 
        'create_by', 'create_time', 'remark'
    }
    
    default_columns = ColumnEntityList(SysPostPo, default_fields, False)
    
    @classmethod
    def select_post_list(cls, post: SysPost) -> List[SysPost]:
        """
        根据条件，查询岗位列表
        
        Args:
            post (SysPost): 岗位条件
        Returns:
            List[SysPost]: 岗位列表
        """
        criterions = []
        if post.post_code:
            criterions.append(SysPostPo.post_code.like(f'%{post.post_code}%'))
        if post.post_name:
            criterions.append(SysPostPo.post_name.like(f'%{post.post_name}%'))
        if post.status:
            criterions.append(SysPostPo.post_status == post.status)
            
        stmt = select(*cls.default_columns).where(*criterions)
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysPost) for row in rows]

    @classmethod
    def select_post_all(cls) -> List[SysPost]:
        """
        查询所有岗位
        
        Returns:
            List[SysPost]: 岗位列表
        """
        stmt = select(*cls.default_columns)
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysPost) for row in rows]

    @classmethod
    def select_post_by_id(cls, post_id: int) -> Optional[SysPost]:
        """
        通过岗位ID查询岗位信息
        
        Args:
            post_id (int): 岗位ID
        Returns:
            Optional[SysPost]: 岗位信息
        """
        stmt = select(*cls.default_columns).where(SysPostPo.post_id == post_id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysPost) if row else None

    @classmethod
    def select_post_list_by_user_id(cls, user_id: int) -> List[int]:
        """
        根据用户ID，查询岗位ID列表
        
        Args:
            user_id (int): 用户ID
        Returns:
            List[int]: 岗位ID列表
        """        
        stmt = select(SysPostPo.post_id).select_from(SysPostPo) \
            .join(SysUserPostPo, SysUserPostPo.post_id == SysPostPo.post_id) \
           .join(SysUserPo, SysUserPo.user_id == SysUserPostPo.user_id) \
           .where(SysUserPo.user_id == user_id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def select_posts_by_user_name(cls, user_name: str) -> List[SysPost]:
        """
        根据用户名，查询岗位列表
        
        Args:
            user_name (str): 用户名
        Returns:
            List[SysPost]: 岗位列表
        """
        fields = {"post_id", "post_name", "post_code"}
        columns = ColumnEntityList(SysPostPo, fields, False)
        
        stmt = select(*columns).select_from(SysPostPo) \
            .join(SysUserPostPo, SysUserPostPo.post_id == SysPostPo.id) \
            .join(SysUserPo, SysUserPo.user_id == SysUserPostPo.user_id) \
            .where(SysUserPo.user_name == user_name)
            
        rows = db.session.execute(stmt).all()
        eos = list()
        for row in rows:
            eos.append(columns.cast(row,SysPost))
        return eos

    @classmethod
    @Transactional(db.session)
    def delete_post_by_id(cls, post_id: int) -> int:
        """
        删除岗位信息
        
        Args:
            post_id (int): 岗位ID
        Returns:
            int: 影响行数
        """
        stmt = delete(SysPostPo).where(SysPostPo.post_id == post_id)
        num = db.session.execute(stmt).rowcount
        return num

    @classmethod
    @Transactional(db.session)
    def delete_post_by_ids(cls, post_ids: List[int]) -> int:
        """
        批量删除岗位信息
        
        Args:
            post_ids (List[int]): 岗位ID列表
        Returns:
            int: 影响行数
        """
        stmt = delete(SysPostPo).where(SysPostPo.post_id.in_(post_ids))
        num = db.session.execute(stmt).rowcount
        return num

    @classmethod
    @Transactional(db.session)
    def update_post(cls, post: SysPost) -> int:
        """
        修改岗位信息
        
        Args:
            post (SysPost): 岗位信息
        Returns:
            int: 影响行数
        """
        fields = {
            "post_name", "post_code", "post_sort", "status", "remark", 
            "update_by", "update_time"
        }
        data = post.model_dump(
            include=fields, 
            exclude_none=True,
            exclude_unset=True
        )
        stmt = update(SysPostPo).where(SysPostPo.post_id == post.post_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def insert_post(cls, post: SysPost) -> int:
        """
        新增岗位信息
        
        Args:
            post (SysPost): 岗位信息
        Returns:
            int: 新增记录的ID
        """
        fields = {
            "post_id", "post_name", "post_code", "post_sort", "status", 
            "remark", "create_by", "create_time"
        }
        data = post.model_dump(
            include=fields, 
            exclude_none=True,
            exclude_unset=True
        )
        stmt = insert(SysPostPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    def check_post_name_unique(cls, post_name: str) -> Optional[SysPost]:
        """
        校验岗位名称
        
        Args:
            post_name (str): 岗位名称
            
        Returns:    
            Optional[SysPost]: 岗位信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysPostPo.post_name == post_name) \
            .limit(1)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysPost) if row else None

    @classmethod
    def check_post_code_unique(cls, post_code: str) -> Optional[SysPost]:
        """
        校验岗位编码
        
        Args:
            post_code (str): 岗位编码
            
        Returns:    
            Optional[SysPost]: 岗位信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysPostPo.post_code == post_code) \
            .limit(1)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysPost) if row else None