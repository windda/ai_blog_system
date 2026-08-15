# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Literal, Optional

from owl_common.constant import UserConstants
from owl_common.exception import ServiceException
from owl_system.domain.entity import SysPost
from owl_system.domain.po import SysPostPo
from owl_system.mapper.sys_post import SysPostMapper
from owl_system.mapper.sys_user_post import SysUserPostMapper


class SysPostService:

    @classmethod
    def select_post_list(cls, query:SysPost) -> List[SysPost]:
        """
        查询岗位信息列表
        
        Args:
            query(SysPost): 包含查询条件的传输对象
        
        Returns:
            List[SysPost]: 岗位信息列表
        """
        return SysPostMapper.select_post_list(query)

    @classmethod
    def select_post_all(cls) -> List[SysPost]:
        """
        查询所有岗位
        
        Returns:
            List[SysPost]: 所有岗位信息列表
        """
        return SysPostMapper.select_post_all()

    @classmethod
    def select_post_by_id(cls, id:int) -> Optional[SysPost]:
        """
        通过岗位ID，查询岗位信息
        
        Args:
            id(int): 岗位ID
        
        Returns:
            Optional[SysPost]: 岗位信息
        """
        return SysPostMapper.select_post_by_id(id)

    @classmethod
    def select_post_list_by_user_id(cls, user_id:int) -> List[int]:
        """
        根据用户ID，查询岗位选择框
        
        Args:
            user_id(int): 用户ID
        
        Returns:
            List[int]: 岗位ID列表
        """
        return SysPostMapper.select_post_list_by_user_id(user_id)

    @classmethod
    def check_post_name_unique(cls, body:SysPost) -> Literal["0","1"]:
        """
        校验岗位名称是否唯一
        
        Args:
            body(SysPost): 包含岗位名称的传输对象
        
        Returns:
            str: 唯一或不唯一, 0-唯一, 1-不唯一
        """
        post_id = -1 if body.post_id is None else body.post_id
        eo:SysPost = SysPostMapper.check_post_name_unique(body.post_name)
        if eo is not None and eo.post_id != post_id:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE

    @classmethod
    def check_post_code_unique(cls, body:SysPost) -> Literal["0","1"]:
        """
        校验岗位编码是否唯一
        
        Args:
            body(SysPost): 包含岗位编码的传输对象
        
        Returns:
            str: 唯一或不唯一, 0-唯一, 1-不唯一
        """
        post_code = -1 if body.post_code is None else body.post_code
        eo:SysPostPo = SysPostMapper.check_post_code_unique(body.post_code)
        if eo is not None and eo.post_code != post_code:
            return UserConstants.NOT_UNIQUE
        return UserConstants.UNIQUE

    @classmethod
    def count_user_post_by_id(cls, id:int) -> int:
        """
        根据岗位ID，查询岗位使用数量
        
        Args:
            id(int): 岗位ID
        
        Returns:
            int: 岗位使用数量
        """
        return SysUserPostMapper.count_user_post_by_id(id)

    @classmethod
    def delete_post_by_id(cls, id:int) -> int:
        """
        删除岗位信息
        
        Args:
            id(int): 岗位ID
        
        Returns:
            int: 删除的数量
        """
        return SysPostMapper.delete_post_by_id(id)

    @classmethod
    def delete_post_by_ids(cls, ids:List[int]) -> int:
        """
        批量删除岗位信息
        
        Args:
            ids(List[int]): 岗位ID列表
        
        Returns:
            int: 删除的数量
        """
        for id in ids:
            po:SysPostPo = cls.select_post_by_id(id)
            if cls.count_user_post_by_id(id) > 0:
                raise ServiceException(f"{po.post_name}已分配,不能删除")
        return SysPostMapper.delete_post_by_ids(ids)

    @classmethod
    def insert_post(cls, body:SysPost) -> int:
        """
        新增岗位信息
        
        Args:
            body(SysPost): 包含岗位信息的传输对象
        
        Returns:
            int: 新增的岗位ID
        """
        return SysPostMapper.insert_post(body)

    @classmethod
    def update_post(cls, body:SysPost) -> int:
        """
        修改岗位信息
        
        Args:
            body(SysPost): 包含岗位信息的传输对象
        
        Returns:
            int: 修改的数量
        """
        return SysPostMapper.update_post(body)