# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from owl_common.domain.entity import SysDictData
from owl_system.mapper.sys_dict_data import SysDictDataMapper


class SysDictDataService:
    
    @classmethod
    def select_dict_data_list(cls,dictdata: SysDictData) -> List[SysDictData]:
        '''
        根据条件，查询字典数据
        
        Args:
            dictdata: SysDictData 对象，包含查询条件
        
        Returns:
            List[SysDictData]: 字典数据列表
        '''
        return SysDictDataMapper.select_dict_data_list(dictdata)
    
    @classmethod
    def select_dict_label(cls,dict_type: str, dict_value: str) -> str:
        '''
        根据字典类型和字典键值，查询字典标签
        
        Args:
            dict_type: 字典类型
            dict_value: 字典键值
        
        Returns:
            str: 字典标签
        '''
        return SysDictDataMapper.select_dict_label(dict_type, dict_value)
    
    @classmethod
    def select_dict_data_by_id(cls,dict_code:int) -> SysDictData:
        '''
        根据字典数据ID，查询信息
        
        Args:
            dict_code: 字典数据ID
        
        Returns:
            SysDictData: 字典数据信息
        '''
        return SysDictDataMapper.select_dict_data_by_id(dict_code)
    
    @classmethod
    def delete_dict_data_by_ids(cls,dict_codes:List[int]) -> bool:
        '''
        批量删除字典数据信息
        
        Args:
            dict_codes: 字典数据ID列表
        
        Returns:
            bool: 操作结果
        '''
        return SysDictDataMapper.delete_dict_data_by_ids(dict_codes) > 0
    
    @classmethod
    def update_dict_data(cls,dict_data: SysDictData) -> bool:
        '''
        修改字典数据信息
        
        Args:
            dict_data: 字典数据信息
        
        Returns:
            bool: 操作结果
        '''
        return SysDictDataMapper.update_dict_data(dict_data) > 0 
    
    @classmethod
    def insert_dict_data(cls,dict_data: SysDictData) -> int:
        '''
        新增字典数据信息
        
        Args:
            dict_data: 字典数据信息
        
        Returns:
            int: 新增字典数据ID
        '''
        return SysDictDataMapper.insert_dict_data(dict_data)
    