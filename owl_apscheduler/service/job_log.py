# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional

from owl_apscheduler.domain.entity import SysJobLog
from owl_apscheduler.mapper.job_log import SysJobLogMapper
from owl_common.sqlalchemy.transaction import Transactional
from owl_admin.ext import db


class SysJobLogService:   
    
    @classmethod
    def select_job_log_list(cls, job_log:SysJobLog) -> List[SysJobLog]:
        """
        查询任务日志列表

        Args:
            job_log (SysJobLog): 包含查询条件的任务日志

        Returns:
            List[SysJobLog]: 任务日志列表
        """
        return SysJobLogMapper.select_job_log_list(job_log)
    
    @classmethod
    def select_job_log_by_id(cls, job_log_id:int) -> Optional[SysJobLog]:
        """
        根据任务日志ID查询任务日志

        Args:
            job_log_id (int): 任务日志ID

        Returns:
            Optional[SysJobLog]: 任务日志
        """
        return SysJobLogMapper.select_job_log_by_id(job_log_id)
    
    @classmethod
    @Transactional(db.session)
    def insert_job_log(cls, job_log:SysJobLog):
        """
        新增任务日志

        Args:
            job_log (SysJobLog): 任务日志
        """
        SysJobLogMapper.insert_job_log(job_log)
    
    @classmethod
    @Transactional(db.session)
    def delete_job_log_by_id(cls, job_log_id:int) -> bool:
        """
        根据任务日志ID，删除任务日志

        Args:
            job_log_id (int): 任务日志ID

        Returns:
            bool: 是否删除成功
        """
        num = SysJobLogMapper.delete_job_log_by_id(job_log_id)
        return num > 0
    
    @classmethod
    @Transactional(db.session)
    def delete_job_log_by_ids(cls, job_log_ids:List[int]):
        """
        根据任务日志ID列表，删除任务日志

        Args:
            job_log_ids (List[int]): 任务日志ID列表

        Returns:
            bool: 是否删除成功
        """
        num = SysJobLogMapper.delete_job_log_by_ids(job_log_ids)
        return num > 0
    
    @classmethod
    @Transactional(db.session)
    def clean_job_logs(cls):
        """
        清空任务日志
        """
        SysJobLogMapper.clean_job_logs()
