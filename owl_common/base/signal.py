# -*- coding: utf-8 -*-
# @Author  : shaw-lee
 
from blinker import Namespace


descriptor_singals = Namespace()

log_signal = descriptor_singals.signal('log')

module_initailize = descriptor_singals.signal('module_initailize')

app_completed = descriptor_singals.signal('app_completed')


