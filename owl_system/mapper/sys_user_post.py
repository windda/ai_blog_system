# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from sqlalchemy import delete, func, insert, select

from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysUserPost
from owl_system.domain.po import SysUserPostPo
from owl_admin.ext import db


class SysUserPostMapper:
    
    """
    用户与岗位相关联的数据访问层
    """

    @classmethod
    @Transactional(db.session)
    def delete_user_post_by_user_id(cls, user_id: int) -> int:
        """
        通过用户ID删除用户和岗位关联

        Args:
            user_id (int): 用户ID

        Returns:
            int: 影响的行数
        """
        stmt = delete(SysUserPostPo).where(SysUserPostPo.user_id == user_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    def count_user_post_by_id(cls, post_id: int) -> int:
        """
        通过岗位ID查询岗位使用数量

        Args:
            post_id (int): 岗位ID

        Returns:
            int: 使用该岗位的用户数量
        """
        stmt = select(func.count()).select_from(SysUserPostPo) \
            .where(SysUserPostPo.post_id == post_id)
        return db.session.execute(stmt).scalar_one_or_none() or 0

    @classmethod
    @Transactional(db.session)
    def delete_user_post(cls, ids: List[int]) -> int:
        """
        批量删除用户和岗位关联

        Args:
            ids (List[int]): 用户ID列表
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysUserPostPo).where(SysUserPostPo.user_id.in_(ids))
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def batch_user_post(cls, user_post_list: List[SysUserPost]) -> int:
        """
        批量新增用户岗位信息

        Args:
            user_post_list (List[SysUserPost]): 用户岗位列表

        Returns:
            int: 影响的行数
        """
        user_post_list = [
            row.model_dump(
                exclude_none=True,
                exclude_unset=True
            ) 
            for row in user_post_list]
        stmt = insert(SysUserPostPo).values(user_post_list)
        return db.session.execute(stmt).rowcount
        
    @classmethod
    def select_post_ids_by_user_id(cls, user_id: int) -> List[int]:
        """
        根据用户ID查询岗位ID列表

        Args:
            user_id (int): 用户ID

        Returns:
            List[int]: 岗位ID列表
        """
        stmt = select(SysUserPostPo.post_id) \
            .where(SysUserPostPo.user_id == user_id)
        rows = db.session.execute(stmt).scalars().all()
        return list(rows)
