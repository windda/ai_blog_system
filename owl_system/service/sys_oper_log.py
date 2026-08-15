# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional

from owl_system.domain.entity import SysOperLog
from owl_system.mapper import SysOperLogMapper


class SysOperLogService:
    
    @classmethod
    def insert_operlog(cls, body: SysOperLog) -> int:
        '''
        新增操作日志
        
        Args:
            body (SysOperLog): 操作日志对象
        
        Returns:
            int: 操作日志id
        '''
        return SysOperLogMapper.insert_operlog(body)
    
    @classmethod
    def select_operlog_list(cls, query: Optional[SysOperLog])-> List[SysOperLog]:
        '''
        查询系统操作日志列表
        
        Args:
            query (SysOperLog|NoneType): 包含查询条件的传输对象
        
        Returns:
            List[SysOperLog]: 操作日志列表
        '''
        return SysOperLogMapper.select_operlog_list(query)
    
    @classmethod
    def delete_operlog_by_ids(cls, ids: list[int]) -> int:
        '''
        批量删除系统操作日志
        
        Args:
            ids (list[int]): 操作日志id列表
        
        Returns:
            int: 删除的行数
        '''
        return SysOperLogMapper.delete_operlog_by_ids(ids)
    
    @classmethod
    def clean_operlog(cls) -> int:
        '''
        清空操作日志
        
        Returns:
            int: 清空的行数
        '''
        return SysOperLogMapper.clean_operlog()
    
    @classmethod
    def select_operlog_by_id(cls, id:int) -> Optional[SysOperLog]:
        '''
        查询操作日志详细信息
        
        Args:
            id (int): 操作日志id
        
        Returns:
            Optional[SysOperLog]: 操作日志信息
        '''
        return SysOperLogMapper.select_operlog_by_id(id)
        