# -*- coding: utf-8 -*-
# @Author  : shaw-lee

EXECUTORS = {
    "default": {"type": "threadpool", "max_workers": 20},
    "processpool": {"type": "processpool", "max_workers": 5},
}

TIMEZONE = "UTC"

JOB_DEFAULTS = {
    "coalesce": True,
    "max_instances": 10,
    "misfire_grace_time": 300,
}