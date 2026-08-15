# -*- coding: utf-8 -*-
# @Author  : shaw-lee

from typing_extensions import Annotated
from pydantic import BeforeValidator, Field, SecretStr

from owl_common.base.transformer import str_to_int
from owl_common.base.model import VoModel


class LoginBody(VoModel):
    
    username: Annotated[str, Field(..., example='admin')]
    
    password: Annotated[SecretStr, Field(..., example='admin')]
    
    code: Annotated[str, Field(default=None, example='1213')]
    
    uuid: Annotated[str, Field(default=None, example='1234567890')]
    
    
class RegisterBody(LoginBody):
    
    pass
