# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select

from owl_common.base.model import ExtraModel
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysOperLog
from owl_admin.ext import db
from owl_system.domain.po import SysOperLogPo


class SysOperLogMapper:
    
    """
    操作日志的数据访问层
    """
    
    default_fields = {
        "oper_id", "title", "business_type", "method", "request_method",
        "operator_type", "oper_name", "dept_name", "oper_url", "oper_ip",
        "oper_location", "oper_param", "json_result", "status", "error_msg",
        "oper_time"
    }
    
    default_columns = ColumnEntityList(SysOperLogPo, default_fields)
    
    @classmethod
    def select_operlog_list(cls, oper: Optional[SysOperLog])-> List[SysOperLog]:
        '''
        查询系统操作日志集合
        
        Args:
            oper (Optional[SysOperLog]): 操作日志对象
            
        Returns:
            List[SysOperLog]: 操作日志集合
        '''
        if oper:
            criterions = []
            if oper.oper_ip:
                criterions.append(SysOperLogPo.ipaddr.like(f'%{oper.oper_ip}%'))
            if oper.status:
                criterions.append(SysOperLogPo.status == oper.status)
            if oper.oper_name:
                criterions.append(SysOperLogPo.oper_name.like(f'%{oper.oper_name}%'))
            if "criterian_meta" in g and g.criterian_meta.extra:
                extra:ExtraModel = g.criterian_meta.extra
                if extra.start_time and extra.end_time:
                    criterions.append(SysOperLogPo.oper_time >= extra.start_time)
                    criterions.append(SysOperLogPo.oper_time <= extra.end_time)
            stmt = select(*cls.default_columns) \
                .where(*criterions)
        else:
            stmt = select(*cls.default_columns)
            
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row, SysOperLog) for row in rows]
    
    @classmethod
    @Transactional(db.session)
    def insert_operlog(cls, oper: SysOperLog) -> int:
        '''
        新增操作日志
        
        Args:
            oper (SysOperLog): 操作日志对象
            
        Returns:
            int: 新增记录的ID
        '''
        fields = {
            "title", "business_type", "method", "request_method","oper_time",
            "operator_type", "oper_name", "dept_name", "oper_url", "oper_ip",
            "oper_location", "oper_param", "json_result", "status", "error_msg"
        }
        data = oper.model_dump(
            include=fields, exclude_none=True
        )
        stmt = insert(SysOperLogPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0
    
    @classmethod
    @Transactional(db.session)
    def delete_operlog_by_ids(cls, ids: List[int]) -> int:
        '''
        批量删除系统操作日志
        
        Args:
            ids (List[int]): 操作日志ID列表
            
        Returns:
            int: 删除的记录数
        '''
        stmt = delete(SysOperLogPo).where(SysOperLogPo.oper_id.in_(ids))
        return db.session.execute(stmt).rowcount
    
    @classmethod
    @Transactional(db.session)
    def clean_operlog(cls) -> int:
        '''
        清空操作日志
        
        Returns:
            int: 删除的记录数
        '''
        stmt = delete(SysOperLogPo)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def select_operlog_by_id(cls, id:int) -> Optional[SysOperLog]:
        '''
        查询操作日志详细
        
        Args:
            id (int): 操作日志ID
            
        Returns:
            Optional[SysOperLog]: 操作日志对象
        '''
        stmt = select(*cls.default_columns).where(SysOperLogPo.oper_id == id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row, SysOperLog) if row else None
        