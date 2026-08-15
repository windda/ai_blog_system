# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import and_, delete, func, insert, select, update

from owl_common.domain.entity import SysMenu
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.po import SysMenuPo, SysRoleMenuPo, SysRolePo, SysUserPo, SysUserRolePo
from owl_admin.ext import db


class SysMenuMapper:
    
    """
    菜单数据访问层
    """
    
    default_fields = {
        'menu_id','menu_name', 'parent_id', 'order_num', 'path', 'component', 
        'query', 'is_frame', 'is_cache', 'menu_type', 'perms', 'visible', 
        'status', 'icon', 'create_by', 'create_time', 'update_by', 
        'update_time'
    }
    
    default_columns = ColumnEntityList(SysMenuPo, default_fields, False)
        
    @classmethod
    def select_menu_list(cls, menu: SysMenu) -> List[SysMenu]:
        """
        查询系统菜单列表
        
        Args:
            menu (SysMenu): 查询条件
        
        Returns:
            List[SysMenu]: 菜单列表
        """
        criterions = []
        if menu.menu_name:
            criterions.append(SysMenuPo.menu_name.like(f'%{menu.menu_name}%'))
        if menu.status:
            criterions.append(SysMenuPo.status == menu.status)
        if menu.visible:
            criterions.append(SysMenuPo.visible == menu.visible)
        
        # columns.append_scalar(func.ifnull(SysMenuPo.perms, '').label('perms'))
        
        stmt = select(*cls.default_columns) \
            .where(*criterions) \
            .order_by(SysMenuPo.parent_id, SysMenuPo.order_num)
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, SysMenu) for row in rows]

    @classmethod
    def select_menu_perms(cls) -> List[str]:
        """
        根据用户，查询所有权限
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            List[str]: 权限列表
        """
        stmt = select(SysMenuPo.perms).distinct() \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .join(SysUserRolePo, SysUserRolePo.role_id == SysRoleMenuPo.role_id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def select_menu_perms_by_role_id(cls, role_id: int) -> List[str]:
        """
        根据角色ID，查询权限
        
        Args:
            role_id (int): 角色ID
        
        Returns:
            List[str]: 权限列表
        """
        coritations = [SysMenuPo.status == "0"]
        coritations.append(SysRoleMenuPo.role_id == role_id)
        
        stmt = select(SysMenuPo.perms).distinct() \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .where(*coritations)
        return db.session.execute(stmt).scalars().all()
    
    @classmethod
    def select_menu_perms_by_user_id(cls, user_id: int) -> List[str]:
        """
        根据用户ID，查询权限
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            List[str]: 权限列表
        """
        coritations = [SysMenuPo.status == "0"]
        coritations.append(SysRolePo.status == "0")
        coritations.append(SysUserRolePo.user_id == user_id)

        stmt = select(SysMenuPo.perms).distinct() \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .join(SysUserRolePo, SysUserRolePo.role_id == SysRoleMenuPo.role_id) \
            .join(SysRolePo, SysRolePo.role_id == SysUserRolePo.role_id) \
            .where(and_(*coritations))
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def select_menu_tree_all(cls) -> List[SysMenu]:
        """
        查询所有菜单
        
        Returns:
            List[SysMenu]: 菜单列表
        """
        fields = {
            "menu_id", "parent_id", "menu_name", "path", "component", 
            "query", "visible", "status", "perms", "is_frame", 
            "is_cache", "menu_type", "icon", "order_num", "create_time"
        }
        columns = ColumnEntityList(SysMenuPo, fields, False)
        
        coritations = [SysMenuPo.status == "0"]
        coritations.append(SysMenuPo.menu_type.in_(['M', 'C']))
        
        stmt = select(*columns).distinct() \
            .where(*coritations) \
            .order_by(SysMenuPo.parent_id, SysMenuPo.order_num)
        
        rows = db.session.execute(stmt).all()
        return [columns.cast(row, SysMenu) for row in rows]
    
    @classmethod
    def select_menu_tree_by_user_id(cls, user_id: int) -> List[SysMenu]:
        """
        根据用户ID，查询菜单树
        
        Args:
            user_id (int): 用户ID
        
        Returns:
            List[SysMenuPo]: 菜单列表
        """
        fields = {
            "menu_id", "parent_id", "menu_name", "path", "component", 
            "query", "visible", "status", "perms", "is_frame", 
            "is_cache", "menu_type", "icon", "order_num", "create_time"
        }
        columns = ColumnEntityList(SysMenuPo, fields, False)
        
        coritations = [SysMenuPo.status == "0"]
        coritations.append(SysRolePo.status=="0")
        coritations.append(SysMenuPo.menu_type.in_(['M', 'C']))
        coritations.append(SysUserPo.user_id==user_id)
        
        stmt = select(*columns).distinct() \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .join(SysUserRolePo, SysUserRolePo.role_id == SysRoleMenuPo.role_id) \
            .join(SysRolePo, SysRolePo.role_id == SysUserRolePo.role_id) \
            .join(SysUserPo, SysUserPo.user_id == SysUserRolePo.user_id) \
            .where(*coritations) \
            .order_by(SysMenuPo.parent_id, SysMenuPo.order_num)
        
        rows = db.session.execute(stmt).all()
        return [columns.cast(row, SysMenu) for row in rows]

    @classmethod
    def select_menu_list_by_user_id(cls, menu: SysMenu, user_id: int) -> List[SysMenu]:
        """
        根据用户ID，查询菜单列表
        
        Args:
            menu (SysMenu): 查询条件
            user_id (int): 用户ID
        
        Returns:
            List[SysMenu]: 菜单列表
        """
        coritations = [SysMenuPo.user_id == user_id]
        if menu.menu_name is not None and menu.menu_name != '':
            coritations.append(SysMenuPo.menu_name.like(menu.menu_name))
        if menu.status is not None and menu.status != '':
            coritations.append(SysMenuPo.status == menu.status)
        if menu.visible is not None and menu.visible != '':
            coritations.append(SysMenuPo.visible == menu.visible)
            
        stmt = select(*cls.default_columns) \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .join(SysUserRolePo, SysUserRolePo.role_id == SysRoleMenuPo.role_id) \
            .join(SysRolePo, SysRolePo.role_id == SysUserRolePo.role_id) \
            .where(*coritations) \
            .order_by(SysMenuPo.parent_id, SysMenuPo.order_num)
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, SysMenu) for row in rows]
    
    @classmethod
    def select_menu_list_by_role_id(cls, role_id: int, menu_check_strictly: bool) -> List[int]:
        """
        根据角色ID，查询菜单列表
        
        Args:
            role_id (int): 角色ID
            menu_check_strictly (bool): 是否严格检查菜单
        
        Returns:
            List[int]: 菜单ID列表
        """
        coritations = [SysRoleMenuPo.role_id == role_id]
        if menu_check_strictly:
            subquery = select(SysMenuPo.parent_id) \
                .join(SysRoleMenuPo, SysMenuPo.menu_id == SysRoleMenuPo.menu_id) \
                .filter(SysRoleMenuPo.role_id == role_id) \
                .subquery()
            coritations.append(SysMenuPo.menu_id.notin_(subquery))
        stmt = select(SysMenuPo.menu_id) \
            .join(SysRoleMenuPo, SysRoleMenuPo.menu_id == SysMenuPo.menu_id) \
            .where(*coritations) \
            .order_by(SysMenuPo.parent_id, SysMenuPo.order_num)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def select_menu_by_id(cls, menu_id: int) -> Optional[SysMenuPo]:
        """
        根据ID，查询菜单
        
        Args:
            menu_id (int): 菜单ID
        
        Returns:
            Optional[SysMenuPo]: 菜单信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysMenuPo.menu_id == menu_id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, SysMenu) if row else None

    @classmethod
    def has_child_by_menu_id(cls, menu_id: int) -> int:
        """
        是否存在菜单子节点
        
        Args:
            menu_id (int): 菜单ID
        
        Returns:
            int: 子节点数量
        """
        stmt = select(func.count(SysMenuPo.menu_id)) \
            .where(SysMenuPo.parent_id == menu_id)
        return db.session.execute(stmt).scalar() or 0

    @classmethod
    @Transactional(db.session)
    def insert_menu(cls, menu: SysMenu) -> int:
        """
        新增菜单信息
        
        Args:
            menu (SysMenu): 菜单信息
        
        Returns:
            int: 新增记录的ID
        """
        fields = {
            "menu_name", "parent_id", "order_num", "path", "component", 
            "query", "is_frame", "is_cache", "menu_type", "perms", "visible", 
            "status", "icon", "create_by", "create_time"
        }
        stmt = insert(SysMenuPo).values(menu.model_dump(
            include=fields,
            exclude_none=True,
            exclude_unset=True,
            ))
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    @Transactional(db.session)
    def update_menu(cls, menu: SysMenu) -> int:
        """
        修改菜单信息
        
        Args:
            menu (SysMenu): 菜单信息
        
        Returns:
            int: 修改记录数
        """
        fields = {
            "menu_name", "parent_id", "order_num", "path", "component", 
            "query", "is_frame", "is_cache", "menu_type", "perms", "visible", 
            "status", "icon", "update_by", "update_time"
        }
        stmt = update(SysMenuPo).values(menu.model_dump(
            include=fields,
            exclude_none=True,
            exclude_unset=True,
            )) \
            .where(SysMenuPo.menu_id == menu.menu_id)
        return db.session.execute(stmt).rowcount
        
    @classmethod
    @Transactional(db.session)
    def delete_menu_by_id(cls, menu_id: int) -> int:
        """
        删除菜单信息
        
        Args:
            menu_id (int): 菜单ID
        
        Returns:
            int: 删除记录数
        """
        stmt = delete(SysMenuPo).where(SysMenuPo.menu_id == menu_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    def check_menu_name_unique(cls, menu_name: str, parent_id: int) -> Optional[SysMenu]:
        """
        校验菜单名称是否唯一
        
        Args:
            menu_name (str): 菜单名称
            parent_id (int): 父菜单ID
        
        Returns:
            Optional[SysMenu]: 菜单信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysMenuPo.menu_name == menu_name, SysMenuPo.parent_id == parent_id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, SysMenu) if row else None
