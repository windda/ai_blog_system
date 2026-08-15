# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import Optional
from sqlalchemy import CHAR, DateTime, String, text
from sqlalchemy.dialects.mysql import BIGINT 
from sqlalchemy.orm import Mapped, mapped_column 
import datetime

from owl_admin.ext import db


class SysJobPo(db.Model):
    __tablename__ = 'sys_job'
    __table_args__ = {'comment': '定时任务调度表'}

    job_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='任务ID')
    job_name: Mapped[str] = mapped_column(String(64), primary_key=True, server_default=text("''"), comment='任务名称')
    job_group: Mapped[str] = mapped_column(String(64), primary_key=True, server_default=text("'DEFAULT'"), comment='任务组名')
    invoke_target: Mapped[str] = mapped_column(String(500), comment='调用目标字符串')
    cron_expression: Mapped[Optional[str]] = mapped_column(String(255), server_default=text("''"), comment='cron执行表达式')
    misfire_policy: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'3'"), comment='计划执行错误策略（1立即执行 2执行一次 3放弃执行）')
    concurrent: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'1'"), comment='是否并发执行（0允许 1禁止）')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='状态（0正常 1暂停）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), server_default=text("''"), comment='备注信息')


class SysJobLogPo(db.Model):
    __tablename__ = 'sys_job_log'
    __table_args__ = {'comment': '定时任务调度日志表'}

    job_log_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='任务日志ID')
    job_name: Mapped[str] = mapped_column(String(64), comment='任务名称')
    job_group: Mapped[str] = mapped_column(String(64), comment='任务组名')
    invoke_target: Mapped[str] = mapped_column(String(500), comment='调用目标字符串')
    job_message: Mapped[Optional[str]] = mapped_column(String(500), comment='日志信息')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='执行状态（0正常 1失败）')
    exception_info: Mapped[Optional[str]] = mapped_column(String(2000), server_default=text("''"), comment='异常信息')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
