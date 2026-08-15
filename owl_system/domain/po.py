# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import Optional
from sqlalchemy import CHAR, DateTime, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGBLOB, TINYINT
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from owl_admin.ext import db


class SysConfigPo(db.Model):
    __tablename__ = 'sys_config'
    __table_args__ = {'comment': '参数配置表'}

    config_id: Mapped[int] = mapped_column(INTEGER(5), primary_key=True, comment='参数主键')
    config_name: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='参数名称')
    config_key: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='参数键名')
    config_value: Mapped[Optional[str]] = mapped_column(String(500), server_default=text("''"), comment='参数键值')
    config_type: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'N'"), comment='系统内置（Y是 N否）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysDeptPo(db.Model):
    __tablename__ = 'sys_dept'
    __table_args__ = {'comment': '部门表'}

    dept_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='部门id')
    parent_id: Mapped[Optional[int]] = mapped_column(BIGINT(20), server_default=text("'0'"), comment='父部门id')
    ancestors: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='祖级列表')
    dept_name: Mapped[Optional[str]] = mapped_column(String(30), server_default=text("''"), comment='部门名称')
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"), comment='显示顺序')
    leader: Mapped[Optional[str]] = mapped_column(String(20), comment='负责人')
    phone: Mapped[Optional[str]] = mapped_column(String(11), comment='联系电话')
    email: Mapped[Optional[str]] = mapped_column(String(50), comment='邮箱')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='部门状态（0正常 1停用）')
    del_flag: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='删除标志（0代表存在 2代表删除）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')


class SysDictDataPo(db.Model):
    __tablename__ = 'sys_dict_data'
    __table_args__ = {'comment': '字典数据表'}

    dict_code: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='字典编码')
    dict_sort: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"), comment='字典排序')
    dict_label: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='字典标签')
    dict_value: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='字典键值')
    dict_type: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='字典类型')
    css_class: Mapped[Optional[str]] = mapped_column(String(100), comment='样式属性（其他样式扩展）')
    list_class: Mapped[Optional[str]] = mapped_column(String(100), comment='表格回显样式')
    is_default: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'N'"), comment='是否默认（Y是 N否）')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='状态（0正常 1停用）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysDictTypePo(db.Model):
    __tablename__ = 'sys_dict_type'
    __table_args__ = (
        Index('dict_type', 'dict_type', unique=True),
        {'comment': '字典类型表'}
    )

    dict_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='字典主键')
    dict_name: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='字典名称')
    dict_type: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='字典类型')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='状态（0正常 1停用）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysLogininforPo(db.Model):
    __tablename__ = 'sys_logininfor'
    __table_args__ = {'comment': '系统访问记录'}

    info_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='访问ID')
    user_name: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='用户账号')
    ipaddr: Mapped[Optional[str]] = mapped_column(String(128), server_default=text("''"), comment='登录IP地址')
    login_location: Mapped[Optional[str]] = mapped_column(String(255), server_default=text("''"), comment='登录地点')
    browser: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='浏览器类型')
    os: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='操作系统')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='登录状态（0成功 1失败）')
    msg: Mapped[Optional[str]] = mapped_column(String(255), server_default=text("''"), comment='提示消息')
    login_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='访问时间')


class SysMenuPo(db.Model):
    __tablename__ = 'sys_menu'
    __table_args__ = {'comment': '菜单权限表'}

    menu_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='菜单ID')
    menu_name: Mapped[str] = mapped_column(String(50), comment='菜单名称')
    parent_id: Mapped[Optional[int]] = mapped_column(BIGINT(20), server_default=text("'0'"), comment='父菜单ID')
    order_num: Mapped[Optional[int]] = mapped_column(INTEGER(4), server_default=text("'0'"), comment='显示顺序')
    path: Mapped[Optional[str]] = mapped_column(String(200), server_default=text("''"), comment='路由地址')
    component: Mapped[Optional[str]] = mapped_column(String(255), comment='组件路径')
    query: Mapped[Optional[str]] = mapped_column(String(255), comment='路由参数')
    is_frame: Mapped[Optional[int]] = mapped_column(INTEGER(1), server_default=text("'1'"), comment='是否为外链（0是 1否）')
    is_cache: Mapped[Optional[int]] = mapped_column(INTEGER(1), server_default=text("'0'"), comment='是否缓存（0缓存 1不缓存）')
    menu_type: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("''"), comment='菜单类型（M目录 C菜单 F按钮）')
    visible: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='菜单状态（0显示 1隐藏）')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='菜单状态（0正常 1停用）')
    perms: Mapped[Optional[str]] = mapped_column(String(100), comment='权限标识')
    icon: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("'#'"), comment='菜单图标')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), server_default=text("''"), comment='备注')


class SysNoticePo(db.Model):
    __tablename__ = 'sys_notice'
    __table_args__ = {'comment': '通知公告表'}

    notice_id: Mapped[int] = mapped_column(INTEGER(4), primary_key=True, comment='公告ID')
    notice_title: Mapped[str] = mapped_column(String(50), comment='公告标题')
    notice_type: Mapped[str] = mapped_column(CHAR(1), comment='公告类型（1通知 2公告）')
    notice_content: Mapped[Optional[bytes]] = mapped_column(LONGBLOB, comment='公告内容')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='公告状态（0正常 1关闭）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(255), comment='备注')


