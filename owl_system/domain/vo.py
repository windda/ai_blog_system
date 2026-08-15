# -*- coding: utf-8 -*-
# @Author  : shaw-lee
   
from typing import List, Optional
from pydantic import BaseModel

from owl_common.base.model import general_response_serial_config


class RouterMetaVo(BaseModel):
    
    # 标题 
    title: Optional[str] = None
    
    # 图标 
    icon: Optional[str] = None
    
    # 缓存（true为缓存） 
    no_cache: Optional[bool] = None
    
    # 内链地址（http(s)://开头） 
    link: Optional[str] = None


class RouterVo(BaseModel):
    
    model_config = general_response_serial_config.copy()
    
    # 路由名称 
    name: Optional[str] = None
    
    # 路由地址 
    path: Optional[str] = None
    
    # 组件地址 
    component: Optional[str] = None
    
    # 是否隐藏路由（0显示 1隐藏） 
    hidden: Optional[str] = None
    
    # 重定向地址 
    redirect: Optional[str] = None
    
    # 路由参数：如 {"id": 1, "name": "ry"}
    query: Optional[str] = None
    
    # 菜单排序 
    sort: Optional[int] = None
    
    # 当你一个路由下面的 children 声明的路由大于1个时，自动会变成嵌套的模式--如组件页面
    always_show: Optional[bool] = None
    
    # 其他元素
    meta: Optional[RouterMetaVo] = None
    
    # 子路由
    children: List["RouterVo"] = []
