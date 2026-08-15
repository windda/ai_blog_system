# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from datetime import datetime
from types import NoneType
from typing import Optional
from pydantic import BeforeValidator, Field, PlainSerializer
from pydantic_core import to_json
from typing_extensions import Annotated

from owl_common.base.transformer import to_datetime, str_to_int
from owl_common.domain.entity import LoginUser
from owl_common.base.model import AuditEntity, BaseEntity, VoAccess


class SysUserRole(BaseEntity):
    
    # 用户ID 
    user_id: int
    
    # 角色ID 
    role_id: int
    

class SysUserOnline(BaseEntity):
    
    # 会话编号 
    token_id: Optional[str] = None

    # 用户名称 
    user_name: Annotated[
        Optional[str], 
        Field(default=None,vo=VoAccess(query=True,sort=True))
    ]

    # 登录IP地址 
    ip_addr: Annotated[
        Optional[str], 
        Field(default=None,vo=VoAccess(query=True,sort=True))
    ]

    # 登录地址 
    login_location: Optional[str] = None

    # 浏览器类型 
    browser: Optional[str] = None

    # 操作系统 
    os: Optional[str] = None

    # 登录时间 
    login_time: Optional[datetime] = None
    
    # 部门名称 
    dept_name: Optional[str] = None
    
    @classmethod
    def from_loginuser(cls, login_user:LoginUser):
        return cls(
            token_id=login_user.token.hex,
            user_name=login_user.user_name,
            dept_name=login_user.dept_name,
            ip_addr=login_user.ip_addr,
            login_location=login_user.login_location,
            browser=login_user.browser,
            os=login_user.os,
            login_time=login_user.login_time,
        )

    
class SysRoleMenu(BaseEntity):

    # 角色ID 
    role_id: int
    
    # 菜单ID 
    menu_id: int
    

class SysUserPost(BaseEntity):

    # 用户ID 
    user_id: int
    
    # 岗位ID 
    post_id: int
    

class SysRoleDept(BaseEntity):

    # 角色ID 
    role_id: int
    
    # 部门ID 
    dept_id: int
    

class SysPost(AuditEntity):
    
    # 岗位序号 
    post_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0,default=None)
    ]
    
    # 岗位编码 
    post_code: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 岗位名称 
    post_name: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 岗位排序 
    post_sort: Optional[int] = None
    
    # 状态（0正常 1停用） 
    status: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 标识 默认不存在 
    flag: Annotated[
        Optional[str],
        Field(default=None,exclude=True,vo=VoAccess(body=False))
    ]


class SysOperLog(BaseEntity):
    
    # 日志主键 # 
    oper_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0,default=None)]
    
    # 操作模块 # 
    title: Optional[str] = None
    
    # 业务类型（0其它 1新增 2修改 3删除） 
    business_type: Optional[int] = None
    
    # 业务类型数组 
    business_types: Optional[str] = None
    
    # 请求方法 
    method: Optional[str] = None
    
    # 请求方式 
    request_method: Optional[str] = None
    
    # 操作类别（0其它 1后台用户 2手机端用户） 
    operator_type: Optional[int] = None
    
    # 操作人员 
    oper_name: Annotated[
        Optional[str],
        Field(default=None,exclude=True,vo=VoAccess(query=True))
    ]
    
    # 部门名称 
    dept_name: Annotated[
        Optional[str],
        Field(default=None,exclude=True,vo=VoAccess(body=False))
    ]
    
    # 请求url 
    oper_url: Optional[str] = None
    
    # 操作地址 
    oper_ip: Annotated[
        Optional[str],
        Field(default=None,exclude=True,vo=VoAccess(query=True))
    ]
    
    # 操作地点 
    oper_location: Optional[str] = None
    
    # 请求参数 
    oper_param: Annotated[
        Optional[str],
        BeforeValidator(lambda x: to_json(x) if isinstance(x,(dict,list,tuple)) else x),
    ] = None
    
    # 返回参数 
    json_result: Optional[str] = None
    
    # 操作状态（0正常 1异常） 
    status: Annotated[
        Optional[int],
        Field(default=None,exclude=True,vo=VoAccess(query=True))
    ]
    
    # 错误消息 
    error_msg: Optional[str] = None
    
    # 操作时间 
    oper_time: Annotated[
        Optional[datetime],
        BeforeValidator(to_datetime()),
        Field(default=None,vo=VoAccess())
    ]
    
    
