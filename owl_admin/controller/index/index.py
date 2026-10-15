# -*- coding: utf-8 -*-
# @Author  : shaw-lee

import os

from flask import send_from_directory

from ... import reg


@reg.api.route("/", methods=["GET"])
def index():
    '''
        首页：打包版返回前端 index.html；前端未构建时返回提示语
    '''
    from owl_admin.app import _resolve_frontend_dir
    frontend_dir = _resolve_frontend_dir()
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(frontend_dir, 'index.html')
    return "欢迎使用后台管理系统"


@reg.api.route("/health", methods=["GET"])
def health():
    '''健康检查：返回 200，无鉴权、不查数据库'''
    return "ok"