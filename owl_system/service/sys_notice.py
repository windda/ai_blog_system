# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional

from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysNotice
from owl_system.mapper.sys_notice import SysNoticeMapper
from owl_admin.ext import db


class SysNoticeService:
    
    @classmethod
    def select_notice_by_id(cls,id:int) -> Optional[SysNotice]:
        """
        查询公告信息
        
        Args:
            id(int): 公告ID
            
        Returns:
            Optional[SysNotice]: 公告信息
        """
        return SysNoticeMapper.select_notice_by_id(id)
    
    @classmethod
    def select_notice_list(cls,query:SysNotice)-> List[SysNotice]:
        """
        查询公告列表
        
        Args:
            query(SysNotice): 包含查询条件的传输对象
            
        Returns:
            List[SysNotice]: 公告列表
        """
        return SysNoticeMapper.select_notice_list(query)
    
    @classmethod
    @Transactional(db.session)
    def insert_notice(cls,body:SysNotice) -> bool:
        """
        新增公告
        
        Args:
            body(SysNotice): 公告信息
            
        Returns:
            bool: 操作结果
        """
        flag = SysNoticeMapper.insert_notice(body)
        return flag > 0
    
    @classmethod
    @Transactional(db.session)
    def update_notice(cls,body:SysNotice) -> bool:
        """
        修改公告
        
        Args:
            body(SysNotice): 公告信息
            
        Returns:
            bool: 操作结果
        """
        return SysNoticeMapper.update_notice(body) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_notice_by_id(cls,id:int) -> bool:
        """
        删除公告
        
        Args:
            id(int): 公告ID
            
        Returns:
            int: 操作结果
        """
        return SysNoticeMapper.delete_notice_by_id(id) > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_notice_by_ids(cls,ids:List[int]) -> bool:
        """
        批量删除公告
        
        Args:
            ids(List[int]): 公告ID列表
            
        Returns:
            bool: 操作结果
        """
        return SysNoticeMapper.delete_notice_by_ids(ids) > 0