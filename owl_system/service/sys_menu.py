# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Literal, Optional, Set

from owl_common.constant import Constants, UserConstants
from owl_common.domain.entity import SysRole, TreeSelect
from owl_system.domain.vo import RouterMetaVo, RouterVo
from owl_system.mapper import SysMenuMapper
from owl_common.utils import security_util as SecurityUtil, StringUtil
from owl_common.domain.entity import SysMenu
from owl_system.mapper.sys_role import SysRoleMapper
from owl_system.mapper.sys_role_menu import SysRoleMenuMapper


class SysMenuService:
    
    @classmethod
    def select_menu_list_by_user_id(cls, user_id) -> List[SysMenu]:
        '''
        根据用户，查询菜单列表
        
        Args:
            user_id(int): 用户ID
            
        Returns:
            List[SysMenu]: 菜单列表
        '''
        return cls.select_menu_list(SysMenu(), user_id)
    
    @classmethod
    def select_menu_list(cls, menu:SysMenu, user_id:int) -> List[SysMenu]:
        '''
        查询菜单列表
        
        Args:
            menu(SysMenu): 菜单实体
            user_id(int): 用户ID
            
        Returns:
            List[SysMenu]: 菜单列表
        '''
        if SecurityUtil.is_admin(user_id):
            eos: List[SysMenu] = SysMenuMapper.select_menu_list(menu)
        else:
            eos: List[SysMenu] = SysMenuMapper \
            .select_menu_list_by_user_id(menu, user_id)
        return eos
        
    @classmethod
    def select_menu_perms_by_user_id(cls, user_id:int) -> List[str]:
        '''
        根据用户ID，查询菜单权限列表
        
        Args:
            user_id(int): 用户ID
            
        Returns:
            List[str]: 菜单权限列表
        '''
        perms: List[str] = SysMenuMapper.select_menu_perms_by_user_id(user_id)
        perm_set = set()
        for perm in perms:
            if perm:
                perm_set |= set(perm.strip().split(','))
        return list(perm_set)
    
    @classmethod
    def select_menu_perms_by_role_id(cls, role_id:int) -> Set[str]:
        '''
        根据角色ID，查询菜单权限列表
        
        Args:
            role_id(int): 角色ID
            
        Returns:
            Set[str]: 菜单权限集合
        '''
        perms: List[str] = SysMenuMapper.select_menu_perms_by_role_id(role_id)
        perm_set = set()
        for perm in perms:
            if perm:
                perm_set |= set(perm.strip().split(','))
        return perm_set

    @classmethod
    def select_menu_tree_by_user_id(cls, user_id:int) -> List[SysMenu]:
        '''
        根据角色ID，查询菜单树
        
        Args:
            user_id(int): 用户ID
            
        Returns:
            List[SysMenu]: 菜单树
        '''
        if SecurityUtil.is_admin(user_id):
            eos: List[SysMenu] = SysMenuMapper.select_menu_tree_all()
        else:
            eos: List[SysMenu] = SysMenuMapper.select_menu_tree_by_user_id(user_id)
        return cls.get_child_perms(eos, 0)
        
    @classmethod
    def select_menu_list_by_role_id(cls, role_id:int):
        '''
        根据角色ID，查询菜单列表
        
        Args:
            role_id(int): 角色ID
            
        Returns:
            List[SysMenu]: 菜单列表
        '''
        eo:SysRole = SysRoleMapper.select_role_by_id(role_id)
        return SysMenuMapper.select_menu_list_by_role_id(role_id,eo.menu_check_strictly)

    @classmethod
    def build_menus(cls, menus:List[SysMenu]):
        '''
        构建菜单
        
        Args:
            menus(List[SysMenu]): 菜单列表
            
        Returns:
            List[RouterVo]: 路由列表
        '''
        routers:List[RouterVo] = []
        for menu in menus:
            rv:RouterVo = RouterVo()
            rv.hidden = False if menu.visible == "0" else True
            rv.name = cls.get_route_name(menu)
            rv.path = cls.get_router_path(menu)
            rv.component = cls.get_component(menu)            
            rv.query = menu.query
            rv.meta = RouterMetaVo(
                title=menu.menu_name, 
                icon=menu.icon, 
                no_cache=True if menu.is_cache == "1" else False, 
                link=menu.path)
            menu_children = menu.children
            if menu_children and UserConstants.TYPE_DIR == menu.menu_type:
                rv.always_show = True
                rv.redirect = 'noRedirect'
                rv.children = cls.build_menus(menu_children)
            elif cls.is_menu_frame(menu):
                rv.meta = None
                rv_child = RouterVo()
                rv_child.path = menu.path
                rv_child.component = menu.component
                rv_child.name = menu.path.capitalize()
                rv_child.meta = RouterMetaVo(
                    title=menu.menu_name, 
                    icon=menu.icon, 
                    no_cache=True if menu.is_cache == "1" else False, 
                    link=menu.path)
                rv_children = [rv_child]
                rv.children = rv_children
            elif menu.parent_id == 0 and cls.is_inner_link(menu):
                rv.meta = RouterMetaVo(
                    title=menu.menu_name, 
                    icon=menu.icon
                )
                rv.path = "/"
                rv_child = RouterVo()
                rv_child.path = cls.inner_link_replace_each(menu.path)
                rv_child.component = UserConstants.INNER_LINK
                rv_child.name = menu.path.capitalize()
                rv_child.meta = RouterMetaVo(
                    title=menu.menu_name, 
                    icon=menu.icon, 
                    link=menu.path
                )
                rv_children = [rv_child]
                rv.children = rv_children
            routers.append(rv)
        return routers
    
    @classmethod
    def get_route_name(cls, menu: SysMenu) -> str:
        '''
        获取路由名称
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            str: 路由名称
        '''
        if cls.is_menu_frame(menu):
            return ""
        else:
            return menu.path.capitalize()
    
    @classmethod
    def get_router_path(cls, menu: SysMenu) -> str:
        '''
        获取路由路径
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            str: 路由路径
        '''
        router_path = menu.path
        if menu.parent_id != 0 and cls.is_inner_link(menu):
            router_path = cls.inner_link_replace_each(router_path)
        if menu.parent_id == 0 and menu.menu_type == UserConstants.TYPE_DIR \
            and UserConstants.NO_FRAME == menu.is_frame:
            router_path = "/" + menu.path
        elif cls.is_menu_frame(menu):
            router_path = "/"
        return router_path
        
    @classmethod
    def is_menu_frame(cls, menu: SysMenu) -> bool:
        '''
        是否为菜单内部跳转
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            bool: 是否为菜单内部跳转
        '''
        return menu.parent_id == 0 and UserConstants.TYPE_MENU == menu.menu_type \
            and menu.is_frame == UserConstants.NO_FRAME
    
    @classmethod
    def is_inner_link(cls, menu: SysMenu) -> bool:
        '''
        是否为内链
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            bool: 是否为内链
        '''
        return menu.is_frame == UserConstants.NO_FRAME and StringUtil.ishttp(menu.path)
    
    @classmethod
    def is_parent_view(cls, menu: SysMenu) -> bool:
        '''
        是否为parent_view
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            bool: 是否为parent_view
        '''
        return menu.parent_id != 0 and UserConstants.TYPE_DIR == menu.menu_type
       
    @classmethod
    def build_menu_tree(cls, menus:List[SysMenu]) -> List[SysMenu]:
        '''
        构建菜单树结构
        
        Args:
            menus(List[SysMenu]): 菜单列表
            
        Returns:
            List[SysMenu]: 菜单树结构
        '''
        return_list = []
        temp_list = []
        for menu in menus:
            temp_list.append(menu.menu_id)
        for menu in menus:
            if menu.parent_id not in temp_list:
                cls.recursion_fn(menus, menu)
                return_list.append(menu)
        if not return_list:
            return_list = menus
        return return_list
    
    @classmethod
    def build_menu_tree_select(cls, menus:List[SysMenu]):
        '''
        构建菜单下拉树结构
        
        Args:
            menus(List[SysMenu]): 菜单列表
            
        Returns:
            List[TreeSelect]: 菜单下拉树结构
        '''
        menu_tree = cls.build_menu_tree(menus)
        return list(map(TreeSelect.from_menu, menu_tree))
    
    @classmethod
    def select_menu_by_id(cls, menu_id) -> Optional[SysMenu]:
        '''
        根据菜单ID，查询菜单信息
        
        Args:
            menu_id(int): 菜单ID
            
        Returns:
            Optional[SysMenu]: 菜单信息
        '''
        return SysMenuMapper.select_menu_by_id(menu_id)
        
    @classmethod
    def has_child_by_menu_id(cls, menu_id) -> bool:
        '''
        判断是否有子节点
        
        Args:
            menu_id(int): 菜单ID
            
        Returns:
            bool: 是否有子节点
        '''
        num = SysMenuMapper.has_child_by_menu_id(menu_id)
        return num > 0
    
    @classmethod
    def check_menu_exist_role(cls, menu_id:int) -> bool:
        '''
        查询菜单使用数量
        
        Args:
            menu_id(int): 菜单ID
            
        Returns:
            bool: 是否有使用
        '''
        num = SysRoleMenuMapper.check_menu_exist_role(menu_id)
        return num > 0
    
    @classmethod
    def insert_menu(cls, menu:SysMenu) -> int:
        '''
        新增菜单
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            int: 新增菜单ID
        '''
        return SysMenuMapper.insert_menu(menu)
    
    @classmethod
    def update_menu(cls, menu:SysMenu) -> int:
        '''
        修改菜单
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            int: 修改菜单的数量
        '''
        return SysMenuMapper.update_menu(menu)
    
    @classmethod
    def delete_menu_by_id(cls, menu_id:int) -> int:
        '''
        根据菜单ID，删除菜单
        
        Args:
            menu_id(int): 菜单ID
            
        Returns:
            int: 删除菜单的数量
        '''
        return SysMenuMapper.delete_menu_by_id(menu_id)
    
    @classmethod
    def check_menu_name_unique(cls, menu:SysMenu) -> Literal["0","1"]:
        '''
        校验菜单名称是否唯一
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            Literal["0","1"]: 是否唯一, 0-唯一, 1-不唯一
        '''
        eo:SysMenu = SysMenuMapper.check_menu_name_unique(menu.menu_name, menu.parent_id)
        if eo and eo.menu_id != menu.menu_id:
            return UserConstants.Not_UNIQUE
        else:
            return UserConstants.UNIQUE
    
    @classmethod
    def get_component(cls, menu: SysMenu) -> Literal['InnerLink','ParentView','Layout']:
        '''
        获取组件类型
        
        Args:
            menu(SysMenu): 菜单信息
            
        Returns:
            Literal['InnerLink','ParentView','Layout']: 组件类型
        '''
        component = UserConstants.LAYOUT
        if menu.component and not cls.is_menu_frame(menu):
            component = menu.component
        elif not menu.component and menu.parent_id != 0 and cls.is_inner_link(menu):
            component = UserConstants.INNER_LINK
        elif not menu.component and cls.is_parent_view(menu):
            component = UserConstants.PARENT_VIEW
        return component

    @classmethod
    def get_child_perms(cls, menus:List[SysMenu], parent_id:int) -> List[SysMenu]:
        '''
        获取子菜单权限列表
        
        Args:
            menus(List[SysMenu]): 菜单列表
            parent_id(int): 父菜单ID
            
        Returns:
            List[SysMenu]: 子菜单列表
        '''
        return_list = []
        for menu in menus:
            if menu.parent_id == parent_id:
                cls.recursion_fn(menus, menu)
                return_list.append(menu)
        return return_list
    
    @classmethod
    def recursion_fn(cls, list:List[SysMenu], t:SysMenu):
        """
        递归菜单列表
        
        Args:
            list(List[SysMenu]): 菜单列表
            t(SysMenu): 父菜单信息
        """
        child_list = cls.get_child_list(list, t)
        t.children = child_list
        for t_child in child_list:
            if cls.has_child(list, t_child):
                cls.recursion_fn(list, t_child)

    @classmethod
    def get_child_list(cls, list:List[SysMenu], t:SysMenu) -> List[SysMenu]:
        """
        子菜单列表
        
        Args:
            list(List[SysMenu]): 菜单列表
            t(SysMenu): 父菜单信息
            
        Returns:
            List[SysMenu]: 子菜单列表
        """
        tlist = []
        for n in list:
            if n.parent_id is not None and n.parent_id == t.menu_id:
                tlist.append(n)
        return tlist

    @classmethod
    def has_child(cls, list:List[SysMenu], t:SysMenu) -> bool:
        """
        判断是否有子菜单
        
        Args:
            list(List[SysMenu]): 菜单列表
            t(SysMenu): 父菜单信息
            
        Returns:
            bool: 是否有子菜单
        """
        for n in list:
            if n.parent_id is not None and n.parent_id==t.menu_id:
                return True
        return False
    
    @classmethod
    def inner_link_replace_each(cls, path:str) -> str:
        '''
        内链域名特殊字符替换
        
        Args:
            path(str): 路径
            
        Returns:
            str: 路径
        '''
        path = path.replace(Constants.HTTP, "")
        path = path.replace(Constants.HTTPS, "")
        path = path.replace(Constants.WWW, "")
        path = path.replace(Constants.DOT, "/")
        return path
    