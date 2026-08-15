# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional
from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from owl_common.base.transformer import str_to_int
from owl_common.base.model import AuditEntity, VoAccess


class BlogCategory(AuditEntity):
    """博客分类"""
    
    category_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0, default=None)
    ]
    
    category_name: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]
    
    order_num: Optional[int] = None
    
    status: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]


class BlogTag(AuditEntity):
    """博客标签"""
    
    tag_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0, default=None)
    ]
    
    tag_name: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]
    
    order_num: Optional[int] = None


class BlogArticle(AuditEntity):
    """博客文章"""
    
    article_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0, default=None)
    ]
    
    title: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]
    
    content: Optional[str] = None
    
    summary: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]
    
    cover_image: Optional[str] = None
    
    category_id: Annotated[Optional[int], Field(default=None, vo=VoAccess(query=True))]
    
    author_id: Optional[int] = None
    
    status: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ]
    
    is_top: Optional[str] = None
    
    view_count: Optional[int] = None
    
    like_count: Optional[int] = None
    
    # 非数据库字段 - 关联查询用
    category_name: Annotated[
        Optional[str],
        Field(default=None)
    ] = None
    
    author_name: Annotated[
        Optional[str],
        Field(default=None)
    ] = None
    
    tags: Annotated[
        Optional[List['BlogTag']],
        Field(default=None)
    ] = None
    
    tag_ids: Annotated[
        Optional[List[int]],
        Field(default=None, exclude=True, vo=VoAccess(body=True))
    ] = None


class BlogArticleTag:
    """博客文章标签关联"""
    
    article_id: int
    tag_id: int


class BlogColumn(AuditEntity):
    """博客专栏（聚合作者的全部文章）"""

    column_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0, default=None)
    ]

    column_name: Annotated[
        Optional[str],
        Field(max_length=100, vo=VoAccess(query=True))
    ]

    description: Annotated[
        Optional[str],
        Field(max_length=500, default='')
    ]

    cover_image: Optional[str] = None

    author_id: Optional[int] = None

    status: Annotated[
        Optional[str],
        Field(max_length=1, default='0', vo=VoAccess(query=True))
    ]

    order_num: Optional[int] = 0

    # 非数据库字段 - 联表查询
    author_name: Optional[str] = None
    article_count: Optional[int] = 0


class BlogComment(AuditEntity):
    """博客评论"""
    
    comment_id: Annotated[
        Optional[int],
        BeforeValidator(str_to_int),
        Field(gt=0, default=None)
    ]
    
    article_id: Optional[int] = None
    
    parent_id: Optional[int] = 0
    
    content: Optional[str] = None
    
    author_name: Optional[str] = None
    
    author_email: Optional[str] = None
    
    user_id: Optional[int] = None
    
    status: Annotated[
        Optional[str],
        Field(default=None, vo=VoAccess(query=True))
    ] = None
    
    create_time: Optional[datetime] = None
    
    update_time: Optional[datetime] = None
    
    # 非数据库字段
    children: Optional[List['BlogComment']] = None
    article_title: Optional[str] = None  # 联表查询时填充