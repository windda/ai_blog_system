# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Literal, Optional

from owl_common.constant import UserConstants
from owl_common.exception import ServiceException
from owl_common.sqlalchemy.transaction import Transactional
from owl_common.domain.entity import SysRole, SysUser
from owl_common.utils import security_util
from owl_common.utils.base import LogUtil, StringUtil
from owl_framework.descriptor.datascope import DataScope
from owl_system.domain.entity import SysPost, SysUserPost, SysUserRole
from owl_system.mapper import SysUserMapper
from owl_system.mapper.sys_post import SysPostMapper
from owl_system.mapper.sys_role import SysRoleMapper
from owl_system.mapper.sys_user_post import SysUserPostMapper
from owl_system.mapper.sys_user_role import SysUserRoleMapper
from owl_admin.ext import db
from owl_system.service.sys_config import SysConfigService


class SysUserService:
    
    @classmethod
    @DataScope(dept=True, user=True)
    def select_user_list(cls, query: SysUser) -> List[SysUser]:
        """
        查询用户列表

        Args:
            query (SysUser): 包含查询条件的传输对象

        Returns:
            List[SysUser]: 用户列表
        """
        return SysUserMapper.select_user_list(query)
        
    @classmethod
    @DataScope(dept=True, user=True)
    def select_allocated_list(cls, query: SysUser) -> List[SysUser]:
        """
        查询已分配用户列表

        Args:
            query (SysUser): 包含查询条件的传输对象

        Returns:
            List[SysUser]: 已分配用户列表
        """
        return SysUserMapper.select_allocated_list(query)
        
    @classmethod
    @DataScope(dept=True, user=True)
    def select_unallocated_list(cls, query: SysUser) -> List[SysUser]:
        """
        查询未分配用户列表

        Args:
            query (SysUser): 包含查询条件的传输对象

        Returns:
            List[SysUser]: 已分配用户列表
        """
        return SysUserMapper.select_unallocated_list(query)
        
    @classmethod
    def select_user_by_user_name(cls, user_name: str) -> Optional[SysUser]:
        """
        根据用户名，查询用户

        Args:
            user_name (str): 用户名

        Returns:
            Optional[SysUser]: 用户信息
        """
        return SysUserMapper.select_user_by_user_name(user_name)
        
    @classmethod
    def select_user_by_id(cls, user_id: int) -> Optional[SysUser]:
        """
        根据用户ID，查询用户

        Args:
            user_id (int): 用户ID

        Returns:
            Optional[SysUser]: 用户信息
        """
        return SysUserMapper.select_user_detail_by_id(user_id)
    
    @classmethod
    def select_user_role_group(cls, user_name: str) -> str:
        """
        查询用户角色组
        
        Args:
            user_name (str): 用户名
        
        Returns:
            str: 角色组
        """
        eos:List[SysRole] = SysRoleMapper.select_role_list_by_user_name(user_name)
        if not eos:
            return StringUtil.EMPTY
        return ",".join([eo.role_name for eo in eos])
    
    @classmethod
    def select_user_post_group(cls, user_name: str)->str:
        """
        查询用户岗位组

        Args:
            user_name (str): 用户名

        Returns:
            str: 岗位组
        """
        eos:List[SysPost] = SysPostMapper.select_posts_by_user_name(user_name)
        if not eos:
            return StringUtil.EMPTY
        return ",".join([eo.post_name for eo in eos])
    
    @classmethod
    def check_user_name_unique(cls, user: SysUser) -> Literal["0","1"]:
        """
        校验用户名是否唯一

        Args:
            user (SysUser): 用户信息

        Returns:
            str: 唯一标识符, 0-唯一, 1-不唯一
        """
        user_name = -1 if user.user_name is None else user.user_name
        num = SysUserMapper.check_user_name_unique(user_name)
        if num > 0:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE
    
    @classmethod
    def check_phone_unique(cls, user: SysUser) -> Literal["0","1"]:
        """
        校验手机号是否唯一

        Args:
            user (SysUser): 用户信息

        Returns:
            str: 唯一标识符, 0-唯一, 1-不唯一
        """
        user_id = -1 if user.user_id is None else user.user_id
        eo:SysUser = SysUserMapper.check_phone_unique(user.phonenumber)
        if eo and eo.user_id != user_id:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE
    
    @classmethod
    def check_email_unique(cls, user: SysUser) -> Literal["0","1"]:
        """
        校验邮箱是否唯一

        Args:
            user (SysUser): 用户信息

        Returns:
            str: 唯一标识符, 0-唯一, 1-不唯一
        """
        user_email = -1 if user.email is None else user.email
        eo:SysUser = SysUserMapper.check_email_unique(user.email)
        if eo and eo.email != user_email:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE
    
    @classmethod
    def check_user_allowed(cls, user: SysUser):
        """
        检查用户是否允许操作

        Args:
            user (SysUser): 用户信息

        Raises:
            ServiceException: 超级管理员用户不允许操作

        """
        if user.is_admin() and security_util.get_user_id() != user.user_id:
            raise ServiceException("不允许操作超级管理员用户")
    
    @classmethod
    def check_user_data_scope(cls, user_id: Optional[int]):
        """
        检查用户数据权限

        Args:
            user_id (Optional[int]): 用户ID

        Raises:
            ServiceException: 无权限访问用户数据
        """
        if not security_util.login_user_is_admin():
            if user_id and user_id == security_util.get_user_id():
                return
            raise ServiceException("没有权限访问用户数据")
            
    @classmethod
    @Transactional(db.session)
    def insert_user(cls, user: SysUser) -> bool:
        """
        新增用户

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        last_pid = SysUserMapper.insert_user(user)
        user.user_id = last_pid
        cls.insert_user_post_by_user(user)
        cls.insert_user_role_by_user(user)
        return last_pid > 0
    
    @classmethod
    def register_user(cls, user: SysUser) -> bool:
        """
        注册用户

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        flag = SysUserMapper.insert_user(user)
        return flag > 0
    
    @classmethod
    def update_user(cls, user: SysUser) -> bool:
        """
        更新用户

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.update_user(user) > 0

    @classmethod
    @Transactional(db.session)
    def insert_user_auth(cls, user_id:int, role_ids:List[int]):
        """
        新增用户角色
        
        Args:
            user_id: 用户id
            role_ids: 角色id列表
        """
        SysUserMapper.delete_user_role_by_user_id(user_id)
        cls.insert_user_role(user_id, role_ids)
    
    @classmethod
    def delete_users_by_id(cls, id: int) -> bool:
        """
        根据用户ID，删除用户

        Args:
            id (int): 用户ID

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.delete_user_by_id(id) > 0
        
    @classmethod
    def delete_users_by_ids(cls, ids: List[int]) -> bool:
        """
        根据用户ID列表，批量删除用户

        Args:
            ids (List[int]): 用户ID列表

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.delete_user_by_ids(ids) > 0
    
    @classmethod
    def update_user_status(cls, user: SysUser) -> bool:
        """
        更新用户状态

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        result = SysUserMapper.update_user(user)
        return result > 0 if result else False

    @classmethod
    def update_user_profile(cls, user: SysUser) -> bool:
        """
        更新用户个人信息

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.update_user(user) > 0

    @classmethod
    def update_user_avatar(cls, user_name:str, avatar:str) -> bool:
        """
        更新用户头像

        Args:
            user_name (str): 用户名
            avatar (str): 头像

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.update_user_avatar(user_name, avatar) > 0

    @classmethod
    def update_profile(cls, user_id: int, nick_name: str = None, introduction: str = None,
                       email: str = None, phonenumber: str = None, avatar: str = None):
        """更新个人资料（前台个人中心用）"""
        user = SysUserMapper.select_user_detail_by_id(user_id)
        if not user:
            raise ServiceException("用户不存在")
        if nick_name is not None:
            user.nick_name = nick_name
        if introduction is not None:
            user.remark = introduction
        if email is not None:
            user.email = email
        if phonenumber is not None:
            user.phonenumber = phonenumber
        if avatar is not None:
            user.avatar = avatar
        SysUserMapper.update_user(user)
        db.session.commit()

    @classmethod
    def update_password(cls, user_id: int, old_password: str, new_password: str):
        """修改密码（前台个人中心用）"""
        user = SysUserMapper.select_user_detail_by_id(user_id)
        if not user:
            raise ServiceException("用户不存在")
        if not security_util.matches_password(old_password, user.password):
            raise ServiceException("旧密码错误")
        new_encrypted = security_util.encrypt_password(new_password)
        user.password = new_encrypted
        SysUserMapper.update_user(user)
        db.session.commit()

    @classmethod
    def reset_user_pwd(cls, username:str, password:str) -> bool:
        """
        重置用户密码

        Args:
            username (str): 用户名
            password (str): 密码

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.reset_user_pwd(username, password) > 0

    @classmethod
    def reset_pwd(cls, user: SysUser) -> bool:
        """
        重置用户密码

        Args:
            user (SysUser): 用户信息

        Returns:
            bool: 操作结果
        """
        return SysUserMapper.update_user(user) > 0
  
    @classmethod
    def insert_user_role_by_user(cls, user: SysUser):
        """
        新增用户角色
        
        Args:
            user: 用户信息
        """
        cls.insert_user_role(user.user_id, user.role_ids)
    
    @classmethod
    @Transactional(db.session)
    def insert_user_role(cls, user_id:int, role_ids:List[int]):
        """
        新增用户角色
        
        Args:
            user_id: 用户id
            role_ids: 角色id列表
        """
        if role_ids:
            lists = [
                SysUserRole(user_id=user_id, role_id=role_id)
                for role_id in role_ids
                ]
            SysUserRoleMapper.batch_user_role(lists)
    
    @classmethod
    def insert_user_post_by_user(cls, user: SysUser):
        """
        新增用户岗位
        
        Args:
            user: 用户信息
        """
        cls.insert_user_post(user.user_id, user.post_ids)
        
    @classmethod
    @Transactional(db.session)
    def insert_user_post(cls, user_id:int, post_ids:List[int]):
        """
        新增用户岗位
        
        Args:
            user_id: 用户id
            post_ids: 岗位id列表
        """
        if post_ids:
            lists = [
                SysUserPost(user_id=user_id, post_id=post_id)
                for post_id in post_ids
                ]
            SysUserPostMapper.batch_user_post(lists)

    @classmethod
    @Transactional(db.session)
    def update_user_roles(cls, user_id: int, role_ids: List[int]) -> bool:
        """
        更新用户角色
        
        Args:
            user_id: 用户id
            role_ids: 角色id列表
        
        Returns:
            bool: 操作结果
        """
        SysUserRoleMapper.delete_user_role_by_user_id(user_id)
        cls.insert_user_role(user_id, role_ids)
        return True
                
    @classmethod
    def import_user(cls, users: List[SysUser],is_update:bool=False) -> str:
        """
        导入用户

        Args:
            users (List[SysUser]):  用户列表
            is_update (bool): 是否更新

        Returns:
            str: 导入消息结果
        """
        if not users:
            raise ServiceException("导入用户不能为空")
        success_count = 0
        fail_count = 0
        success_msg = ""
        fail_msg = ""
        default_password = SysConfigService.select_config_by_key("sys.user.initPassword")
        for user in users:
            try:
                dto = SysUserMapper.select_user_by_user_name(user.user_name)
                if not dto:
                    user.password = security_util.encrypt_password(default_password)
                    user.create_by_user(security_util.get_user_id())
                    cls.insert_user(user)
                    success_count += 1
                    success_msg += f"<br/> 第{success_count}个账号，导入成功：{user.user_name}"
                elif is_update:
                    user.update_by_user(security_util.get_user_id())
                    cls.update_user(user)
                    success_count += 1
                    success_msg += f"<br/> 第{success_count}个账号，更新成功：{user.user_name}"
                else:
                    fail_count += 1
                    fail_msg += f"<br/> 第{fail_count}个账号，已存在：{user.user_name}"
            except Exception as e:
                fail_count += 1
                fail_msg += f"<br/> 第{fail_count}个账号，导入失败：{user.user_name}，\
                    原因：{e.__class__.__name__}"
                LogUtil.logger.error(f"导入用户失败，原因：{e}")
        if fail_count > 0:
            if success_msg:
                fail_msg = f"导入成功{success_count}个，失败{fail_count}个。{success_msg} \
                    <br/>" + fail_msg
            else:
                fail_msg = f"导入成功{success_count}个，失败{fail_count}个。{fail_msg}"
            raise ServiceException(fail_msg)
        else:
            success_msg = f"恭喜您，数据已全部导入成功！共 {success_count} 条，数据如下：" \
                + success_msg
        return success_msg
