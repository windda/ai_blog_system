# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from enum import Enum

DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


class ScheduleStatus(Enum):
    
    NORMAL = "0"
    
    PAUSED = "1"
    

class ScheduleConstant:
    
    MISFIRE_DEFAULT = "0"
    
    MISFIRE_IGNORE_MISFIRES = "1"
    
    MISFIRE_FIRE_AND_PROCEED = "2"
    
    MISFIRE_DO_NOTHING = "3"
    
    ALLOW_CONCURRENT = "0"
    
    FORBIDDEN_CONCURRENT = "1"
    
    JOB_WHITELIST_STR = { "owl_apscheduler" }
    
