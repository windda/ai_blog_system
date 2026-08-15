# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List
from flask import g
from sqlalchemy import insert,delete,select

from owl_common.base.model import ExtraModel
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_apscheduler.domain.po import SysJobLogPo
from owl_apscheduler.domain.entity import SysJobLog
from owl_admin.ext import db


class SysJobLogMapper:

    default_fields = {
        "job_log_id", "job_name", "job_group", "invoke_target", "job_message", 
        "status", "exception_info", "create_time"
    }
    
    default_columns = ColumnEntityList(SysJobLogPo, default_fields, False)
    
    @classmethod
    def select_job_log_list(cls, joblog:SysJobLog) -> List[SysJobLog]:
        """
        查询任务日志列表

        Args:
            joblog (SysJobLog): 包含查询条件的数据传输对象

        Returns:
            List[SysJobLog]: 任务日志列表
        """
        criterions = []
        if joblog.job_name:
            criterions.append(SysJobLogPo.job_name.like(f"%{joblog.job_name}%"))
        if joblog.job_group:
            criterions.append(SysJobLogPo.job_group==joblog.job_group)
        if joblog.status:
            criterions.append(SysJobLogPo.status == joblog.status)
        if joblog.invoke_target:
            criterions.append(
                SysJobLogPo.invoke_target.like(f"%{joblog.invoke_target}%")
            )
        if "criterian_meta" in g and g.criterian_meta.extra:
            extra:ExtraModel = g.criterian_meta.extra
            if extra.start_time and extra.end_time:
                criterions.append(SysJobLogPo.create_time >= extra.start_time)
                criterions.append(SysJobLogPo.create_time <= extra.end_time)
        stmt = select(*cls.default_columns) \
            .where(*criterions)
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysJobLog) for row in rows]
    
    @classmethod
    def select_job_log_all(cls) -> List[SysJobLog]:
        """
        查询所有任务日志

        Returns:
            List[SysJobLog]: 任务日志列表
        """
        stmt = select(*cls.default_columns)
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysJobLog) for row in rows]
        
    @classmethod
    def insert_job_log(cls, joblog:SysJobLog):
        """
        新增任务日志

        Args:
            joblog (SysJobLog): 任务日志信息

        Returns:
            int: 影响的行数
        """
        fields = {
            "job_log_id", "job_name", "job_group", "invoke_target", "job_message", 
            "status", "exception_info", "create_time"
        }
        data = joblog.model_dump(
            include=fields,exclude_unset=True,exclude_none=True
        )
        stmt = insert(SysJobLogPo).values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    def delete_job_log_by_id(cls, job_id:int):
        """
        根据任务日志ID，删除任务日志

        Args:
            job_id (int): 任务日志ID

        Returns:
            int: 影响的行数
        """
        stmt = delete(SysJobLogPo).where(SysJobLogPo.job_log_id==job_id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_job_log_by_ids(cls, job_ids:List[int]):
        """
        根据任务日志ID列表，删除任务日志

        Args:
            job_ids (List[int]): 任务日志ID列表

        Returns:
            int: 影响的行数
        """
        stmt = delete(SysJobLogPo).where(SysJobLogPo.job_log_id.in_(job_ids))
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def clean_job_logs(cls):
        """
        清空任务日志

        Returns:
            int: 影响的行数
        """
        stmt = delete(SysJobLogPo)
        return db.session.execute(stmt).rowcount
    