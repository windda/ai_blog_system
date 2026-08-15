# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from sqlalchemy import delete, func, insert, select

from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysUserRole
from owl_admin.ext import db
from owl_system.domain.po import SysUserRolePo


class SysUserRoleMapper:
    
    """
    用户与角色相关联的数据访问层
    """

    @classmethod
    @Transactional(db.session)
    def delete_user_role_by_user_id(cls, user_id: int) -> int:
        """
        通过用户ID删除用户和角色关联

        Args:
            user_id (int): 用户ID
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysUserRolePo).where(SysUserRolePo.user_id==user_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_user_role(cls, ids: List[int]) -> int:
        """
        批量删除用户和角色关联

        Args:
            ids (List[int]): 需要删除的数据ID列表
        
        Returns:
            int: 影响的行数
        """ 
        stmt = delete(SysUserRolePo) \
            .where(SysUserRolePo.role_id.in_(ids))
        return db.session.execute(stmt).rowcount

    @classmethod
    def count_user_role_by_role_id(cls, role_id: int) -> int:
        """
        通过角色ID查询角色使用数量

        Args:
            role_id (int): 角色ID
        
        Returns:
            int: 使用该角色的用户数量
        """
        stmt = select(func.count()).select_from(SysUserRolePo) \
            .where(SysUserRolePo.role_id==role_id)
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    @Transactional(db.session)
    def batch_user_role(cls, user_role_list: List[SysUserRole]) -> int:
        """
        批量新增用户角色信息

        Args:
            user_role_list (List[SysUserRole]): 用户角色列表
        
        Returns:
            int: 影响的行数
        """
        user_role_list = [
            row.model_dump(
                exclude_none=True,
                exclude_unset=True
            ) 
            for row in user_role_list]
        stmt = insert(SysUserRolePo).values(user_role_list)
        return db.session.execute(stmt).rowcount
        
    @classmethod
    @Transactional(db.session)
    def delete_user_role_info(cls, user_role: SysUserRole) -> int:
        """
        删除用户和角色关联信息

        Args:
            user_role (SysUserRole): 用户角色信息
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysUserRolePo).where(
            SysUserRolePo.user_id==user_role.user_id,
            SysUserRolePo.role_id==user_role.role_id
            )
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_user_role_infos(cls, role_id: int, user_ids: List[int]) -> int:
        """
        批量取消授权用户角色

        Args:
            role_id (int): 角色ID
            user_ids (List[int]): 用户ID列表
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysUserRolePo).where(
            SysUserRolePo.user_id.in_(user_ids),
            SysUserRolePo.role_id==role_id
            )
        return db.session.execute(stmt).rowcount

    @classmethod
    def select_role_ids_by_user_id(cls, user_id: int) -> List[int]:
        """
        根据用户ID查询角色ID列表

        Args:
            user_id (int): 用户ID

        Returns:
            List[int]: 角色ID列表
        """
        stmt = select(SysUserRolePo.role_id) \
            .where(SysUserRolePo.user_id == user_id)
        rows = db.session.execute(stmt).scalars().all()
        return list(rows)
