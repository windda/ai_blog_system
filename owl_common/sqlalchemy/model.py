
from collections import UserList
from math import ceil
from typing import List, Set, Type, TypeVar
import typing as t
from flask import abort
from flask_sqlalchemy.model import Model
from flask_sqlalchemy.pagination import Pagination as _Pagination
from sqlalchemy import Column, ScalarSelect
from sqlalchemy.orm.attributes import InstrumentedAttribute

from owl_common.base.model import BaseEntity, DbValidatorContext


T = TypeVar('T', bound=BaseEntity)


class ColumnEntityList(UserList[Column]):
    """
    字段名称列表类
    """
    
    context_key = "db_columns_alias"
    
    def __init__(self, clz:type[Model], names:Set, alia_prefix:bool=True):
        self._clz = clz
        self._names = names
        self._alia_prefix = alia_prefix
        
        super(ColumnEntityList, self).__init__(self._columns())

    def _columns(self)-> List[Column]:
        """
        获取字段列表
        
        Returns:
            List[Column]: 字段列表
        """
        columns = []
        for name in self._names:
            if not hasattr(self._clz, name):
                raise AttributeError(
                    f"column {name} not found in {self._clz.__name__}"
                )
            column:InstrumentedAttribute = getattr(self._clz, name)
            if not isinstance(column, InstrumentedAttribute):
                raise AttributeError(
                    f"column {name} is not a column in {self._clz.__name__}"
                )
            if self._alia_prefix:
                label_name = self.to_label(name)
                columns.append(column.label(label_name))
            else:
                columns.append(column)
            
        return columns
    
    def to_label(self, name:str) -> str:
        """
        给字段列表添加别名前缀，生成标签名
        
        Args:
            name (str): 字段名
        
        Returns:
            str: 标签名
        """
        return "{}_{}".format(self._clz.__name__, name)
    
    def to_field(self, label:str) -> str:
        """
        从标签名删除别名前缀，还原字段名
        
        Args:
            label (str): 标签名
        
        Returns:
            str: 字段名
        """
        alias_prefix = self._clz.__name__ + "_"
        return label[len(alias_prefix):]
    
    def check_prefix(self, label:str) -> bool:
        """
        检查标签名是否以表名开头
        
        Args:
            label (str): 标签名
        
        Returns:
            bool: 是否以表名开头
        """
        alias_prefix = self._clz.__name__ + "_"
        return label.startswith(alias_prefix)
    
    def cast(self, row, to: Type[T]) -> T:
        """
        获取字段值，并转换为指定数据模型对象
        
        Args:
            row (dict): 数据库查询结果
            to (Type[T]): 数据模型类
        
        Returns:
            T: 数据模型对象
        """
        data = to.model_validate(
            row,
            from_attributes=True,
            context=DbValidatorContext(col_entity_list=self)
        )
        return data
    
    def append_scalar(self, scalar:ScalarSelect):
        """
        追加一个标量字段
        
        Args:
            scalar (ScalarSelect): 标量字段
        """
        if self._alia_prefix:
            self._names.add(self.to_label(scalar.name))
        else:
            self._names.add(scalar.name)
        self.append(scalar)
        
  