# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from flask import g
from sqlalchemy import delete, insert, select

from owl_common.base.model import ExtraModel
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysLogininfor
from owl_admin.ext import db
from owl_system.domain.po import SysLogininforPo


class SysLogininforMapper:

    """
    登录日志的数据访问层
    """
    
    default_fields = {
        "info_id", "user_name", "ipaddr", "login_location", "browser", "os",
        "status", "msg", "login_time", "status"
    }
    
    default_columns = ColumnEntityList(SysLogininforPo, default_fields, False)
    
    @classmethod
    @Transactional(db.session)
    def insert_logininfor(cls, info: SysLogininfor) -> int:
        """
        新增系统登录日志
        
        Args:
            info (SysLogininfor): 系统登录日志对象
        
        Returns:
            int: 新增记录的ID
        """
        fields = {
            "user_name", "status", "ipaddr", "login_location", "browser", "os",
            "msg", "login_time"
        }
        data = info.model_dump(
            include=fields, exclude_none=True, exclude_unset=True,
        )
        stmt = insert(SysLogininforPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
            
    @classmethod
    def select_logininfor_list(cls, info: SysLogininfor) -> List[SysLogininforPo]:
        """
        查询系统登录日志集合
        
        Args:
            info (SysLogininfor): 系统登录日志对象
        
        Returns:
            List[SysLogininforPo]: 系统登录日志集合
        """
        criterions = []
        if info.ipaddr:
            criterions.append(SysLogininforPo.ipaddr.like(f"%{info.ipaddr}%"))
        if info.status:
            criterions.append(SysLogininforPo.status == info.status)
        if info.user_name:
            criterions.append(SysLogininforPo.user_name.like(f"%{info.user_name}%"))
        if "criterian_meta" in g and g.criterian_meta.extra:
            extra:ExtraModel = g.criterian_meta.extra
            if extra.start_time and extra.end_time:
                criterions.append(SysLogininforPo.create_time >= extra.start_time)
                criterions.append(SysLogininforPo.create_time <= extra.end_time)
        stmt = select(*cls.default_columns) \
            .where(*criterions)
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, SysLogininfor) for row in rows]

    @classmethod
    @Transactional(db.session)
    def delete_logininfor_by_ids(cls, ids: List[int]) -> int:
        """
        批量删除系统登录日志
        
        Args:
            ids (List[int]): 系统登录日志ID列表
        
        Returns:
            int: 删除的行数
        """
        stmt = delete(SysLogininforPo).where(SysLogininforPo.info_id.in_(ids))
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def clean_logininfor(cls) -> int:
        """
        清空系统登录日志
        
        Returns:
            int: 删除的行数
        """
        stmt = delete(SysLogininforPo)
        return db.session.execute(stmt).rowcount
