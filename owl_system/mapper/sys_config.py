# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing import List, Optional
from flask import g
from sqlalchemy import delete, insert, select, update

from owl_admin.ext import db
from owl_common.base.model import ExtraModel
from owl_common.sqlalchemy.model import ColumnEntityList
from owl_common.sqlalchemy.transaction import Transactional
from owl_system.domain.entity import SysConfig
from owl_system.domain.po import SysConfigPo


class SysConfigMapper:
    
    """
    配置数据访问层
    """
    
    default_fields = {
        'config_id', 'config_key', 'config_name', 'config_value', 
        'config_type', 'create_time', 'update_time'
    }
    
    default_columns = ColumnEntityList(SysConfigPo, default_fields, False)
    
    @classmethod
    def select_config(cls, config: SysConfig) -> Optional[SysConfig]:
        """
        查询单个配置信息
        
        Args:
            config (SysConfig): 配置信息
        
        Returns:
            Optional[SysConfig]: 配置信息
        """
        criterions = []
        if config.config_id:
            criterions.append(SysConfigPo.config_id == config.config_id)
        if config.config_key:
            criterions.append(SysConfigPo.config_key == config.config_key)
        
        stmt = select(*cls.default_columns) \
            .where(*criterions)
        
        row = db.session.execute(stmt).one_or_none()
        return cls.default_columns.cast(row,SysConfig) if row else None

    @classmethod
    def select_config_list(cls, config: SysConfig) -> List[SysConfig]:
        """
        查询配置列表
        
        Args:
            config (SysConfig): 配置信息
        
        Returns:
            List[SysConfig]: 配置列表
        """
        criterions = []
        if config.config_name:
            criterions.append(SysConfigPo.config_name == config.config_name)
        if config.config_type:
            criterions.append(SysConfigPo.config_type == config.config_type)
        if config.config_key:
            criterions.append(SysConfigPo.config_key == config.config_key)
        if "criterian_meta" in g and g.criterian_meta.extra:
            extra:ExtraModel = g.criterian_meta.extra
            if extra.start_time and extra.end_time:
                criterions.append(SysConfigPo.create_time >= extra.start_time)
                criterions.append(SysConfigPo.create_time <= extra.end_time)
        stmt = select(*cls.default_columns) \
            .where(*criterions) \
            .order_by(SysConfigPo.config_id.desc())
        if "criterian_meta" in g and g.criterian_meta.page:
            g.criterian_meta.page.stmt = stmt
        
        rows = db.session.execute(stmt).all()
        eos = list()
        for row in rows:
            eos.append(cls.default_columns.cast(row,SysConfig))
        return eos

    @classmethod
    def check_config_key_unique(cls, config_key: str) -> Optional[SysConfig]:
        """
        根据键名查询配置信息
        
        Args:
            config_key (str): 键名
        
        Returns:
            Optional[SysConfig]: 配置信息
        """
        stmt = select(*cls.default_columns) \
            .where(SysConfigPo.config_key == config_key) \
            .limit(1)
        row = db.session.execute(stmt).scalar_one_or_none()
        return cls.default_columns.cast(row,SysConfig) if row else None

    @classmethod
    @Transactional(db.session)
    def insert_config(cls, config: SysConfig) -> int:
        """
        新增配置信息
        
        Args:
            config (SysConfig): 配置信息
        
        Returns:
            int: 新增记录的ID
        """
        fields = {
            'config_key', 'config_name', 'config_value', 'config_type',
            'remark', "create_time" , "create_by"
        }
        data = config.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = insert(SysConfigPo).values(data)
        out = db.session.execute(stmt).inserted_primary_key
        return out[0] if out else 0

    @classmethod
    @Transactional(db.session)
    def update_config(cls, config: SysConfig) -> int:
        """
        修改配置信息
        
        Args:
            config (SysConfig): 配置信息
        
        Returns:
            int: 影响的行数
        """
        fields = {
            'config_key', 'config_name', 'config_value', 'config_type',
            'remark', "update_time" , "update_by"
        }
        data = config.model_dump(
            include=fields, exclude_none=True, exclude_unset=True
        )
        stmt = update(SysConfigPo) \
            .where(SysConfigPo.config_id == config.config_id) \
            .values(data)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_config_by_id(cls, config_id: int) -> int:
        """
        根据 ID 删除配置信息
        
        Args:
            config_id (int): 配置 ID
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysConfigPo).where(SysConfigPo.config_id == config_id)
        return db.session.execute(stmt).rowcount

    @classmethod
    @Transactional(db.session)
    def delete_configs_by_ids(cls, config_ids: List[int]) -> int:
        """
        批量删除配置信息
        
        Args:
            config_ids (List[int]): 配置 ID 列表
        
        Returns:
            int: 影响的行数
        """
        stmt = delete(SysConfigPo).where(SysConfigPo.config_id.in_(config_ids))
        return db.session.execute(stmt).rowcount
