# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from types import NoneType
from typing import Callable, List, Optional
from datetime import datetime
from typing_extensions import Annotated
from pydantic import BeforeValidator, ValidationInfo

from owl_common.utils.base import DateUtil


def ids_to_list(value:str) -> Optional[List[int]]:
    """
    验证ids转换为字符串列表

    Args:
        value (str | NoneType): 传入参数

    Returns:
        Optional[List[str]]: 列表
    """
    return [int(i) for i in value.split(',')]


def to_datetime(format=DateUtil.YYYY_MM_DD_HH_MM_SS) \
        -> Callable[[str|NoneType, ValidationInfo], datetime|NoneType]:
    """
    根据指定格式，验证datetime

    Args:
        format (str): 日期格式. Defaults to '%Y-%m-%d %H:%M:%S'.
    """
    def validate_datetime(value:str|NoneType, info:ValidationInfo) \
            -> datetime|NoneType:
        """
        验证datetime

        Args:
            value (str | NoneType): 传入参数
            info (ValidationInfo): pydantic的验证信息

        Raises:
            ValueError: 日期格式错误

        Returns:
            _type_: datetime
        """
        if value:
            if isinstance(value, str):
                return datetime.strptime(value, format)
            elif isinstance(value, datetime):
                return value
            raise ValueError(f"Invalid datetime format: {value}")
        else:
            return None
    return validate_datetime


def str_to_int(value:str|NoneType, info:ValidationInfo) \
        -> int:
    """
    验证str是否为整数，并转换为整数

    Args:
        value (str | NoneType): 传入参数
        info (ValidationInfo): pydantic的验证信息

    Raises:
        ValueError: 字符串格式错误

    Returns:
        int: 整数
    """
    if value:
        if isinstance(value, str):
            if value.isdecimal():
                return int(value)
            else:
                raise ValueError(f"Invalid str format, cannot convert to int: {value}")
    return value


def int_to_str(value:int|NoneType)-> str:
    if isinstance(value, int):
        return str(value)
    else:
        return value


ids_convertor = Annotated[List[int],BeforeValidator(ids_to_list)]