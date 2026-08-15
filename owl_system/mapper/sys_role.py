# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import func, select,update,insert

from owl_common.base.model import ExtraModel
from owl_common.domain.entity import SysRole
from owl_admin.ext import db
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.po import SysDeptPo, SysRolePo, SysUserPo, SysUserRolePo

class SysRoleMapper:
    
    """
    角色数据访问层
    """
    
    default_fields = {
        "role_id", "role_name", "role_key", "role_sort", "data_scope", \
        "menu_check_strictly", "dept_check_strictly", "status", "del_flag", \
        "create_time", "remark"
    }
    
    default_columns = ColumnEntityList(SysRolePo, default_fields)
    
    default_select = select(*default_columns).distinct() \
        .outerjoin(SysUserRolePo, SysUserRolePo.role_id == SysRolePo.role_id) \
        .outerjoin(SysUserPo,SysUserPo.user_id == SysUserRolePo.user_id) \
        .outerjoin(SysDeptPo,SysDeptPo.dept_id == SysUserPo.dept_id)

    @classmethod
    def select_role_list(cls, role: SysRole) -> List[SysRole]:
        """
        根据条件，查询角色列表
        
        Args:
            role: SysRole: 角色查询条件
        
        Returns:
            List[SysRole]: 角色列表
        """
        
        criterions = [SysRolePo.del_flag=="0"]
        if role.role_id and role.role_id != 0:
            criterions.append(SysRolePo.role_id==role.role_id)
        if role.role_name:
            criterions.append(SysRolePo.role_name.like(f"%{role.role_name}%"))
        if role.role_key:
            criterions.append(SysRolePo.role_key.like(f"%{role.role_key}%"))
        if role.status:
            criterions.append(SysRolePo.status==role.status)
        if "criterian_meta" in g and g.criterian_meta.extra:
            extra:ExtraModel = g.criterian_meta.extra
            if extra.start_time and extra.end_time:
                criterions.append(SysRolePo.create_time >= extra.start_time)
                criterions.append(SysRolePo.create_time <= extra.end_time)
        if "criterian_meta" in g and g.criterian_meta.scope:
            criterions.append(g.criterian_meta.scope)
        
        stmt = cls.default_select.where(*criterions)
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
                
        rows = db.session.execute(stmt).all()
        
        eos = list()
        for row in rows:
            role = cls.default_columns.cast(row,SysRole)
            eos.append(role)
        return eos

    @classmethod
    def select_role_permission_by_user_id(cls, user_id: int) -> List[SysRole]:
        """
        根据用户ID，查询角色
        
        Args:
            user_id: int: 用户ID
        
        Returns:
            List[SysRole]: 角色列表
        """
        criterions = [SysRolePo.del_flag=="0"]
        criterions.append(SysUserRolePo.user_id==user_id)
        stmt = cls.default_select.where(*criterions)
        rows = db.session.execute(stmt).all()
        eos = list()
        for row in rows:
            role = cls.default_columns.cast(row,SysRole)
            eos.append(role)
        return eos

    @classmethod
    def select_role_all(cls) -> List[SysRole]:
        """
        查询所有角色
        
        Returns:
            List[SysRole]: 角色列表
        """
        stmt = cls.default_select
        rows = db.session.execute(stmt).all()
        eos = list()
        for row in rows:
            role = cls.default_columns.cast(row,SysRole)
            eos.append(role)
        return eos
    
    @classmethod
    def select_role_list_by_user_name(cls, user_name: str) -> List[SysRole]:
        """
        根据用户名，查询角色列表
        
        Args:
            user_name: str: 用户名
        
        Returns:    
            List[SysRole]: 角色列表
        """
        criterions = [SysRolePo.del_flag=="0"]
        criterions.append(SysUserPo.user_name==user_name)
        stmt = cls.default_select.where(*criterions)
        rows = db.session.execute(stmt).all()
        eos = list()
        for row in rows:
            role = cls.default_columns.cast(row,SysRole)
            eos.append(role)
        return eos

    @classmethod
    def select_role_list_by_user_id(cls, user_id: int) -> List[int]:
        """
        根据用户ID，查询角色选择框列表
        
        Args:
            user_id: int: 用户ID
        
        Returns:
            List[int]: 角色ID列表
        """
        stmt = select(SysRolePo.role_id).select_from(SysRolePo) \
            .outerjoin(SysUserRolePo, SysUserRolePo.role_id == SysRolePo.role_id) \
            .outerjoin(SysUserPo, SysUserPo.user_id == SysUserRolePo.user_id) \
            .where(SysUserPo.user_id==user_id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def select_role_by_id(cls, role_id: int) -> Optional[SysRole]:
        """
        根据角色ID，查询角色
        
        Args:
            role_id: int: 角色ID
        
        Returns:
            Optional[SysRole]: 角色
        """        
        stmt = cls.default_select.where(SysRolePo.role_id==role_id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysRole) if row else None

    @classmethod
    def count_user_role_by_role_id(cls, role_id: int) -> int:
        """
        根据角色ID，查询角色使用数量
        
        Args:
            role_id: int: 角色ID
        
        Returns:
            int: 角色使用数量
        """
        stmt = select(func.count()).select_from(SysUserRolePo) \
            .where(SysUserRolePo.role_id==role_id)
        return db.session.execute(stmt).scalar() or 0
        
    @classmethod
    def check_role_name_unique(cls, role_name:str) -> Optional[SysRole]:
        """
        检查角色名称是否唯一
        
        Args:
            role_name: str: 角色名称
        
        Returns:
            Optional[SysRole]: 角色
        """
        criterions = [SysRolePo.del_flag=="0"]
        criterions.append(SysRolePo.role_name==role_name)
        stmt = cls.default_select.where(*criterions).limit(1)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysRole) if row else None

    @classmethod
    def check_role_key_unique(cls, role_key:str) -> Optional[SysRolePo]:
        """
        校验角色权限是否唯一
        
        Args:
            role_key: str: 角色权限
        
        Returns:
            Optional[SysRolePo]: 角色
        """
        criterions = [SysRolePo.del_flag=="0"]
        criterions.append(SysRolePo.role_key==role_key)
        stmt = cls.default_select.where(*criterions).limit(1)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysRole) if row else None
    
    @classmethod
    @Transactional(db.session)
    def insert_role(cls, role: SysRole) -> int:
        """
        新增角色信息
        
        Args:
            role: SysRole: 角色信息
        
        Returns:
            int: 新增记录的ID
        """
        fields = {
            "role_id", "role_name", "role_key", "role_sort", "data_scope", \
            "menu_check_strictly", "dept_check_strictly", "status", "remark", \
            "create_by", "create_time"
        }
        data = role.model_dump(
            include=fields,
            exclude_unset=True,
            exclude_none=True
        )
        
        stmt = insert(SysRolePo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
            
    @classmethod
    @Transactional(db.session)
    def update_role(cls, role: SysRole) -> int:
        """
        修改角色信息
        
        Args:
            role: SysRole: 角色信息
        
        Returns:
            int: 修改数量
        """
        fields = {
            "role_name", "role_key", "role_sort", "data_scope", \
            "menu_check_strictly", "dept_check_strictly", "status", "remark", \
            "update_by", "update_time"
        }
        data = role.model_dump(
            include=fields,exclude_unset=True,exclude_none=True
        )
        stmt = update(SysRolePo) \
            .where(SysRolePo.role_id==role.role_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_role_by_id(cls, role_id: int) -> int:
        """
        根据角色ID，删除角色
        
        Args:
            role_id: int: 角色ID
        
        Returns:
            int: 删除数量
        """
        stmt = update(SysRolePo).where(SysRolePo.role_id==role_id) \
            .values(del_flag="2")
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_role_by_ids(cls, role_ids: List[int]) -> int:
        """
        批量删除角色信息
        
        Args:
            role_ids: List[int]: 角色ID列表
        
        Returns:
            int: 删除数量
        """
        stmt = update(SysRolePo).where(SysRolePo.role_id.in_(role_ids)) \
            .values(del_flag="2")
        return db.session.execute(stmt).rowcount
