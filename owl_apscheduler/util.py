# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import importlib
import re
from types import NoneType
from typing import Callable, Dict, List, Optional, Tuple
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger as _CronTrigger
from croniter import croniter

from owl_apscheduler.constant import ScheduleConstant, ScheduleStatus
from owl_apscheduler.domain.entity import SysJob


class TargetParser:
    
    def __init__(self, target:str):
        self.target = target
        
    def parse(self):
        self.func_str = self.target


def check_method_importable(module: str, method: str) -> bool:
    try:
        module = importlib.import_module(module)
        if hasattr(module, method):
            return True 
        else:
            return False
    except Exception as e:
        return False


class ScheduleUtil:
    
    REPLACE_EXISTING = False
    
    DEFAULT_JOBSTORE = 'default'
    
    @classmethod
    def create_schedule_job(cls, scheduler:BaseScheduler, job:SysJob):
        """
        创建定时任务
        
        Args:
            scheduler: 调度器
            job: 系统任务
        """
        module_name, method_name, args, kwargs = cls.parse_target(job.invoke_target)
        if not check_method_importable(module_name, method_name):
            raise ImportError(
                f"Method {method_name} not found in module {module_name}"
            )
        func = getattr(importlib.import_module(module_name), method_name)
        trigger = CronTrigger.from_crontab(job.cron_expression)
        
        misfire_time, replace = cls.get_misfire_policy(job.misfire_policy)
        concurrent_num = cls.concurrent_num(job.concurrent)
        
        scheduler.add_job(
            func=func,
            args=args,
            kwargs=kwargs,
            trigger=trigger,
            id=job.job_key,
            name=job.job_name,
            max_instances=concurrent_num,
            coalesce=True,
            misfire_grace_time=misfire_time,
            replace_existing=cls.REPLACE_EXISTING or replace,
            jobstore=cls.DEFAULT_JOBSTORE
        )
        if job.status == ScheduleStatus.PAUSED.value:
            scheduler.pause_job(job.job_key)
    
    @classmethod
    def reschedule_job(cls, scheduler:BaseScheduler, job:SysJob):
        """
        重新调度任务
        
        Args:
            scheduler: 调度器
            job: 系统任务
        """
        if job.cron_expression:
            trigger = CronTrigger.from_crontab(job.cron_expression)
            scheduler.reschedule_job(
                job_id=job.job_key,
                trigger=trigger,
                jobstore=cls.DEFAULT_JOBSTORE
            )
        else:
            scheduler.resume_job(job.job_key, jobstore=cls.DEFAULT_JOBSTORE)
        
    @classmethod
    def concurrent_num(cls, concurrent:str) -> int:
        """
        允许并发数量
        
        Args:
            concurrent(str): 并发策略
        
        Returns:
            int: 并发数量
        """
        if concurrent == ScheduleConstant.ALLOW_CONCURRENT:
            return 10
        else:
            return 1
        
    @classmethod
    def get_misfire_policy(cls, policy:str) -> Tuple[Optional[int], bool]:
        """
        获取任务的过期策略
        
        Args:
            misfire_policy(str): 过期策略
        
        Returns:
            Tuple[Optional[int], bool]: 过期策略, 是否替换已存在的任务
        """
        if policy == ScheduleConstant.MISFIRE_DEFAULT:
            misfire_grace_time = None
            replace_existing = True
        elif policy == ScheduleConstant.MISFIRE_IGNORE_MISFIRES:
            misfire_grace_time = None
            replace_existing = True
        elif policy == ScheduleConstant.MISFIRE_FIRE_AND_PROCEED:
            misfire_grace_time = 1
            replace_existing = False
        elif policy == ScheduleConstant.MISFIRE_DO_NOTHING:
            misfire_grace_time = None
            replace_existing = False
        else:
            misfire_grace_time = None
            replace_existing = False
        return misfire_grace_time, replace_existing
    
    @classmethod
    def parse_target(cls, target:str) -> Tuple[Callable, List, Dict]:
        """
        解析目标方法字符串
        
        Args:
            target(str): 目标字符串
        
        Returns:
            Tuple[Str, Str, List, Dict]: 模块名, 方法名, 参数列表, 关键字参数字典
        """
        match = re.match(r"""
            (?P<module>[a-zA-Z_][a-zA-Z0-9_\.]*)\.
            (?P<method>[a-zA-Z_][a-zA-Z0-9_]*)
            (\((?P<params>.*)\))?
            """, target, re.VERBOSE)
        method_dict = match.groupdict()
        if method_dict:
            module_name = method_dict['module']
            method_name = method_dict['method']
            params = method_dict['params']
            args = []; kwargs = {}
            if params:
                for param in params.split(','):
                    _param = param.strip().strip("'").strip("\"")
                    if "=" in _param:
                        key,value = _param.split("=")
                        kwargs[key] = value
                    else:
                        args.append(_param)
            return module_name, method_name, args, kwargs
        raise ValueError("Invalid target string: %s" % target)
    
    @classmethod
    def unparse_target(cls, module_name, method_name, args, kwargs) -> str:
        """
        反解析目标方法字符串
        
        Args:
            module_name(str): 模块名
            method_name(str): 方法名
            args(list): 参数列表
            kwargs(dict): 关键字参数字典
        
        Returns:
            str: 目标字符串
        """
        funcname = f"{module_name}.{method_name}"
        return cls.unparse_target_by_funcname(funcname, args, kwargs)
    
    @classmethod
    def unparse_target_by_funcname(cls, funcname, args, kwargs) -> str:
        """
        反解析目标方法字符串-根据带模块的方法名
        
        Args:
            funcname(str): 带模块的方法名
            args(list): 参数列表
            kwargs(dict): 关键字参数字典
        
        Returns:
            str: 目标字符串
        """
        args_list = []
        for arg in args:
            if isinstance(arg, str):
                args_list.append(f"'{arg}'")
            else:
                args_list.append(str(arg))
        for k in kwargs:
            if isinstance(kwargs[k], str):
                args_list.append(f"{k}='{kwargs[k]}'")
            elif isinstance(kwargs[k], int):
                args_list.append(f"{k}={kwargs[k]}")
        args_str = ", ".join(args_list) if args_list else ""
        return f"{funcname}({args_str})"

    @classmethod
    def white_list_check(cls, invoke_target:str) -> bool:
        """
        白名单检查
        
        Args:
            invoke_target(str): 目标字符串
        
        Returns:
            bool: 是否允许执行
        """
        module_name, _, _, _ = cls.parse_target(invoke_target)
        for pack_name in ScheduleConstant.JOB_WHITELIST_STR:
            if module_name.startswith(pack_name):
                return True
        return False
    
    @classmethod
    def check_cron_expression(cls, expr:str) -> bool:
        """
        校验cron表达式
        
        Args:
            cron_expression(str): cron表达式
        
        Returns:
            bool: 是否合法
        """
        expr = CronTrigger.transform_from_quartz(expr)
        return croniter.is_valid(expr)


class CronTrigger(_CronTrigger):
    
    @classmethod
    def from_crontab(cls, expr:str, timezone=None) -> 'CronTrigger':
        """
        cron表达式转换为CronTrigger

        Args:
            expr (str): cron表达式
            timezone (_type_, optional): 时区. Defaults to None.

        Raises:
            ValueError: cron表达式错误

        Returns:
            CronTrigger: CronTrigger对象
        """
        expr = cls.transform_from_quartz(expr)
        
        if not croniter.is_valid(expr):
            raise ValueError("Invalid cron expression: %s" % expr)
        
        values = expr.split()
        return cls(second=values[0], minute=values[1], hour=values[2], day=values[3], month=values[4],
                   day_of_week=values[5], timezone=timezone)
        
    @classmethod
    def transform_from_quartz(cls, expr:str) -> str:
        """
        quartz表达式转换为apscheduler表达式

        Args:
            expr (str): quartz表达式

        Returns:
            str: apscheduler表达式
        """
        return expr.replace('?', '*')
    