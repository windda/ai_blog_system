
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Dict
from flask import g, request
from pydantic import BaseModel
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import BadRequest,UnsupportedMediaType

from owl_common.base.model import BaseEntity, CriterianMeta, ExtraModel, \
    BaseEntity, OrderModel, PageModel, VoValidatorContext
from owl_common.base.schema_vo import BaseSchemaFactory, QuerySchemaFactory


class AbsReqParser(ABC):
    
    @abstractmethod
    def data(self) -> Dict:
        """
        获取请求参数

        Returns:
            Dict: 请求参数字典
        """
    
    @abstractmethod
    def cast_model(self, bo_model:BaseEntity) -> BaseModel:
        """
        适配模型

        Args:
            bo_model (BaseEntity): Vo模型
            src_model (BaseModel): 源模型

        Returns:
            BaseModel: 适配后的模型
        """
    
    @abstractmethod
    def prepare_factory(self, factory:BaseSchemaFactory):
        """
        准备工厂

        Args:
            factory (BaseSchemaFactory): 工厂
        """
    
    @abstractmethod
    def prepare(self):
        """
        准备数据
        """ 

class BaseReqParser(AbsReqParser):
    
    def data(self) -> Dict:
        pass
    
    def cast_model(self, bo_model:BaseEntity) -> BaseModel:
        pass
    
    def prepare_factory(self, factory:BaseSchemaFactory):
        pass

    def prepare(self):
        pass
    

class QueryReqParser(BaseReqParser):

    def __init__(self, context:VoValidatorContext):
        self.context = context
        self.extra_model = ExtraModel
    
    def prepare_factory(self, factory: QuerySchemaFactory):
        if factory.extra_model:
            self.extra_model = factory.extra_model
            
    def prepare(self):
        self.criterian_meta = CriterianMeta()
        g.criterian_meta = self.criterian_meta
    
    def validate_request(self) -> Dict:
        return request.args.to_dict()
    
    def data(self) -> Dict:
        data = self.validate_request().copy()
        if self.context.is_page:
            page = PageModel.model_validate(data,context=self.context)
            if page.model_fields_set:
                self.criterian_meta.page = page
        if self.context.is_sort:
            sort = OrderModel.model_validate(data,context=self.context)
            if sort.model_fields_set:
                self.criterian_meta.sort = sort
        if self.extra_model:
            extra = self.extra_model.model_validate(data,context=self.context)
            if extra.model_fields_set:
                self.criterian_meta.extra = extra
        return data
    
    def cast_model(self, bo_model:BaseEntity) -> BaseModel:
        data = self.data()
        bo = bo_model.model_validate(data)
        return bo
    
    
@dataclass
class PathReqParser(BaseReqParser):
    
    def data(self) -> Dict:
        return request.view_args.copy()
        

@dataclass
class BodyReqParser(BaseReqParser):
    
    minetype: ClassVar[str] = "application/json"

    def __init__(self, context:VoValidatorContext):
        self.context = context
        
    def validate_request(self) -> Dict:
        content_type = request.headers.get("Content-Type", "").lower()
        minetype = content_type.split(";")[0]
        if minetype == self.minetype:
            body: dict | list = request.get_json()
            if not body:
                raise BadRequest(
                    description="在{}, body数据不能为空".format(content_type),
                )
        else:
            raise UnsupportedMediaType(
                description="content-type仅支持application/json"
            )
        return body
    
    def data(self) -> Dict:
        data = self.validate_request().copy()
        return data

    def cast_model(self, bo_model:BaseEntity) -> BaseModel:
        data = self.data()
        bo = bo_model.model_validate(data, context=self.context)
        return bo


@dataclass
class FormUrlencodedQueryReqParser(QueryReqParser):
    
    minetype: ClassVar[str] = "application/x-www-form-urlencoded"
    
    def __init__(self, context:VoValidatorContext):
        super().__init__(context)
    
    def validate_request(self) -> Dict:
        content_type = request.headers.get("Content-Type", "").lower()
        minetype = content_type.split(";")[0]
        if minetype == self.minetype:
            form:ImmutableMultiDict = request.form
            body = form.to_dict()
        else:
            raise UnsupportedMediaType(
                description="除了{},content-type不支持{}".format(self.minetype,minetype)
            )
        return body


@dataclass
class DownloadFileQueryReqParser(FormUrlencodedQueryReqParser):
    
    def __init__(self, context:VoValidatorContext):
        super().__init__(context)


class FormReqParser(BaseReqParser):
    
    minetype: ClassVar[str] = "multipart/form-data"
    
    def __init__(
        self, 
        is_form:bool=True,
        is_query:bool=False,
        is_file:bool|None=None,
        ):
        self.is_form = is_form
        self.is_query = is_query
        self.is_file = is_file
        
    def validate_request(self) -> Dict:
        content_type = request.headers.get("Content-Type", "").lower()
        minetype = content_type.split(";")[0]
        new_data = {}
        if minetype == self.minetype:
            if self.is_form:
                new_data.update(request.form.to_dict())
            if self.is_query:
                new_data.update(request.args.to_dict())
            if self.is_file:
                new_data.update(request.files.to_dict(flat=False))
        else:
            raise UnsupportedMediaType(
                description="除了{},content-type不支持{}".format(self.minetype,minetype)
            )
        return new_data
    
    def data(self) -> Dict:
        data = self.validate_request()
        return data

    
class UploadFileFormReqParser(FormReqParser):
    
    def validate_request(self) -> Dict:
        return super().validate_request()

    def data(self) -> Dict:
        data = self.validate_request()
        return data
    
            
class StreamReqParser(BaseReqParser):

    minetype: ClassVar[str] = "application/octet-stream"

    def data(self, *args, **kwargs) -> Dict:
        pass