# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import alias, and_, case, func, insert, select, update
from sqlalchemy.orm import aliased

from owl_common.domain.entity import SysDept
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.po import SysDeptPo, SysRoleDeptPo, SysUserPo
from owl_admin.ext import db


class SysDeptMapper:
    
    """
    部门数据访问层
    """
    
    default_fields = {
        "dept_id", "parent_id", "ancestors", "dept_name", "order_num", 
        "leader", "phone", "email", "status", "del_flag", "create_by", 
        "create_time"
    }
    
    default_columns = ColumnEntityList(SysDeptPo, default_fields, False)
    
    @classmethod
    def select_dept_list(cls, dept: SysDept) -> List[SysDept]:
        """
        根据条件，查询部门列表
        
        Args:
            dept (SysDept): 部门实体
        
        Returns:
            List[SysDept]: 部门列表
        """        
        criterions = [SysDeptPo.del_flag=="0"]
        if dept.dept_id:
            criterions.append(SysDeptPo.dept_id==dept.dept_id)
        if dept.parent_id:
            criterions.append(SysDeptPo.parent_id==dept.parent_id)
        if dept.dept_name:
            criterions.append(SysDeptPo.dept_name.like(f'%{dept.dept_name}%'))
        if dept.status:
            criterions.append(SysDeptPo.status==dept.status)
        if "criterian_meta" in g and g.criterian_meta.scope:
            criterions.append(g.criterian_meta.scope)
        
        stmt = select(*cls.default_columns).where(*criterions)
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, SysDept) for row in rows]
        
    @classmethod
    def select_dept_list_by_role_id(
        cls, 
        role_id: int, 
        dept_check_strictly: bool
        ) -> List[int]:
        """
        根据角色ID，查询部门Id列表
        
        Args:
            role_id (int): 角色ID
            dept_check_strictly (bool): 是否严格检查部门权限
        
        Returns:
            List[int]: 部门ID列表
        """
        criterions = []
        criterions.append(SysRoleDeptPo.role_id==role_id)
        if dept_check_strictly:
            subquery = select(SysDeptPo.parent_id) \
                .join(SysRoleDeptPo, and_(
                    SysDeptPo.dept_id==SysRoleDeptPo.dept_id,
                    SysRoleDeptPo.role_id==role_id
                )) \
                .subquery()
            criterions.append(SysDeptPo.dept_id.not_in(subquery))
        
        stmt = select(SysDeptPo.dept_id).outerjoin(
            SysRoleDeptPo, SysDeptPo.dept_id==SysRoleDeptPo.dept_id
        ) \
            .where(*criterions) \
            .order_by(SysDeptPo.parent_id, SysDeptPo.order_num)
        rows = db.session.execute(stmt).scalars()
        return rows

    @classmethod
    def select_dept_by_id(cls, dept_id: int) -> Optional[SysDept]:
        """
        根据部门ID查询信息
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            Optional[SysDept]: 部门实体
        """
        fields = {
            "dept_id", "parent_id", "ancestors", "dept_name", "order_num", \
            "leader", "phone", "email", "status"
        }
        columns = ColumnEntityList(SysDeptPo, fields, alia_prefix=False)
        SysDeptPo_P = aliased(SysDeptPo, name="p")
        p_name_scalar = select(SysDeptPo_P.dept_name) \
            .where(SysDeptPo_P.dept_id==SysDeptPo.parent_id) \
            .scalar_subquery()
        columns.append_scalar(p_name_scalar.label("parent_name"))
        
        stmt = select(*columns).where(SysDeptPo.dept_id==dept_id)
        row = db.session.execute(stmt).one_or_none()
        return columns.cast(row, SysDept) if row else None

    @classmethod
    def select_children_dept_by_id(cls, dept_id: int) -> List[SysDept]:
        """
        根据ID查询所有子部门
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            List[SysDept]: 部门列表
        """
        fields = {
            "dept_id", "parent_id", "ancestors", "dept_name", "order_num", \
            "leader", "phone", "email", "status", "del_flag", "create_by", \
            "create_time"
        }
        columns = ColumnEntityList(SysDeptPo, fields, alia_prefix=False)
        
        stmt = select(*columns) \
            .where(func.find_in_set(dept_id, SysDeptPo.ancestors))
        rows = db.session.execute(stmt).all()
        
        return [columns.cast(row, SysDept) for row in rows]

    @classmethod
    def select_normal_children_dept_by_id(cls, dept_id: int) -> int:
        """
        根据ID，查询所有子部门（正常状态）
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            int: 部门数量
        """
        criterions = [SysDeptPo.status==0, SysDeptPo.del_flag=="0"]
        criterions.append(func.find_in_set(dept_id, SysDeptPo.ancestors))
        
        stmt = select(func.count()).select_from(SysDeptPo) \
            .where(*criterions)
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def has_child_by_dept_id(cls, dept_id: int) -> int:
        """
        是否存在子节点
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            int: 数量
        """
        criterions = [SysDeptPo.parent_id==dept_id, SysDeptPo.del_flag=="0"]
        
        stmt = select(func.count()).select_from(SysDeptPo) \
            .where(*criterions).limit(1)
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def check_dept_exist_user(cls, dept_id: int) -> int:
        """
        查询部门是否存在用户
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            int: 数量
        """
        criterions = [SysUserPo.dept_id==dept_id, SysUserPo.del_flag=="0"]
        
        stmt = select(func.count()).select_from(SysUserPo) \
            .where(*criterions) 
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def check_dept_name_unique(cls, dept_name: str, parent_id: int) -> Optional[SysDept]:
        """
        校验部门名称是否唯一
        
        Args:
            dept_name (str): 部门名称
            parent_id (int): 父部门ID
        
        Returns:
            Optional[SysDept]: 部门实体
        """
        criterions = [SysDeptPo.parent_id==parent_id]
        criterions.append(SysDeptPo.del_flag=="0")
        criterions.append(SysDeptPo.dept_name==dept_name)
        
        stmt = select(*cls.default_columns) \
            .where(*criterions)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, SysDept) if row else None

    @classmethod
    @Transactional(db.session)
    def insert_dept(cls, dept: SysDept) -> int:
        """
        新增部门信息
        
        Args:
            dept (SysDept): 部门实体
        
        Returns:
            int: 新增记录的ID
        """
        fields = {
            "dept_id", "parent_id", "ancestors", "dept_name", "order_num", 
            "leader", "phone", "email", "status", "create_by", "create_time"
        }
        data = dept.model_dump(
            include=fields,
            exclude_unset=True,
            exclude_none=True
        )
        stmt = insert(SysDeptPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    @Transactional(db.session)
    def update_dept(cls, dept: SysDept) -> int:
        """
        修改部门信息

        Args:
            dept (SysDept): 部门实体
        
        Returns:
            int: 数量
        """
        fields = {
            "parent_id", "ancestors", "dept_name", "order_num", "leader", 
            "phone", "email", "status", "create_by", "create_time"
        }
        data = dept.model_dump(
            include=fields,
            exclude_unset=True,
            exclude_none=True
        )
        stmt = update(SysDeptPo) \
            .where(SysDeptPo.dept_id==dept.dept_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def update_dept_status_normal(cls, dept_ids: List[int]) -> int:
        """
        修改所在部门正常状态

        Args:
            dept_ids (List[int]): 部门ID列表
        
        Returns:
            int: 数量
        """
        stmt = update(SysDeptPo) \
            .where(SysDeptPo.dept_id.in_(dept_ids)) \
            .values(status="0")
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def update_dept_children(cls, depts: List[SysDept]) -> int:
        """
        修改子元素关系
        
        Args:
            depts (List[SysDept]): 部门列表
        
        Returns:
            int: 数量
        """
        print("depts: {}".format(depts))
        
        case_expr = case(
            *[(SysDeptPo.dept_id==dept.dept_id, dept.ancestors) for dept in depts],
            else_=SysDeptPo.ancestors
        )
        stmt = update(SysDeptPo) \
            .where(SysDeptPo.dept_id.in_([dept.dept_id for dept in depts])) \
            .values(ancestors=case_expr)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_dept_by_id(cls, dept_id: int) -> int:
        """
        删除部门管理信息
        
        Args:
            dept_id (int): 部门ID
        
        Returns:
            int: 数量
        """
        stmt = update(SysDeptPo) \
            .where(SysDeptPo.dept_id==dept_id) \
            .values(del_flag="2")
        return db.session.execute(stmt).rowcount