# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from datetime import datetime
import json
import time
import os
import platform
import sys
from flask import current_app
import psutil
from typing import Dict, List
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from owl_common.base.model import strict_base_config
from owl_common.utils import IpUtil



class Cpu(BaseModel):
    
    model_config = strict_base_config
    
    # 核心数
    cpu_num: int
    
    # CPU总的使用率
    total: float
    
    # CPU系统使用率
    sys: float
    
    # CPU用户使用率
    used: float
    
    # CPU当前等待率
    wait: float
    
    # CPU当前空闲率
    free: float
    
    @classmethod
    def from_module(cls) -> "Cpu":
        """
        获取CPU信息

        Returns:
            Cpu: CPU信息
        """
        scputimes = psutil.cpu_times_percent(1)
        nice = getattr(scputimes, 'nice', 0)
        irq = getattr(scputimes, 'irq', 0)
        softirq = getattr(scputimes, 'softirq', 0)
        steal = getattr(scputimes, 'steal', 0)
        used = getattr(scputimes, 'user', 0)
        sys = getattr(scputimes,'system', 0)
        wait = getattr(scputimes, 'iowait', 0)
        free = getattr(scputimes, 'idle', 0)
        total = used + sys + wait + free + nice + irq + softirq + steal
        return cls(
            cpu_num=psutil.cpu_count(), 
            total=total, 
            sys=sys, 
            used=used, 
            wait=wait, 
            free=free
            )


class Memory(BaseModel):
    
    model_config = strict_base_config
    
    # 内存总量
    total: str
    
    # 已用内存
    used: str
    
    # 剩余内存
    free: str

    @classmethod
    def from_module(cls) -> "Memory":
        """
        获取内存信息

        Returns:
            Memory: 内存信息
        """
        memory = psutil.virtual_memory()
        total = cls.bytes_to_gb(memory.total)
        used = cls.bytes_to_gb(memory.used)
        free = cls.bytes_to_gb(memory.free)
        return cls(total=total, used=used, free=free)
        
    @classmethod
    def bytes_to_gb(cls, val:int) -> str:
        return "{:.2f}".format(val / 1024 / 1024 / 1024)


class Jvm(BaseModel):
    
    model_config = strict_base_config
    
    # 当前JVM占用的内存总数(M)
    total: float = 0
    
    # JVM最大可用内存总数(M)
    max: float = 0
    
    # JVM空闲内存(M)
    free: float = 0
    
    # JDK版本
    version: str = ""
    
    # JDK路径
    home: str = ""
    
    name: str = "[java示例，非python示例] 请执行 bash patch.sh upgrade",
    
    usage: float = 75.76,
        
    used: float = 1015.63,
    
    start_time: str = "2024-11-11 12:00:50",
    
    input_args: str = "[java示例，非python示例] 请执行 bash patch.sh upgrade"
    
    run_time: str = "2小时12分钟"
    

class SystemFile(BaseModel):
    
    model_config = strict_base_config

    # 盘符路径
    dir_name: str
    
    # 盘符类型
    sys_type_name: str
    
    # 文件类型
    type_name: str
    
    # 总大小
    total: str
    
    # 剩余大小
    free: str
    
    # 已经使用量
    used: str
    
    # 资源的使用率
    usage: float


class System(BaseModel):
    
    model_config = strict_base_config
    
    # 服务器名称
    computer_name: str
    
    # 服务器IP地址
    computer_ip: str
    
    # 项目路径
    user_dir: str
    
    # 操作系统
    os_name:str 
    
    # 系统架构
    os_arch:str

    @classmethod
    def from_module(cls) -> "System":
        """
        获取服务器系统信息

        Returns:
            System: 服务器系统信息
        """
        computer_name = platform.node()
        computer_ip = IpUtil.get_local_ips()[0]
        user_dir = current_app.extensions['flaskowl'].proot
        os_name = platform.system()
        os_arch = platform.machine()
        return cls(
            computer_name=computer_name, 
            computer_ip=computer_ip, 
            user_dir=user_dir, 
            os_name=os_name, 
            os_arch=os_arch
        )
        
        
