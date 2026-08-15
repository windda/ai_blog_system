# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from types import NoneType
from typing import Any, List, Literal

from owl_common.sqlalchemy.transaction import Transactional
from owl_common.utils import security_util as SecurityUtil
from owl_common.constant import UserConstants
from owl_common.domain.entity import SysDept, SysRole, TreeSelect
from owl_common.exception import ServiceException
from owl_system.mapper import SysDeptMapper, SysRoleMapper
from owl_admin.ext import db


class SysDeptService:
    
    @classmethod
    def select_dept_list(cls, dept:SysDept) -> List[SysDept]:
        """
        查询部门列表

        Args:
            dept (SysDept): 包含查询条件的传输对象

        Returns:
            List[SysDept]: 部门列表
        """
        return SysDeptMapper.select_dept_list(dept or SysDept())
    
    @classmethod
    def select_dept_tree_list(cls, dept:SysDept):
        """
        查询部门树列表

        Args:
            dept (SysDept): 包含查询条件的传输对象

        Returns:
            List[TreeSelect]: 部门树列表
        """
        eos: List[SysDept] = cls.select_dept_list(dept)
        return cls.build_dept_tree_select(eos)
        
    @classmethod
    def build_dept_tree(cls, depts:List[SysDept]) -> List[SysDept]:
        """
        构建部门树

        Args:
            depts (List[SysDept]): 部门列表

        Returns:
            List[SysDept]: 部门树列表
        """
        return_list = []
        temp_list = []
        for dept in depts:
            temp_list.append(dept.dept_id)
        for dept in depts:
            if dept.parent_id not in temp_list:
                cls.recursion_fn(depts, dept)
                return_list.append(dept)
        if not return_list:
            return_list = depts
        return return_list

    @classmethod
    def build_dept_tree_select(cls, depts:List[SysDept]) -> List[TreeSelect]:
        """
        构建部门树选择框

        Args:
            depts (List[SysDept]): 部门列表

        Returns:
            List[TreeSelect]: 部门树选择框列表  
        """
        dept_trees = cls.build_dept_tree(depts)
        return [TreeSelect.from_dept(dept) for dept in dept_trees]

    @classmethod
    def select_dept_list_by_role_id(cls, role_id:int) -> List[int]:
        """
        根据角色ID，查询部门列表
        
        Args:
            role_id (int): 角色ID

        Returns:
            List[int]: 部门列表
        """
        role:SysRole = SysRoleMapper.select_role_by_id(role_id)
        return SysDeptMapper.select_dept_list_by_role_id(
            role_id, role.dept_check_strictly
        )

    @classmethod
    def select_dept_by_id(cls, dept_id:int) -> SysDept|NoneType:
        """
        根据部门ID，查询部门信息
        
        Args:
            dept_id (int): 部门ID

        Returns:
            SysDept|NoneType: 部门信息
        """
        return SysDeptMapper.select_dept_by_id(dept_id)        

    @classmethod
    def select_normal_children_dept_by_id(cls, dept_id:int) -> int:
        """
        根据部门ID，查询正常部门的数量
        
        Args:
            dept_id (int): 部门ID

        Returns:
            int: 正常部门的数量
        """
        return SysDeptMapper.select_normal_children_dept_by_id(dept_id)

    @classmethod
    def has_child_by_dept_id(cls, dept_id:int) -> int:
        """
        根据部门ID，判断是否有子部门
        
        Args:
            dept_id (int): 部门ID

        Returns:
            int: 数量
        """
        return SysDeptMapper.has_child_by_dept_id(dept_id)

    @classmethod
    def check_dept_exist_user(cls, dept_id:int) -> int:
        """
        判断部门是否存在用户
        
        Args:
            dept_id (int): 部门ID

        Returns:
            int: 数量
        """
        return SysDeptMapper.check_dept_exist_user(dept_id)

    @classmethod
    def check_dept_name_unique(cls, dept:SysDept) -> Literal["0","1"]:
        """
        判断部门名称是否唯一
        
        Args:
            dept (SysDept): 部门信息

        Returns:
            Literal["0","1"]: 唯一或不唯一, 0: 唯一, 1: 不唯一
        """
        dept_id = -1 if dept.dept_id is None else dept.dept_id
        eo:SysDept = SysDeptMapper.check_dept_name_unique(dept.dept_name, dept.parent_id)
        if eo is None:
            return UserConstants.UNIQUE
        if eo.dept_id != dept_id:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE

    @classmethod
    def check_dept_data_scope(cls, dept_id:int):
        """
        判断部门数据权限
        
        Args:
            dept_id (int): 部门ID

        Raises:
            ServiceException: 无权限访问部门数据
        """
        if not SecurityUtil.login_user_is_admin():
            dept = SysDept(dept_id=dept_id)
            depts = cls.select_dept_list(dept)
            if not depts:
                raise ServiceException("没有权限访问部门数据！")
            
    @classmethod
    def insert_dept(cls, dept:SysDept) -> int:
        """
        新增部门信息

        Args:
            dept (SysDept): 部门信息

        Returns:
            int: 部门ID
        """
        parent = SysDeptMapper.select_dept_by_id(dept.parent_id)
        if not UserConstants.DEPT_NORMAL == parent.status:
            raise ServiceException("部门停用，不允许新增")
        dept.ancestors = f"{parent.ancestors},{dept.parent_id}"
        return SysDeptMapper.insert_dept(dept)

    @classmethod
    @Transactional(db.session)
    def update_dept(cls, dept:SysDept) -> int:
        """
        修改部门信息

        Args:
            dept (SysDept): 部门信息

        Returns:
            int: 数量
        """
        parent_dept = SysDeptMapper.select_dept_by_id(dept.parent_id)
        old_dept = SysDeptMapper.select_dept_by_id(dept.dept_id)
        if parent_dept is not None and old_dept is not None:
            new_ancestors = f"{parent_dept.ancestors},{parent_dept.dept_id}"
            old_ancestors = old_dept.ancestors
            dept.ancestors = new_ancestors
            cls.update_dept_children(dept.dept_id, new_ancestors, old_ancestors)
        num = SysDeptMapper.update_dept(dept)
        if UserConstants.DEPT_NORMAL == dept.status and dept.ancestors and dept.ancestors != "0":
            # 如果该部门是启用状态，则启用该部门的所有上级部门
            cls.update_parent_dept_status_normal(dept)
        return num

    @classmethod
    def update_parent_dept_status_normal(cls, dept:SysDept):
        """
        修改该部门的父级部门

        Args:
            dept (SysDept): 部门信息
        """
        dept_ids = dept.ancestors.split(",")
        SysDeptMapper.update_dept_status_normal(dept_ids)

    @classmethod
    def update_dept_children(cls, dept_id, new_ancestors, old_ancestors):
        """
        修改子元素关系

        Args:
            dept_id (int): 部门ID
            new_ancestors (str): 新的祖先路径
            old_ancestors (str): 旧的祖先路径
        """
        children:List[SysDept] = SysDeptMapper.select_children_dept_by_id(dept_id)
        for child in children:
            child.ancestors = (child.ancestors.replace(old_ancestors, new_ancestors, 1))
        if children:
            SysDeptMapper.update_dept_children(children)

    @classmethod
    def delete_dept_by_id(cls, dept_id) -> int:
        """
        删除部门管理信息

        Args:
            dept_id (int): 部门ID

        Returns:
            int: 数量
        """
        return SysDeptMapper.delete_dept_by_id(dept_id)

    @classmethod
    def recursion_fn(cls, list:List[SysDept], t:SysDept):
        """
        递归列表
        
        Args:
            list (List[SysDept]): 部门列表
            t (SysDept): 父节点
        """
        child_list = cls.get_child_list(list, t)
        t.children = child_list
        for t_child in child_list:
            if cls.has_child(list, t_child):
                cls.recursion_fn(list, t_child)

    @classmethod
    def get_child_list(cls, list:List[SysDept], t:SysDept) -> List[Any]:
        """
        获取子节点列表
        
        Args:
            list (List[SysDept]): 部门列表
            t (SysDept): 父节点

        Returns:
            List[Any]: 子节点列表
        """
        tlist = []
        for n in list:
            if n.parent_id is not None and n.parent_id==t.dept_id:
                tlist.append(n)
        return tlist

    @classmethod
    def has_child(cls, list:List[SysDept], t:SysDept) -> bool:
        """
        判断是否有子节点
        
        Args:
            list (List[SysDept]): 部门列表
            t (SysDept): 父节点

        Returns:
            bool: 是否有子节点
        """
        for n in list:
            if n.parent_id is not None and n.parent_id==t.dept_id:
                return True
        return False
