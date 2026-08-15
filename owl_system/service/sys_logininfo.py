# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List

from owl_system.mapper import SysLogininforMapper
from owl_system.domain.entity import SysLogininfor


class SysLogininforService:
    
    @classmethod
    def insert_logininfor(cls, logininfor: SysLogininfor) -> int:
        '''
        新增登录日志
        
        Args:
            logininfor(SysLogininfor): 登录日志信息 
        
        Returns:
            int: 新增的记录的id
        '''
        flag = SysLogininforMapper.insert_logininfor(logininfor)
        return flag
    
    @classmethod
    def select_logininfor_list(cls, query: SysLogininfor) -> List[SysLogininfor]:
        '''
        查询登录日志列表
        
        Args:
            query(SysLogininfor): 查询条件 
        
        Returns:
            List[SysLogininfor]: 登录日志列表
        '''
        return SysLogininforMapper.select_logininfor_list(query)
    
    @classmethod
    def delete_logininfor_by_ids(cls, ids: List[int]) -> int:
        '''
        根据ids删除登录日志
        
        Args:
            ids(List[int]): 日志id列表 
        
        Returns:
            int: 删除的记录数
        '''
        return SysLogininforMapper.delete_logininfor_by_ids(ids)
    
    @classmethod
    def clean_logininfor(cls) -> int:
        '''
        清空登录日志
        
        Returns:
            int: 清空的记录数
        '''
        return SysLogininforMapper.clean_logininfor()
