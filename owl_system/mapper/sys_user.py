# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional 
from flask import g
from sqlalchemy import and_, delete, or_, func, insert, select, update

from owl_common.base.model import ExtraModel
from owl_common.domain.entity import SysDept, SysRole, SysUser
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.po import SysDeptPo, SysRolePo, SysUserPo, \
    SysUserPostPo, SysUserRolePo
from owl_admin.ext import db


class SysUserMapper:
    
    """
    用户数据访问层
    """

    default_fields = {
        "user_id", "dept_id", "user_name", "nick_name", "email", "phonenumber",
        "avatar", "status", "password", "sex", "del_flag", "login_ip", 
        "login_date", "create_by", "create_time", "update_by", "update_time",
        "remark"
    }
    
    default_columns = ColumnEntityList(SysUserPo, default_fields, False)
    
    @classmethod
    def select_user_list(cls, user: SysUser) -> List[SysUser]:
        """
        根据条件，查询用户列表

        Args:
            user: 用户传输条件信息

        Returns:
            用户信息列表
        """
        dept_vo_fields = {"dept_name","leader"}
        user_columns = ColumnEntityList(SysUserPo, cls.default_fields)
        dept_columns = ColumnEntityList(SysDeptPo, dept_vo_fields)
                
        criterions = [SysUserPo.del_flag=="0"]
        if user.user_id is not None and user.user_id != 0:
            criterions.append(SysUserPo.user_id==user.user_id)
        if user.user_name is not None and user.user_name != '':
            criterions.append(SysUserPo.user_name.like(f"%{user.user_name}%"))
        if user.status is not None and user.status != 0:
            criterions.append(SysUserPo.status==user.status)
        if user.phonenumber is not None and user.phonenumber != '':
            criterions.append(SysUserPo.phonenumber.like(f"%{user.phonenumber}%"))
        if user.dept_id is not None and user.dept_id != 0:
            subquery = select(SysUserPo.dept_id).where(or_(
                SysUserPo.dept_id==user.dept_id,
                func.find_in_set(user.dept_id, SysDeptPo.ancestors)
            )).subquery()
            criterions.append(SysUserPo.dept_id.in_(subquery))
        if g.criterian_meta.extra:
            extra:ExtraModel = g.criterian_meta.extra
            if extra.start_time and extra.end_time:
                criterions.append(SysUserPo.create_time >= extra.start_time)
                criterions.append(SysUserPo.create_time <= extra.end_time)
        if g.criterian_meta.scope:
            criterions.append(g.criterian_meta.scope)
        
        stmt = select(*user_columns, *dept_columns) \
            .join(SysDeptPo,SysUserPo.dept_id==SysDeptPo.dept_id) \
            .where(*criterions)
        if g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt

        rows = db.session.execute(stmt).all()
        
        eos = list()
        for row in rows:
            user = user_columns.cast(row,SysUser)
            user.dept = dept_columns.cast(row,SysDept)
            eos.append(user)
        return eos

    @classmethod
    def select_allocated_list(cls, user: SysUser) -> List[SysUser]:
        """
        根据条件，查询已配用户角色列表

        Args:
            user (SysUser): 用户传输条件信息

        Returns:
            List[SysUser]: 用户信息列表
        """
        fields = {"user_id", "dept_id", "user_name", "nick_name", "email", \
            "phonenumber", "status", "create_time"}
        columns = ColumnEntityList(SysUserPo, fields, alia_prefix=False)
        
        criterions = [SysUserPo.del_flag=="0"]
        if user.user_name:
            criterions.append(SysUserPo.user_name.like(f"%{user.user_name}%"))
        if user.phonenumber:
            criterions.append(SysUserPo.phonenumber.like(f"%{user.phonenumber}%"))
        if "criterian_meta" in g and g.criterian_meta.scope:
            criterions.append(g.criterian_meta.scope)
        
        stmt = select(*columns).distinct() \
            .join(SysDeptPo, SysUserPo.dept_id==SysDeptPo.dept_id) \
            .join(SysUserRolePo, SysUserPo.user_id==SysUserRolePo.user_id) \
            .join(SysRolePo, SysUserRolePo.role_id==SysRolePo.role_id) \
            .where(*criterions)
        rows = db.session.execute(stmt).all()
        
        return [columns.cast(row,SysUser) for row in rows]

    @classmethod
    def select_unallocated_list(cls, user: SysUser) -> List[SysUser]:
        """
        根据条件，查询未分配用户角色列表

        Args:
            user (SysUser): 用户传输条件信息

        Returns:
            List[SysUser]: 用户信息列表
        """
        fields = {
            "user_id", "dept_id", "user_name", "nick_name", "email", \
            "phonenumber", "status", "create_time"
        }
        columns = ColumnEntityList(SysUserPo, fields, False)
        
        criterions = [SysUserPo.del_flag=="0"]
        subquery = select(SysUserPo.user_id) \
            .join(SysUserRolePo, and_(
                SysUserPo.user_id==SysUserRolePo.user_id,
                SysUserRolePo.role_id==user.role_id
            )) \
            .subquery()
        criterions.append(or_(
            SysRolePo.role_id!=user.role_id,
            SysRolePo.role_id.is_(None)
        ))
        criterions.append(SysUserPo.user_id.notin_(subquery))
        if user.user_name:
            criterions.append(SysUserPo.user_name.like(f"%{user.user_name}%"))
        if user.phonenumber:
            criterions.append(SysUserPo.phonenumber.like(f"%{user.phonenumber}%"))
        if "criterian_meta" in g and g.criterian_meta.scope:
            criterions.append(g.criterian_meta.scope)
        
        stmt = select(*columns).distinct() \
            .join(SysDeptPo, SysUserPo.dept_id==SysDeptPo.dept_id) \
            .join(SysUserRolePo, SysUserPo.user_id==SysUserRolePo.user_id) \
            .join(SysRolePo, SysUserRolePo.role_id==SysRolePo.role_id) \
            .where(*criterions)
        rows = db.session.execute(stmt).all()

        return [columns.cast(row,SysUser) for row in rows]

    @classmethod
    def select_user_by_user_name(cls, user_name: str) -> Optional[SysUser]:
        """
        通过用户名查询用户

        Args:
            user_name (str): 用户名

        Returns:
            Optional[SysUser]: 用户信息
        """
        return cls.select_user_by_unique_map("user_name", user_name)

    @classmethod
    def select_user_by_id(cls, user_id: int) -> Optional[SysUser]:
        """
        通过用户ID查询用户

        Args:
            user_id (int): 用户ID

        Returns:
            Optional[SysUser]: 用户信息
        """
        return cls.select_user_by_unique_map("user_id", user_id)
    
    @classmethod
    def select_user_by_unique_map(
        cls, 
        key: str, 
        value: int|str
        ) -> Optional[SysUser]:
        """
        通过含有唯一键的条件，查询用户

        Args:
            key (str): 唯一键名
            value (int|str): 唯一键值

        Returns:
            Optional[SysUser]: 用户信息
        """
        dept_vo_fields = {
            "dept_id", "parent_id", "dept_name", "order_num", "leader", 
            "status"
        }
        role_vo_fields = {
            "role_id", "role_name", "role_key", "role_sort", "data_scope", 
            "status"
        }
        
        user_columns = ColumnEntityList(SysUserPo, cls.default_fields)
        dept_columns = ColumnEntityList(SysDeptPo, dept_vo_fields)
        role_columns = ColumnEntityList(SysRolePo, role_vo_fields)
        
        column = getattr(SysUserPo, key)
        stmt = select(*user_columns,*dept_columns,*role_columns).distinct() \
            .join(SysDeptPo, SysUserPo.dept_id==SysDeptPo.dept_id) \
            .join(SysUserRolePo, SysUserPo.user_id==SysUserRolePo.user_id) \
            .join(SysRolePo, SysUserRolePo.role_id==SysRolePo.role_id) \
            .where(column==value)
        rows = db.session.execute(stmt).all()
        
        eo_tmp = {}
        for row in rows:
            if key in eo_tmp:
                user = eo_tmp[key]
            else:
                user = user_columns.cast(row,SysUser)
                user.dept = dept_columns.cast(row,SysDept)
                eo_tmp[key] = user
            user.roles.append(role_columns.cast(row,SysRole))
            
        return eo_tmp[key] if rows else None

    @classmethod
    @Transactional(db.session)
    def insert_user(cls, user: SysUser) -> int:
        """
        新增用户信息

        Args:
            user (SysUser): 用户信息

        Returns:
            int: 新增记录的ID
        """
        fields = {
            "user_id", "dept_id", "user_name", "nick_name", "email", "avatar",
            "phonenumber", "sex", "password", "status", "create_by", "remark"
        }
        data = user.model_dump(
            include=fields,
            exclude_unset=True,
            exclude_none=True
        )
        stmt = insert(SysUserPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    @Transactional(db.session)
    def update_user(cls, user: SysUser) -> int:
        """
        修改用户信息

        Args:
            user (SysUser): 用户信息

        Returns:
            int: 修改数量
        """
        fields = {
            "dept_id", "user_name", "nick_name", "email", "avatar", "login_ip",
            "phonenumber", "sex", "password", "login_date", "status", "update_by", 
            "remark"
        }
        data = user.model_dump(
            include=fields,exclude_unset=True,exclude_none=True
        )
        stmt = update(SysUserPo) \
            .where(SysUserPo.user_id==user.user_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def update_user_avatar(cls, user_name: str, avatar: str) -> int:
        """
        修改用户头像

        Args:
            user_name (str): 用户名
            avatar (str): 头像地址

        Returns:
            int: 修改数量
        """
        stmt = update(SysUserPo) \
            .where(SysUserPo.user_name==user_name) \
            .values(**{'avatar': avatar})
        return db.session.execute(stmt).rowcount
    
    @classmethod
    @Transactional(db.session)
    def reset_user_pwd(cls, user_name: str, password: str) -> int:
        """
        重置用户密码

        Args:
            user_name (str): 用户名
            password (str): 密码

        Returns:
            int: 修改数量
        """
        stmt = update(SysUserPo) \
            .where(SysUserPo.user_name==user_name) \
            .values(password=password)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_user_by_id(cls, user_id: int) -> int:
        """
        通过用户ID物理删除用户（同时删除关联的角色和岗位）

        Args:
            user_id (int): 用户ID

        Returns:
            int: 删除数量
        """
        # 先删关联表
        db.session.execute(
            delete(SysUserRolePo).where(SysUserRolePo.user_id == user_id)
        )
        db.session.execute(
            delete(SysUserPostPo).where(SysUserPostPo.user_id == user_id)
        )
        # 再删用户
        stmt = delete(SysUserPo).where(SysUserPo.user_id == user_id)
        num = db.session.execute(stmt).rowcount
        return num
    
    @classmethod
    @Transactional(db.session)
    def delete_user_by_ids(cls, user_ids: List[int]) -> int:
        """
        批量物理删除用户信息（同时删除关联的角色和岗位）

        Args:
            user_ids (List[int]): 用户ID列表

        Returns:
            int: 删除数量
        """
        # 先删关联表
        db.session.execute(
            delete(SysUserRolePo).where(SysUserRolePo.user_id.in_(user_ids))
        )
        db.session.execute(
            delete(SysUserPostPo).where(SysUserPostPo.user_id.in_(user_ids))
        )
        # 再删用户
        stmt = delete(SysUserPo).where(SysUserPo.user_id.in_(user_ids))
        num = db.session.execute(stmt).rowcount
        return num

    @classmethod
    def check_user_name_unique(cls, user_name: str) -> int:
        """
        校验用户名称是否唯一

        Args:
            user_name (str): 用户名称

        Returns:
            int: 0-唯一，大于0-已存在
        """
        stmt = select(func.count()).select_from(SysUserPo) \
            .where(SysUserPo.user_name==user_name) \
            .where(SysUserPo.del_flag=="0")
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    def check_phone_unique(cls, phone_number: str) -> Optional[SysUser]:
        """
        校验手机号码是否唯一

        Args:
            phone_number (str): 手机号码

        Returns:
            Optional[SysUser]: 用户信息
        """
        fields = {"user_id","phonenumber"}
        columns = ColumnEntityList(
            SysUserPo, fields, alia_prefix=False
            )
        
        stmt = select(*columns) \
            .where(SysUserPo.phonenumber==phone_number) \
            .where(SysUserPo.del_flag=="0")
        row = db.session.execute(stmt).one_or_none()
        return columns.cast(row,SysUser) if row else None

    @classmethod
    def check_email_unique(cls, email: str) -> Optional[SysUser]:
        """
        校验email是否唯一

        Args:
            email (str): email

        Returns:
            Optional[SysUser]: 用户信息
        """
        fields = {"user_id","email"}
        columns = ColumnEntityList(
            SysUserPo, fields, alia_prefix=False
            )
        
        stmt = select(*columns) \
            .where(SysUserPo.email==email) \
            .where(SysUserPo.del_flag=="0")
        row = db.session.execute(stmt).one_or_none()
        return columns.cast(row,SysUser) if row else None
    
    @classmethod
    def select_user_detail_by_id(cls, user_id: int) -> Optional[SysUser]:
        """
        通过用户ID查询用户详情（不含角色关联，避免INNER JOIN导致无角色用户查不到）

        Args:
            user_id (int): 用户ID

        Returns:
            Optional[SysUser]: 用户信息
        """
        dept_vo_fields = {
            "dept_id", "parent_id", "dept_name", "order_num", "leader", 
            "status"
        }
        
        user_columns = ColumnEntityList(SysUserPo, cls.default_fields)
        dept_columns = ColumnEntityList(SysDeptPo, dept_vo_fields)
        
        stmt = select(*user_columns, *dept_columns) \
            .join(SysDeptPo, SysUserPo.dept_id == SysDeptPo.dept_id) \
            .where(SysUserPo.user_id == user_id)
        row = db.session.execute(stmt).one_or_none()
        if not row:
            return None
        
        user = user_columns.cast(row, SysUser)
        user.dept = dept_columns.cast(row, SysDept)
        return user
