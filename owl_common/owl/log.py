# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import os
from typing import Dict, Optional
from logging.handlers import RotatingFileHandler
from logging import Logger

class OwlLog:

    @classmethod
    def generate_handler_from_config(cls, config:Dict) \
            -> Optional[RotatingFileHandler]:
        """
        生成日志处理器

        Args:
            config (Dict): 日志配置

        Returns:
            Optional[RotatingFileHandler]: 日志处理类
        """
        log_config = config.get("log")
        if log_config:
            filename = log_config.get("filename")
            dir_name,base_name = os.path.split(filename)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            filesize = log_config.get("filesize")
            if filesize.upper().endswith("MB"):
                filesize = cls.mb_to_bytes(int(filesize[:-2]))
            elif filesize.upper().endswith("KB"):
                filesize = cls.kb_to_bytes(int(filesize[:-2]))
            else:
                filesize = int(filesize)
            filenum = log_config.get("filenum")
            handler = RotatingFileHandler(filename, maxBytes=filesize, backupCount=filenum)
            level = log_config.get("level")
            if level is None or level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                return None
            handler.setLevel(level)
            formatter = log_config.get("format")
            if formatter is None or not isinstance(formatter, dict):
                return None
            handler.setFormatter(**formatter)
            return handler
        else:
            return None
    
    @classmethod
    def mb_to_bytes(cls, mb:int) -> int:
        """
        转换MB为字节

        Args:
            mb (int): 输入

        Returns:
            int: 输出
        """
        return mb * 1024 * 1024
    
    @classmethod
    def kb_to_bytes(cls, kb:int) -> int:
        """
        转换KB为字节

        Args:
            mb (int): 输入

        Returns:
            int: 输出
        """
        return kb * 1024
