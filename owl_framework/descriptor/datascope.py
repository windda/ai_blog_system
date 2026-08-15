# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from enum import Enum
from functools import wraps
from typing import Any, Literal
from flask import g
from pydantic import ConfigDict, Field, validate_call
from pydantic.dataclasses import dataclass
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import or_
from sqlalchemy import func

from owl_common.base.model import CriterianMeta
from owl_common.descriptor.validator import ValidatorScopeFunction
from owl_common.base.schema_vo import BaseEntity
from owl_common.domain.entity import LoginUser, SysUser
from owl_common.utils import security_util as SecurityUtil
from owl_system.domain.po import SysDeptPo, SysRoleDeptPo, SysUserPo


class DataScopeEnum(Enum):
    
    ALL = "1"
    
    CUSTOM = "2"
    
    DEPT = "3"
    
    DEPT_AND_CHILD = "4"
    
    SELF = "5"
    
    
@dataclass
class DataScope:
    """
    数据权限范围
    """
    model_config = ConfigDict(
        frozen = True,
        extra = "forbid",
        strict = True,
        populate_by_name = True
    )
    
    # DATA_SCOPE: Literal["data_scope"] = Field(init=False, exclude=True, repr=False)
    
    dept : bool = True
    user : bool = False
    
    
    def __call__(self, func) -> Any:
        
        vsfunc = ValidatorScopeFunction(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            unbound_model = vsfunc.unbound_model
            if unbound_model:
                key,_ = unbound_model
                # bo = kwargs.get(key)
                # self.handle_data_scope(bo)
            return vsfunc(*args, **kwargs)
        return wrapper

    def handle_data_scope(self, bo: BaseEntity):
        """
        处理数据权限范围
        
        Args:
            bo (BaseEntity): 校验对象
        """
        login_user:LoginUser = SecurityUtil.get_login_user()
        if login_user:
            current_user:SysUser = login_user.user
            if not SecurityUtil.is_admin(login_user.user_id):
                self.filter_data_scope(current_user)
    
    def filter_data_scope(self,user: SysUser):
        """
        过滤数据权限范围
        
        Args:
            bo (BaseEntity): 校验对象
            user (SysUser): 当前用户
        """
        criterian_meta:CriterianMeta = g.criterian_meta
        
        criterions = []
        for role in user.roles:
            if role.data_scope == DataScopeEnum.ALL.value:
                # 全部数据权限
                criterions = []
                break
            elif role.data_scope == DataScopeEnum.CUSTOM.value:
                # 自定义数据权限
                subquery = SysRoleDeptPo.query(SysRoleDeptPo.dept_id) \
                    .filter(
                        SysRoleDeptPo.role_id == role.role_id
                        ).subquery()
                if self.dept is True:
                    criterion = SysDeptPo.dept_id.in_(subquery)
                elif isinstance(self.dept, AliasedClass):
                    criterion = self.dept.dept_id.in_(subquery)
                if criterion:
                    criterions.append(criterion)
            elif role.data_scope == DataScopeEnum.DEPT.value:
                # 本部门数据权限
                if self.dept is True:
                    criterion = SysDeptPo.dept_id == user.dept_id
                elif isinstance(self.dept, AliasedClass):
                    criterion = self.dept.dept_id == user.dept_id
                if criterion:
                    criterions.append(criterion)
            elif role.data_scope == DataScopeEnum.DEPT_AND_CHILD.value:
                # 本部门及子部门数据权限
                subquery = SysDeptPo.query(SysDeptPo.dept_id) \
                    .filter(
                        or_(
                            SysDeptPo.dept_id == user.dept_id,
                            func.find_in_set(user.dept_id, SysDeptPo.ancestors)
                            )
                        ).subquery()
                if self.dept is True:
                    criterion = SysDeptPo.dept_id.in_(subquery)
                elif isinstance(self.dept, AliasedClass):
                    criterion = self.dept.dept_id.in_(subquery)
                if criterion:
                    criterions.append(criterion)
            elif role.data_scope == DataScopeEnum.SELF.value:
                # 仅本人数据权限
                if self.user is True:
                    criterion = SysUserPo.user_id == user.user_id
                elif isinstance(self.user, AliasedClass):
                    criterion = self.user.user_id == user.user_id
                else:
                    criterion = "1=0"
                criterions.append(criterion)
            else:
                print(ValueError("Invalid data_scope value: {}".format(role.data_scope)))
        data_scope = or_(*criterions)
        criterian_meta.scope = data_scope