class SysNotice(AuditEntity):

    # 公告ID
    notice_id: Annotated[
        int,
        BeforeValidator(str_to_int),
        Field(gt=0,default=None)
    ]

    # 公告标题
    notice_title: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]

    # 公告类型（1通知 2公告）
    notice_type: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]

    # 公告内容
    notice_content: Annotated[
        Optional[str],
        BeforeValidator(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x),
        PlainSerializer(lambda x: x.encode('utf-8'), return_type=bytes)
    ] = None

    # 公告状态（0正常 1关闭）
    status: Optional[str] = None
    
    create_by: Annotated[
        str | int | NoneType,
        Field(default=None,vo=VoAccess(body=False,query=True))
    ]
    

class SysLogininfor(AuditEntity):
    
    # id
    info_id: Optional[int] = None
    
    # 用户账号
    user_name: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 登录状态（0成功 1失败）
    status: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 登录IP地址
    ipaddr: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 登录地点
    login_location: Optional[str] = None
    
    # 登录浏览器
    browser: Optional[str] = None
    
    # 登录操作系统
    os: Optional[str] = None
    
    # 登录时间
    login_time: Annotated[Optional[datetime],Field(default_factory=datetime.now)] = None
    
    # 提示消息
    msg: Optional[str] = None
    


class SysConfig(AuditEntity):
    
    # 参数主键
    config_id: Optional[int] = None   # @Excel(name = "参数主键")
    
    # 参数名称
    config_name: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 参数键名
    config_key: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]

    # 系统内置（Y是 N否）
    config_type: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    # 参数键值
    config_value: Optional[str] = None   # @Excel(name = "参数键值")

    

class MetaEntity(BaseEntity):
    
    # 设置该路由在侧边栏和面包屑中展示的名字
    title: Optional[str] = None   # @Excel(name = "标题")
    
    # 设置该路由的图标，对应路径src/assets/icons/svg
    icon: Optional[str] = None   # @Excel(name = "图标")
    
    # 设置为true，则不会被 <keep-alive>缓存
    no_cache: Optional[bool] = None   # @Excel(name = "是否缓存", readConverterExp = "Y=是,N=否")
    
    # 内链地址（http(s)://开头）
    link: Optional[str] = None  
    

class RouterEntity(BaseEntity):
    
    # 路由名字
    name: Optional[str] = None   # @Excel(name = "名称")
    
    # 路由路径
    path: Optional[str] = None   # @Excel(name = "路径")
    
    # 组件路径
    component: Optional[str] = None   # @Excel(name = "组件")
    
    # 其他元素
    meta: Optional[MetaEntity] = None   # @Excel(name = "元数据")
    
    # 子路由
    children: Optional[list] = []   # @Excel(name = "子路由")
    
    # 是否隐藏路由，当设置 true 的时候该路由不会再侧边栏出现
    hidden: Optional[bool] = None   # @Excel(name = "是否隐藏", readConverterExp = "Y=是,N=否")
    
    # 当你一个路由下面的 children 声明的路由大于1个时，自动会变成嵌套的模式--如组件页面
    always_show: Optional[bool] = None   # @Excel(name = "显示根路由", readConverterExp = "Y=是,N=否")
    
    # 重定向地址，当设置 noRedirect 的时候该路由在面包屑导航中不可被点击
    redirect: Optional[str] = None   # @Excel(name = "重定向")
    
    # 排序
    sort: Optional[int] = None   # @Excel(name = "排序")
    
    # 路由参数：如 {"id": 1, "name": "ry"}
    query: Optional[str] = None   # @Excel(name = "查询")
