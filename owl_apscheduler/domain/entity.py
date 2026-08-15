# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from datetime import datetime
from typing import Optional
from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from owl_common.base.model import BaseEntity, AuditEntity
from owl_common.base.transformer import str_to_int, to_datetime
from owl_common.base.schema_vo import VoAccess
from owl_apscheduler.constant import DATETIME_FORMAT


class SysJob(AuditEntity):
    
    job_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(default=None)
    ]
    
    job_name: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    job_group: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    invoke_target: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    cron_expression: Optional[str] = None
    
    misfire_policy: Optional[str] = None
    
    concurrent: Optional[str] = None
    
    status: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    remark: Optional[str] = None
    
    # 创建时间
    create_time: Annotated[
        Optional[datetime],
        BeforeValidator(to_datetime(DATETIME_FORMAT)),
        Field(default=None,vo=VoAccess(body=False))
    ]
    
    # 更新时间
    update_time: Annotated[
        Optional[datetime],
        BeforeValidator(to_datetime(DATETIME_FORMAT)),
        Field(default=None,vo=VoAccess(body=False))
    ]
    
    @property
    def job_key(self):
        return f"{self.job_id}_{self.job_group}"


class SysJobLog(BaseEntity):
    
    job_log_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int)
    ]
    
    job_name: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    job_group: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    invoke_target: Optional[str] = None
    
    job_message: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    status: Annotated[
        Optional[str],
        Field(default=None,vo=VoAccess(query=True))
    ]
    
    exception_info: Optional[str] = None
    
    # 创建时间
    create_time: Annotated[
        Optional[datetime],
        BeforeValidator(to_datetime()),
        Field(default=None,vo=VoAccess(body=False,query=True))
    ]
