# -*- coding: utf-8 -*-
# @Author  : shaw-lee

"""
系统定时任务。

sync_article_pv_to_mysql: 每5分钟将 Redis PV 计数器批量同步到 MySQL，
采用 Redis 原子自增 + 定时批量回写，避免每次阅读都直接写 MySQL。
"""

import traceback
from sqlalchemy import update

from owl_blog.domain.po import BlogArticlePo
from owl_admin.ext import db


def no_args():
    print("无参方法")


def one_args(x):
    print("单个参方法： x: {} ".format(x))


def multiply_args(x, y):
    print("多参方法： x: {} y: {}".format(x, y))


def sync_article_pv_to_mysql():
    """
    定时任务：同步 Redis PV 计数器到 MySQL
    
    执行流程：
    1. 从 Redis Hash `blog:article:pv:counter` 读取所有文章ID及对应的 PV 增量
    2. 逐条 UPDATE MySQL `blog_article` 表的 view_count 字段（累加增量值）
    3. 同步完成后删除 Redis 中的对应 field（避免重复累加）
    4. 整个操作包裹在 try/except 中，Redis 不可用时跳过不报错

    调度配置：
    - interval: 5 minutes
    - misfire_grace_time: 120s（错过2分钟内仍可执行）
    """
    try:
        from owl_admin.ext import redis_cache

        # 1. 读取 Redis Hash 中所有 PV 增量数据
        #    key: blog:article:pv:counter, field: 文章ID, value: 浏览次数增量
        pv_data = redis_cache.hgetall("blog:article:pv:counter")
        if not pv_data:
            return  # 无增量数据，跳过

        synced_count = 0
        for article_id_str, increment_str in pv_data.items():
            try:
                article_id = int(article_id_str)
                increment = int(increment_str)
                if increment <= 0:
                    continue

                # 2. 批量更新 MySQL：通过 SQLAlchemy 累加 view_count
                stmt = (
                    update(BlogArticlePo)
                    .where(BlogArticlePo.article_id == article_id)
                    .values(view_count=BlogArticlePo.view_count + increment)
                )
                db.session.execute(stmt)

                # 3. 删除已同步的 Redis field（HINCRBY 重新从0开始）
                redis_cache.hdel("blog:article:pv:counter", article_id_str)
                synced_count += 1
            except Exception:
                traceback.print_exc()
                continue  # 单条失败不影响其他文章

        # 4. 提交数据库事务
        if synced_count > 0:
            db.session.commit()
            print(f"[PV Sync] 成功同步 {synced_count} 篇文章的 PV 数据到 MySQL")
    except Exception:
        # Redis 不可用或连接异常时静默跳过
        pass