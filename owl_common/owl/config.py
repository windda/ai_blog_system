# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import os
from typing import Dict
from flask import Flask
import yaml

from ..utils.base import DictUtil


CONFIG_CACHE = dict()


class OwlConfigLoader(object):
    
    pname = "config"
    name = "app.yml"
    name_tmpl = "app-{}.yml"
    
    def __init__(self, root):
        self._root = root
        self._raw_data = {}
        config_file = self._generate_main_config()
        self.load_config(config_file)
        self.load_config_from_cache()
    
    def load_config_from_cache(self):
        '''
        从缓存配置env配置中加载配置
        '''
        env = self.cache.get("owl.env")
        if env is not None:
            config_file = os.path.join(self._root, self.pname, self.name_tmpl.format(env))
            if not os.path.exists(config_file):
                raise FileNotFoundError(f"Config file {config_file} not found")
            self.load_config(config_file)        
    
    def _generate_main_config(self) -> str:
        '''
        生成配置文件
        
        Returns:
            str: 配置文件路径
        '''
        config_path = os.path.join(self._root, self.pname)
        config_file = os.path.join(config_path, self.name)
        if not os.path.exists(config_path):
            os.mkdir(config_path)
        return config_file
    
    def load_config(self, file):
        '''
        加载配置文件参数
        '''
        with open(file, 'r') as f:
            config_obj = yaml.load(f, Loader=yaml.FullLoader)
        self._raw_data.update(config_obj)
        data = DictUtil.recurive_key(config_obj)
        flatten_data = DictUtil.flatten(data)
        formated_data = DictUtil.format_value(flatten_data)
        CONFIG_CACHE.update(formated_data)
    
    @property
    def cache(self) -> Dict:
        """
        缓存配置

        Returns:
            Dict: 缓存配置
        """
        return CONFIG_CACHE
    
    def set_app(self,app:Flask):
        """
        关联flask应用

        Args:
            app (Flask):  flask应用
        """
        config = self._raw_data.get("flask",{})
        owl_config = self._raw_data.get("owl",{})
        host = owl_config.get("host","127.0.0.1")
        port = owl_config.get("port",9000)
        # 不设置 SERVER_NAME，避免访问域名不匹配导致404
        config.update({"SERVER_HOST": host, "SERVER_PORT": port})
        config = DictUtil.upper_key(config)
        app.config.update(config)
    