
from typing import Any, Tuple
from flask import Flask, g, has_app_context
import sqlalchemy as sa
import sqlalchemy.event as sa_event

from owl_common.base.model import PageModel
from owl_common.sqlalchemy.query import Pagination


def init_listener(engine: sa.engine.Engine) -> None:
    """
    初始化监听器，监听SQL执行前的事件

    Args:
        engine (sa.engine.Engine): 数据库引擎
    """
    sa_event.listen(engine, "before_execute", before_execute_listening, retval=True)
    

def before_execute_listening(engine, clauseelement, multiparams,params) -> Tuple[Any,Any,Any]:
    """
    SQL执行前的监听器

    Args:
        engine (sa.engine.Engine): 数据库引擎
        clauseelement (sa.sql.ClauseElement): SQL语句
        multiparams (Any): 多参数
        params (Any): 参数

    Returns:
        Tuple[Any,Any,Any]: 新的SQL语句，多参数，参数
    """
    raw_input = clauseelement, multiparams, params
    if not has_app_context():
        return raw_input

    if isinstance(clauseelement, sa.Select):
        
        if not "criterian_meta" in g:
            return raw_input
        
        if not g.criterian_meta or not g.criterian_meta.page:
            return raw_input
        
        page:PageModel = g.criterian_meta.page
        if page.stmt != clauseelement:
            return raw_input
        
        pagination = Pagination(
            page_num=page.page_num,
            page_size=page.page_size
        )
        
        new_clauseelement = pagination.rebuild(clauseelement)
        page.total = pagination.compute_count(clauseelement,engine)
        new_output = new_clauseelement, multiparams, params
        return new_output
    return raw_input
    