class SysOperLogPo(db.Model):
    __tablename__ = 'sys_oper_log'
    __table_args__ = {'comment': '操作日志记录'}

    oper_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='日志主键')
    title: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='模块标题')
    business_type: Mapped[Optional[int]] = mapped_column(INTEGER(2), server_default=text("'0'"), comment='业务类型（0其它 1新增 2修改 3删除）')
    method: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='方法名称')
    request_method: Mapped[Optional[str]] = mapped_column(String(10), server_default=text("''"), comment='请求方式')
    operator_type: Mapped[Optional[int]] = mapped_column(INTEGER(1), server_default=text("'0'"), comment='操作类别（0其它 1后台用户 2手机端用户）')
    oper_name: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='操作人员')
    dept_name: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='部门名称')
    oper_url: Mapped[Optional[str]] = mapped_column(String(255), server_default=text("''"), comment='请求URL')
    oper_ip: Mapped[Optional[str]] = mapped_column(String(128), server_default=text("''"), comment='主机地址')
    oper_location: Mapped[Optional[str]] = mapped_column(String(255), server_default=text("''"), comment='操作地点')
    oper_param: Mapped[Optional[str]] = mapped_column(String(2000), server_default=text("''"), comment='请求参数')
    json_result: Mapped[Optional[str]] = mapped_column(String(2000), server_default=text("''"), comment='返回参数')
    status: Mapped[Optional[int]] = mapped_column(INTEGER(1), server_default=text("'0'"), comment='操作状态（0正常 1异常）')
    error_msg: Mapped[Optional[str]] = mapped_column(String(2000), server_default=text("''"), comment='错误消息')
    oper_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='操作时间')


class SysPostPo(db.Model):
    __tablename__ = 'sys_post'
    __table_args__ = {'comment': '岗位信息表'}

    post_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='岗位ID')
    post_code: Mapped[str] = mapped_column(String(64), comment='岗位编码')
    post_name: Mapped[str] = mapped_column(String(50), comment='岗位名称')
    post_sort: Mapped[int] = mapped_column(INTEGER(4), comment='显示顺序')
    status: Mapped[str] = mapped_column(CHAR(1), comment='状态（0正常 1停用）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysRolePo(db.Model):
    __tablename__ = 'sys_role'
    __table_args__ = {'comment': '角色信息表'}

    role_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='角色ID')
    role_name: Mapped[str] = mapped_column(String(30), comment='角色名称')
    role_key: Mapped[str] = mapped_column(String(100), comment='角色权限字符串')
    role_sort: Mapped[int] = mapped_column(INTEGER(4), comment='显示顺序')
    status: Mapped[str] = mapped_column(CHAR(1), comment='角色状态（0正常 1停用）')
    data_scope: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'1'"), comment='数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）')
    menu_check_strictly: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"), comment='菜单树选择项是否关联显示')
    dept_check_strictly: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"), comment='部门树选择项是否关联显示')
    del_flag: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='删除标志（0代表存在 2代表删除）')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysRoleDeptPo(db.Model):
    __tablename__ = 'sys_role_dept'
    __table_args__ = {'comment': '角色和部门关联表'}

    role_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='角色ID')
    dept_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='部门ID')


class SysRoleMenuPo(db.Model):
    __tablename__ = 'sys_role_menu'
    __table_args__ = {'comment': '角色和菜单关联表'}

    role_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='角色ID')
    menu_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='菜单ID')


class SysUserPo(db.Model):
    __tablename__ = 'sys_user'
    __table_args__ = {'comment': '用户信息表'}

    user_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='用户ID')
    user_name: Mapped[str] = mapped_column(String(30), comment='用户账号')
    nick_name: Mapped[str] = mapped_column(String(30), comment='用户昵称')
    dept_id: Mapped[Optional[int]] = mapped_column(BIGINT(20), comment='部门ID')
    user_type: Mapped[Optional[str]] = mapped_column(String(2), server_default=text("'00'"), comment='用户类型（00系统用户）')
    email: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("''"), comment='用户邮箱')
    phonenumber: Mapped[Optional[str]] = mapped_column(String(11), server_default=text("''"), comment='手机号码')
    sex: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='用户性别（0男 1女 2未知）')
    avatar: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='头像地址')
    password: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("''"), comment='密码')
    status: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='帐号状态（0正常 1停用）')
    del_flag: Mapped[Optional[str]] = mapped_column(CHAR(1), server_default=text("'0'"), comment='删除标志（0代表存在 2代表删除）')
    login_ip: Mapped[Optional[str]] = mapped_column(String(128), server_default=text("''"), comment='最后登录IP')
    login_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='最后登录时间')
    create_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='创建者')
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    update_by: Mapped[Optional[str]] = mapped_column(String(64), server_default=text("''"), comment='更新者')
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    remark: Mapped[Optional[str]] = mapped_column(String(500), comment='备注')


class SysUserPostPo(db.Model):
    __tablename__ = 'sys_user_post'
    __table_args__ = {'comment': '用户与岗位关联表'}

    user_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='用户ID')
    post_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='岗位ID')


class SysUserRolePo(db.Model):
    __tablename__ = 'sys_user_role'
    __table_args__ = {'comment': '用户和角色关联表'}

    user_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='用户ID')
    role_id: Mapped[int] = mapped_column(BIGINT(20), primary_key=True, comment='角色ID')
