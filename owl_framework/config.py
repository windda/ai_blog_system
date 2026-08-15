# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from owl_common.owl.config import CONFIG_CACHE


class TokenConfig:
    
    header = CONFIG_CACHE["token.header"]
    
    secret = CONFIG_CACHE["token.secret"]
    
    _expire_time = CONFIG_CACHE["token.expireTime"]
    
    @classmethod
    def expire_time(cls) -> timedelta:
        """
        获取过期时间

        Returns:
            timedelta: 过期时间
        """
        return timedelta(minutes=int(cls._expire_time))
    

class ThreadPoolConfig:
    
    max_pool_size = 200
    
    keep_alive_time = 300
    
    @classmethod
    def thread_pool(cls) -> ThreadPoolExecutor:
        """
        获取线程池

        Returns:
            ThreadPoolExecutor: 线程池
        """
        ThreadPool = ThreadPoolExecutor(
            max_workers=cls.max_pool_size,
            thread_name_prefix='schedule-pool-%d',
        )
        return ThreadPool

    

