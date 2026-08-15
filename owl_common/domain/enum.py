# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from enum import Enum


class BusinessStatus(int,Enum):
    
    """
    业务操作状态
    """
    
    # 正常
    SUCCESS = 0

    # 异常
    FAIL = 1
    

class BusinessType(int, Enum):
    
    """
    业务操作类型
    """
    
    # 其它
    OTHER = 0

    # 新增
    INSERT = 1

    # 修改
    UPDATE = 2

    # 删除
    DELETE = 3

    # 授权
    GRANT = 4

    # 导出
    EXPORT = 5

    # 导入
    IMPORT = 6 

    # 强退
    FORCE = 7

    # 生成代码
    GENCODE = 8
    
    # 清空数据
    CLEAN = 9


class OperatorType(int, Enum):
    
    """
    操作人类别
    """
    
    # 其它
    OTHER = 0

    # 后台用户
    MANAGE = 1

    # 手机端用户
    MOBILE = 2


class UserStatus(Enum):
    
    """
    用户状态
    """
    
    # 正常
    OK = 0

    # 停用
    DISABLE = 1

    # 删除
    DELETED = 2
    

class DataPermEnum(Enum):
    
    """
    数据权限枚举
    """
    
    # 全部数据权限
    ALL = '1'  
    
    # 自定义数据权限
    CUSTOM = '2' 
    
    # 仅本部门及以下数据权限
    DEPT_AND_CHILD = '3'  
    
    # 本部门数据权限
    DEPT = '4'  
    
    # 仅本部门及以下数据权限+自定义数据权限
    DEPT_AND_CHILD_AND_CUSTOM = '5'  


class LimitType(Enum):
    
    """
    限流类型
    """
    
    # 默认策略全局限流
    DEFAULT = "default"
    
    # 根据请求者IP进行限流
    IP = "ip"
