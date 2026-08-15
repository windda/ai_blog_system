# -*- coding: utf-8 -*-

from typing import List, Set
from owl_common.domain.entity import SysUser
from owl_common.utils import security_util as SecurityUtil
from owl_system.service import SysMenuService,SysRoleService


class SysPermissionService:
    
    @classmethod
    def get_role_permission(cls, user:SysUser) -> List[str]:
        """
        获取用户角色权限

        Args:
            user (SysUser): 用户信息

        Returns:
            List[str]: 角色权限列表
        """
        if SecurityUtil.is_admin(user.user_id):
            roles = ["admin"]
        else:
            roles = SysRoleService.select_role_permission_by_user_id(user.user_id)
        return roles
    
    @classmethod
    def get_menu_permission(cls, user:SysUser) -> List[str]:
        """
        获取用户菜单权限

        Args:
            user (SysUser): 用户信息

        Returns:
            List[str]: 菜单权限列表
        """
        if SecurityUtil.is_admin(user.user_id):
            perms = ["*:*:*"]
        else:
            perms = SysMenuService.select_menu_perms_by_user_id(user.user_id)
        return perms
    