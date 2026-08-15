# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from ... import reg


@reg.api.route("/", methods=["GET"])
def index():
    '''
        首页提示语
    '''
    return "欢迎使用后台管理系统"