class PyImplementation(BaseModel):
    
    model_config = strict_base_config
    
    # 当前Python占用的内存总数(MB) ##### 虚拟数据 #####
    total: str
    
    # Python最大可用内存总数(MB) ##### 虚拟数据 #####
    max: str
    
    # Python空闲内存(MB) ##### 虚拟数据 #####
    free: str
    
    # Python解释器名称
    name: str = "CPython"
    
    # Python内存使用率 ##### 虚拟数据 #####
    usage: str
    
    # Python占用的内存总数 ##### 虚拟数据 #####
    used: str
    
    # 启动时间
    start_time: str = "",
    
    # 启动参数
    input_args: str = ""
    
    # 运行时间
    run_time: str = ""
    
    # Python版本
    version: str
    
    # Python路径
    home: str

    @classmethod
    def from_module(cls) -> "PyImplementation":
        """
        获取当前Python进程信息

        Returns:
            PyImplementation: Python进程信息
        """
        proc = psutil.Process(os.getpid())
        memory = proc.memory_info()
        total = memory.rss
        used = total
        usage = "30"
        name = platform.python_implementation()
        if hasattr(proc, 'rlimit'):
            max = proc.rlimit(psutil.RLIMIT_AS)
        else:
            max = 0
        version = platform.python_version()
        home = sys.executable
        start_time = proc.create_time()
        run_time = time.time() - start_time
        input_args = json.dumps(proc.cmdline())
        
        return cls(
            total = cls.bytes_to_mb(total),
            max = cls.bytes_to_mb(max),
            used = cls.bytes_to_mb(used),
            usage = usage,
            name = name,
            free = cls.bytes_to_mb(total) if max == 0 else cls.bytes_to_mb(max - total),
            version=version,
            home=home,
            start_time=datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
            run_time=datetime.fromtimestamp(run_time).strftime('%H小时 %M分钟 %S秒'),
            input_args=input_args
        )

    @classmethod
    def bytes_to_mb(cls, val:int) -> str:
        """
        字节转换为MB

        Args:
            val (int): 输入

        Returns:
            str: 输出字符串
        """
        return "{:.2f}".format(val / 1024 / 1024)
    
    
class Server(BaseModel):
    
    model_config = strict_base_config
    
    cpu: Cpu
    
    mem: Memory
    
    sys: System
    
    sys_files: List[SystemFile] = []
    
    pyimp: PyImplementation = None
    
    jvm: Jvm = None
    
    @classmethod
    def from_module(cls) -> "Server":
        """
        获取服务器信息

        Returns:
            Server: 服务器信息
        """
        cpu = Cpu.from_module()
        mem = Memory.from_module()
        sys = System.from_module()
        pyimp = PyImplementation.from_module()
        jvm = Jvm(
            total=1340.5,
            max=3579,
            free=324.87,
            version="[java示例，非python示例] 请执行 bash patch.sh upgrade",
            home="[java示例，非python示例 请执行 bash patch.sh upgrade",
            name="[java示例，非python示例 请执行 bash patch.sh upgrade",
            usage=75.76,
            used=1015.63,
            start_time="[java示例，非python示例 请执行 bash patch.sh upgrade",
            input_args="[java示例，非python示例 请执行 bash patch.sh upgrade",
            run_time="[java示例，非python示例 请执行 bash patch.sh upgrade"
        )
        
        sys_files = []
        for part in psutil.disk_partitions():
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
            usage = psutil.disk_usage(part.mountpoint)
            sys_file = SystemFile(
                dirName=part.mountpoint,
                sysTypeName=part.fstype,
                typeName=part.device,
                total=cls.bytes_to_gb(usage.total),
                free=cls.bytes_to_gb(usage.free),
                used=cls.bytes_to_gb(usage.used),
                usage=usage.percent
            )
            sys_files.append(sys_file)
        return cls(cpu=cpu, mem=mem, sys=sys, sys_files=sys_files, pyimp=pyimp, jvm=jvm)

    @classmethod
    def bytes_to_gb(cls, val:int) -> str:
        """
        字节转换为GB

        Args:
            val (int): 输入

        Returns:
            str: 输出字符串
        """
        return "{:.2f}".format(val / 1024 / 1024 / 1024) + " GB"


class RedisCommandStatsOption(BaseModel):
    
    name: str
    
    value: Annotated[str, Field(coerce_numbers_to_str=True)]
    

class RedisCache(BaseModel):
    
    model_config = strict_base_config
    
    info: Dict = {}
    
    db_size: int
    
    command_stats: List[RedisCommandStatsOption]
    
    @classmethod
    def from_connection(cls, connection) -> "RedisCache":
        """
        获取Redis缓存信息

        Args:
            connection (redis.Redis): Redis连接

        Returns:
            RedisCache: Redis缓存信息
        """
        info = connection.info()
        db_size = connection.dbsize()
        _command_stats = connection.info('commandstats')
        command_stats = []
        for key,value in _command_stats.items():
            key = key.replace('cmdstat_', '')
            value = value["calls"]
            command_stats.append(RedisCommandStatsOption(name=key, value=value))
        return cls(info=info, db_size=db_size, command_stats=command_stats)

