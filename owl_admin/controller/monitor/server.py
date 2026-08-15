# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.base.model import AjaxResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_framework.domain.entity import Server
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from ... import reg


@reg.api.route('/monitor/server',methods=['GET'])
@PreAuthorize(HasPerm("monitor:server:list"))
@JsonSerializer()
def monitor_server_get():
    '''
        获取服务器信息
    '''
    server = Server.from_module()
    return AjaxResponse.from_success(data = server)
