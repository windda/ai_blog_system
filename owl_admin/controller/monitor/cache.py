# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from owl_common.base.model import AjaxResponse
from owl_common.descriptor.serializer import JsonSerializer
from owl_framework.domain.entity import RedisCache
from owl_framework.descriptor.permission import HasPerm, PreAuthorize
from owl_admin.ext import redis_cache
from ... import reg


@reg.api.route('/monitor/cache',methods=['GET'])
@PreAuthorize(HasPerm("monitor:cache:list"))
@JsonSerializer()
def monitor_cache():
    '''
        获取缓存信息
    '''
    cache = RedisCache.from_connection(redis_cache)
    return AjaxResponse.from_success(data = cache)