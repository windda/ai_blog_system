# -*- coding: utf-8 -*-

"""
文章服务层。

公开文章列表使用 Redis 缓存（5 分钟过期），降低数据库压力；
新增/修改/删除文章时自动清除缓存，保证数据一致性。
"""

import json
from typing import List, Optional

from owl_common.sqlalchemy.transaction import Transactional
from owl_blog.domain.entity import BlogArticle
from owl_blog.mapper.article import BlogArticleMapper
from owl_admin.ext import db, redis_cache

# 缓存key前缀
CACHE_KEY_PUB_LIST = "blog:article:pub_list"


class BlogArticleService:

    @classmethod
    def select_article_by_id(cls, id: int) -> Optional[BlogArticle]:
        return BlogArticleMapper.select_article_by_id(id)

    @classmethod
    def select_article_list(cls, query: BlogArticle) -> List[BlogArticle]:
        """
        查询文章列表（公开列表走Redis缓存）
        """
        # 只有查"已发布+无筛选条件"时才走缓存
        is_pub_list = (
            query is not None
            and query.status == '1'
            and query.title is None
            and query.category_id is None
            and query.author_id is None
        )

        if is_pub_list:
            try:
                cached = redis_cache.get(CACHE_KEY_PUB_LIST)
                if cached:
                    data = json.loads(cached)
                    return [BlogArticle(**item) for item in data]
            except Exception:
                pass  # 缓存异常不影响主流程，继续查数据库

        # 查数据库
        rows = BlogArticleMapper.select_article_list(query)

        # 写入缓存
        if is_pub_list and rows:
            try:
                data = [r.model_dump(mode='json') for r in rows]
                redis_cache.setex(CACHE_KEY_PUB_LIST, 300, json.dumps(data))  # 5分钟过期
            except Exception:
                pass

        return rows

    @classmethod
    def _clear_pub_cache(cls):
        """清除公开列表缓存（新增/修改/删除时调用）"""
        try:
            redis_cache.delete(CACHE_KEY_PUB_LIST)
        except Exception:
            pass

    @classmethod
    @Transactional(db.session)
    def insert_article(cls, body: BlogArticle) -> bool:
        article_id = BlogArticleMapper.insert_article(body)
        if article_id and body.tag_ids:
            BlogArticleMapper.insert_article_tags(article_id, body.tag_ids)
        cls._clear_pub_cache()  # 新增后清缓存
        return article_id > 0

    @classmethod
    @Transactional(db.session)
    def update_article(cls, body: BlogArticle) -> bool:
        flag = BlogArticleMapper.update_article(body) > 0
        if flag and body.tag_ids is not None:
            BlogArticleMapper.delete_article_tags(body.article_id)
            if body.tag_ids:
                BlogArticleMapper.insert_article_tags(body.article_id, body.tag_ids)
        cls._clear_pub_cache()  # 修改后清缓存
        return flag

    @classmethod
    @Transactional(db.session)
    def delete_article_by_id(cls, id: int) -> bool:
        BlogArticleMapper.delete_article_tags(id)
        cls._clear_pub_cache()  # 删除后清缓存
        return BlogArticleMapper.delete_article_by_id(id) > 0

    @classmethod
    @Transactional(db.session)
    def delete_article_by_ids(cls, ids: List[int]) -> bool:
        for id in ids:
            BlogArticleMapper.delete_article_tags(id)
        cls._clear_pub_cache()  # 删除后清缓存
        return BlogArticleMapper.delete_article_by_ids(ids) > 0

    @classmethod
    @Transactional(db.session)
    def increment_view_count(cls, article_id: int):
        BlogArticleMapper.increment_view_count(article_id)