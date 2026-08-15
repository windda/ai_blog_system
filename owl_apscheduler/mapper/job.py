# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from sqlalchemy import insert,update,delete,select

from owl_common.sqlalchemy.model import ColumnEntityList
from owl_apscheduler.domain.po import SysJobPo
from owl_apscheduler.domain.entity import SysJob
from owl_admin.ext import db


class SysJobMapper:
    
    default_fields = {
        "job_id","job_name","job_group","invoke_target","cron_expression", \
        "misfire_policy","concurrent","status","create_by","create_time", \
        "remark"
    }
    
    default_columns = ColumnEntityList(SysJobPo, default_fields, False)
    
    @classmethod
    def select_job_list(cls, job:SysJob) -> List[SysJob]:
        """
        有条件查询任务列表

        Args:
            job (SysJob): 查询条件

        Returns:
            List[SysJob]: 任务列表
        """
        criterions = []
        if job.job_name:
            criterions.append(SysJobPo.job_name.like(f"%{job.job_name}%"))
        if job.job_group:
            criterions.append(SysJobPo.job_group==job.job_group)
        if job.status:
            criterions.append(SysJobPo.status == job.status)
        if job.invoke_target:
            criterions.append(
                SysJobPo.invoke_target.like(f"%{job.invoke_target}%")
            )
        stmt = select(*cls.default_columns) \
            .where(*criterions)
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysJob) for row in rows]
    
    @classmethod
    def select_job_all(cls) -> List[SysJob]:
        """
        查询所有任务

        Returns:
            List[SysJob]: 任务列表
        """
        stmt = select(*cls.default_columns).select_from(SysJobPo)
        rows = db.session.execute(stmt).all()
        return [cls.default_columns.cast(row,SysJob) for row in rows]
    
    @classmethod
    def select_job_by_id(cls, job_id:int) -> Optional[SysJob]:
        """
        根据任务ID，查询任务

        Args:
            job_id (int): 任务ID

        Returns:
            Optional[SysJob]: 任务
        """
        stmt = select(*cls.default_columns) \
            .where(SysJobPo.job_id==job_id)
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysJob) if row else None
    
    @classmethod
    def insert_job(cls, job:SysJob) -> Optional[int]:
        """
        新增任务

        Args:
            job (SysJob): 任务

        Returns:
            Optional[int]: 任务ID
        """
        fields = {
            "job_id","job_name","job_group","invoke_target","cron_expression", \
            "misfire_policy","concurrent","status","create_by","create_time", \
            "remark"
        }
        data = job.model_dump(
            include=fields,exclude_unset=True,exclude_none=True
        )
        stmt = insert(SysJobPo).values(data)
        return db.session.execute(stmt).scalar_one_or_none()
    
    @classmethod
    def update_job(cls, job:SysJob) -> int:
        """
        更新任务

        Args:
            job (SysJob): 任务

        Returns:
            int: 影响行数
        """
        fields = {
            "job_name","job_group","invoke_target","cron_expression", \
            "misfire_policy","concurrent","status","update_by","update_time", \
            "remark"
        }
        data = job.model_dump(
            include=fields,exclude_unset=True,exclude_none=True
        )
        stmt = update(SysJobPo) \
            .where(SysJobPo.job_id==job.job_id) \
            .values(data)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_job_by_id(cls, job_id:int) -> int:
        """
        根据任务ID，删除任务

        Args:
            job_id (int): 任务ID

        Returns:
            int: 影响行数
        """
        stmt = delete(SysJobPo).where(SysJobPo.job_id==job_id)
        return db.session.execute(stmt).rowcount
    
    @classmethod
    def delete_job_by_ids(cls, job_ids:List[int]) -> int:
        """
        根据任务ID列表，删除任务

        Args:
            job_ids (List[int]): 任务ID列表

        Returns:
            int: 影响行数
        """
        stmt = delete(SysJobPo).where(SysJobPo.job_id.in_(job_ids))
        return db.session.execute(stmt).rowcount
    