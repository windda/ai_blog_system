# -*- coding: utf-8 -*-
"""
一次性迁移脚本：MySQL -> SQLite
将 ry-vue-py 库的数据迁移到 app.db（用于打包交付场景）。
"""
from sqlalchemy import create_engine, MetaData, inspect, text

MYSQL_URL = 'mysql+pymysql://root:123456@127.0.0.1/ry-vue-py?charset=utf8mb4'
SQLITE_URL = 'sqlite:///instance/app.db'

mysql = create_engine(MYSQL_URL)
sqlite = create_engine(SQLITE_URL)

meta = MetaData()
meta.reflect(bind=mysql)

# 获取 SQLite 已有表（db.create_all 建的表）
sqlite_tables = set(inspect(sqlite).get_table_names())

with sqlite.begin() as conn, mysql.connect() as mconn:
    for table in meta.sorted_tables:
        if table.name not in sqlite_tables:
            print(f'跳过 {table.name}（SQLite 无此表）')
            continue
        rows = mconn.execute(table.select()).fetchall()
        if not rows:
            continue
        cols = [c.name for c in table.columns]
        ok = 0
        for row in rows:
            d = dict(zip(cols, row))
            # LONGBLOB/bytes 转 str，避免 SQLite 绑定问题
            for k, v in d.items():
                if isinstance(v, bytes):
                    d[k] = v.decode('utf-8', errors='ignore')
            try:
                conn.execute(table.insert().values(**d))
                ok += 1
            except Exception:
                pass
        print(f'表 {table.name}: {ok}/{len(rows)} 条')
print('迁移完成')
