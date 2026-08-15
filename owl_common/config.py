# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.owl.config import CONFIG_CACHE
        

class OWLConfig:
    
    profile = CONFIG_CACHE["owl.profile"]
    
    @property
    def upload_path(self) -> str:
        """
        获取上传路径

        Returns:
            str: 上传路径
        """
        return f"uploads/{self.profile}/upload"
    
    @property
    def download_path(self) -> str:
        """
        获取下载路径

        Returns:
            str: 下载路径
        """
        return f"uploads/{self.profile}/download/"
    
    @property
    def avatar_path(self) -> str:
        """
        获取头像路径

        Returns:
            str: 头像路径
        """
        return f"uploads/{self.profile}/avatar"
    
    @property
    def import_path(self) -> str:
        """
        获取导入路径

        Returns:
            str: 导入路径
        """
        return f"uploads/{self.profile}/import"
    

