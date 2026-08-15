from functools import wraps
from typing import Any
from enum import Enum
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session


class Propagation(Enum):
    
    # 不存在事务，则创建事务，如果存在事务，则加入该事务
    REQUIRED = 'REQUIRED'
    
    # 不存在事务，则创建新事务，如果存在事务，则创建新嵌套事务
    REQUIRES_NEW = 'REQUIRES_NEW'
    
    # 创建新嵌套事务
    NESTED = 'NESTED'
    
    # 存在事务或者不存在事务，都执行该操作
    SUPPORTS = 'SUPPORTS'
    
    # 如果存在事务，则立即结束事务
    NOT_SUPPORTED = 'NOT_SUPPORTED'
    
    # 如果不存在事务，则抛出异常
    MANDATORY = 'MANDATORY'
    
    # 如果存在事务，则抛出异常
    NEVER = 'NEVER'
    

class Transactional:
    
    def __init__(self,
        session:scoped_session, 
        propagation=Propagation.REQUIRED,
        ):
        self.session = session
        self.propagation = propagation
    
    def __call__(self, func) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return TransactionWrapper(
                func,
                session=self.session,
                propagation=self.propagation
                )(*args, **kwargs)
        return wrapper

    def prepare(self):
        pass
    


class TransactionWrapper:
    
    def __init__(self,func ,session:scoped_session | Session, propagation:Propagation=Propagation.REQUIRED):
        self.func = func
        self.session:Session = session._proxied \
            if isinstance(session, scoped_session) else session
        self.propagation = propagation
    
    def top_transaction(self) -> bool:
        '''
        判断当前事务是否为顶层事务
        
        :return: bool
        '''
        return self.session.get_transaction() is self.session._transaction
    
    def prepare_transaction(self):
        '''
        准备工作：提前关闭顶层查询事务
        '''
        if self.session.in_transaction() and self.top_transaction():
            if self.session._trans_context_manager is None:
                self.session.close()
    
    def __call__(self, *args, **kwargs) -> Any:
        if self.propagation == Propagation.REQUIRED:
            self.prepare_transaction()
            if self.session.in_transaction():
                rv = self.func(*args, **kwargs)
            else:
                with self.session.begin():
                    rv = self.func(*args, **kwargs)
        elif self.propagation == Propagation.REQUIRES_NEW:
            if self.session.in_transaction():
                with self.session.begin_nested():
                    rv = self.func(*args, **kwargs)
            else:
                with self.session.begin():
                    rv = self.func(*args, **kwargs)
        elif self.propagation == Propagation.NESTED:
            with self.session.begin_nested():
                rv = self.func(*args, **kwargs)
        elif self.propagation == Propagation.SUPPORTS:
            if self.session.in_transaction():
                rv = self.func(*args, **kwargs)
            else:
                rv = self.func(*args, **kwargs)
        elif self.propagation == Propagation.NOT_SUPPORTED:
            if self.session.in_transaction():
                self.session.commit()  # Or handle appropriately
            rv = self.func(*args, **kwargs)
        elif self.propagation == Propagation.MANDATORY:
            if self.session.in_transaction():
                rv = self.func(*args, **kwargs)
            else:
                raise Exception("No existing transaction found")
        elif self.propagation == Propagation.NEVER:
            if self.session.in_transaction():
                raise Exception("Existing transaction found")
            rv = self.func(None, *args, **kwargs)
        else:
            raise ValueError(f"Unknown propagation level: {self.propagation}")            
        return rv