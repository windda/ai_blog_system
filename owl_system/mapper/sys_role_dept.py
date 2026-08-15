# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List

from sqlalchemy import delete, func, insert, select
from owl_admin.ext import db
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysRoleDept
from owl_system.domain.po import SysRoleDeptPo


class SysRoleDeptMapper:
    
    """
    部门与角色相关联的数据访问层
    """

    @classmethod
    @Transactional(db.session)
    def batch_role_dept(cls, role_dept_list: List[SysRoleDept]) -> int:
        """
        批量新增角色部门信息

        Args:
            role_dept_list (List[SysRoleDept]): 角色部门列表
        
        Returns:
            int: 操作影响的行数
        """
        role_dept_list = [
            row.model_dump(
                exclude_none=True,
                exclude_unset=True,
            ) for row in role_dept_list]
        stmt = insert(SysRoleDeptPo).values(role_dept_list)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    @Transactional(db.session)
    def delete_role_dept_by_role_id(cls, role_id: int) -> int:
        """
        根据角色ID，删除角色和部门关联数据

        Args:
            role_id (int): 角色ID
        
        Returns:
            int: 操作影响的行数
        """
        stmt = delete(SysRoleDeptPo).where(SysRoleDeptPo.role_id == role_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_role_dept(cls, role_ids: List[int]) -> int:
        """
        批量删除角色部门关联信息

        Args:
            role_ids (List[int]): 多个角色ID
        
        Returns:
            int: 操作影响的行数
        """
        stmt = delete(SysRoleDeptPo).where(SysRoleDeptPo.role_id.in_(role_ids))
        return db.session.execute(stmt).rowcount
        
    @classmethod
    def select_count_role_dept_by_dept_id(cls, dept_id: int) -> int:
        """
        查询部门使用的角色数量

        Args:
            dept_id (int): 部门ID
        
        Returns:
            int: 角色数量
        """
        stmt = select(func.count()).select_from(SysRoleDeptPo) \
            .where(SysRoleDeptPo.dept_id == dept_id)
        return db.session.execute(stmt).scalar_one_or_none() or 0

