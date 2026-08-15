# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from itertools import groupby
from types import NoneType
from typing import List
from flask import Flask
from pydantic_core import to_json

from owl_common.constant import Constants, UserConstants
from owl_common.base.signal import app_completed
from owl_common.domain.entity import SysDictData, SysDictType
from owl_common.sqlalchemy.transaction import Transactional
from owl_common.exception import ServiceException
from owl_system.mapper import SysDictDataMapper,SysDictTypeMapper
from owl_admin.ext import redis_cache,db
from .. import reg


class SysDictTypeService:
    
    @classmethod
    def init(cls):
        '''
        初始化字典缓存
        '''
        cls.loading_dict_cache()
    
    @classmethod
    def loading_dict_cache(cls):
        '''
        加载字典缓存
        '''
        dict_data: SysDictData = SysDictData(status="0")
        dict_data_list = SysDictDataMapper.select_dict_data_list(dict_data)
        dict_data_list.sort(key=lambda x: x.dict_type)
        dict_data_map = groupby(dict_data_list, lambda x: x.dict_type)
        for key, group in dict_data_map:
            DictCacheUtil.set_dict_cache(key, list(group))
        
    @classmethod
    def clear_dict_cache(cls):
        '''
        清除字典缓存
        '''
        DictCacheUtil.clear_dict_cache()
    
    @classmethod
    def select_dict_data_by_type(cls, dict_type:str) -> List[SysDictData]:
        '''
        根据字典类型，查询字典数据列表
        
        Args:
            dict_type(str): 字典类型
        
        Returns:
            List[SysDictData]: 字典数据列表
        '''
        eos:List[SysDictData] = SysDictDataMapper.select_dict_data_by_type(dict_type)
        return eos
    
    @classmethod
    def select_dict_type_list(cls, dictype:SysDictType) -> List[SysDictType]:
        '''
        根据字典类型，查询字典类型列表
        
        Args:
            dictype(SysDictType): 字典类型
        
        Returns:
            List[SysDictType]: 字典类型列表
        '''
        eos:List[SysDictType] = SysDictTypeMapper.select_dict_type_list(dictype)
        return eos
    
    @classmethod
    def select_dict_type_all(cls) -> List[SysDictType]:
        '''
        所有字典类型
        
        Returns:
            List[SysDictType]: 字典类型列表
        '''
        eos:List[SysDictType] = SysDictTypeMapper.select_dict_type_all()
        return eos
    
    @classmethod
    def select_dict_type_by_id(cls, dict_id:int) -> SysDictType | NoneType:
        '''
        根据字典id，查询字典类型
        
        Args:
            dict_id(int): 字典id
        
        Returns:
            SysDictType | NoneType: 字典类型
        '''
        return SysDictTypeMapper.select_dict_type_by_id(dict_id)
    
    @classmethod
    def select_dict_type_by_type(cls, dict_type:str) -> SysDictType:
        '''
        根据字典类型，查询字典类型信息
        
        Args:
            dict_type(str): 字典类型
        
        Returns:
            SysDictType: 字典类型
        '''
        return SysDictTypeMapper.select_dict_type_by_type(dict_type)
    
    @classmethod
    def insert_dict_type(cls, dictype:SysDictType) -> bool:
        '''
        新增字典类型
        
        Args:
            dictype(SysDictType): 字典类型
        
        Returns:
            bool: 操作结果
        '''
        flag = SysDictTypeMapper.insert_dict_type(dictype)
        if flag and flag > 0:
            DictCacheUtil.set_dict_cache(dictype.dict_type, [])
        return True
    
    @classmethod
    @Transactional(db.session)
    def update_dict_type(cls, dictype:SysDictType) -> bool:
        '''
            修改字典类型
        '''
        old_dictype = SysDictTypeMapper.select_dict_type_by_id(
            dictype.dict_id
        )
        SysDictDataMapper.update_dict_data_type(
            old_dictype.dict_type, dictype.dict_type
        )
        num = SysDictTypeMapper.update_dict_type(dictype)
        flag = num > 0
        if flag:
            datas:List[SysDictData] = SysDictDataMapper \
                .select_dict_data_by_type(dictype.dict_type)
            DictCacheUtil.set_dict_cache(dictype.dict_type, datas)
        return flag 
    
    @classmethod
    @Transactional(db.session)
    def delete_dict_type_by_ids(cls, ids:List[int]) -> bool:
        '''
            批量删除字典类型
        '''
        for id in ids:
            dict_type = cls.select_dict_type_by_id(id)
            if dict_type is None:
                continue
            if SysDictDataMapper.select_dict_data_count_by_type(dict_type.dict_type) > 0:
                raise ServiceException("{}已分配,不能删除".format(dict_type.dict_type))
            SysDictTypeMapper.delete_dict_type_by_id(id)
            DictCacheUtil.remove_dict_cache(dict_type.dict_type)
        return True
    
    @classmethod
    def check_dict_type_unique(cls, dict_type:SysDictType):
        '''
            检查字典类型是否唯一
        '''
        eo:SysDictType = SysDictTypeMapper.check_dict_type_unique(dict_type.dict_type)
        if eo and dict_type.dict_id != eo.dict_id:
            return UserConstants.NOT_UNIQUE
        else:
            return UserConstants.UNIQUE
    
    @classmethod
    def reset_dict_type_cache(cls):
        '''
            重置字典缓存
        '''
        cls.clear_dict_cache()
        cls.loading_dict_cache()


class DictCacheUtil:
    
    @classmethod
    def clear_dict_cache(cls):
        pass
    
    @classmethod
    def get_cache_key(cls, key:str):
        return Constants.SYS_DICT_KEY + key
    
    @classmethod
    def remove_dict_cache(cls, key:str):
        redis_cache.delete(cls.get_cache_key(key))
    
    @classmethod
    def get_dict_value_sep(cls, dict_type, dict_label, sep):
        pass
    
    @classmethod
    def get_dict_label_sep(cls, dict_type, dict_value, sep):
        pass
    
    @classmethod
    def get_dict_value(cls, dict_type, dict_label):
        pass
    
    @classmethod
    def get_dict_label(cls, dict_type, dict_value):
        pass
    
    @classmethod
    def set_dict_cache(cls, key, dict_data_list:List[SysDictData]):
        redis_cache.set(cls.get_cache_key(key), to_json(dict_data_list))


@app_completed.connect_via(reg.app)
def init(sender:Flask):
    '''
    初始化操作
    
    Args:
        sender (Flask): 消息发送者
    '''
    with sender.app_context():
        SysDictTypeService.init()

