from collections import UserDict,UserList
from contextlib import contextmanager
from threading import Lock
from pydantic.dataclasses import dataclass
import sqlalchemy.orm as sa_orm
import sqlalchemy as sa
from sqlalchemy.orm import Session


DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_NUM = 1


class WriteReadLock:
    
    """读写锁实现-写优先"""
    
    def __init__(self):
        self._read_lock = Lock()
        self._write_lock = Lock()
        self._write_count = 0
    
    @contextmanager
    def write_lock(self):
        """
        获取写锁
        """
        try:
            with self._write_lock:
                self._write_count += 1
                if self._write_count == 1:
                    self._read_lock.acquire()
            yield
        finally:
            with self._write_lock:
                self._write_count -= 1
                if self._write_count == 0:
                    self._read_lock.release()
    
    @contextmanager
    def read_lock(self):
        """
        获取读锁
        """
        try:
            self._read_lock.acquire()
            yield
        finally:
            self._read_lock.release()


class SafeUserDict(UserDict):
    
    """使用读写锁的线程安全字典"""
    
    def __init__(self, *args, **kwargs):
        self._lock = WriteReadLock()
        super().__init__(*args, **kwargs)
    
    @contextmanager
    def write(self):
        with self._lock.write_lock():
            yield self

    @contextmanager
    def read(self):
        with self._lock.read_lock():
            yield self


class CriterianDict(SafeUserDict):
    
    pass


    
@dataclass
class Pagination:
    
    page_size: int
    
    page_num: int
    
    def __post_init__(self):
        self.page_size = self.page_size or DEFAULT_PAGE_SIZE
        self.page_num = self.page_num or DEFAULT_PAGE_NUM
    
    @property
    def offset(self) -> int:
        '''
        偏移量
        
        Returns:
            int: 偏移量
        '''
        return (self.page_num - 1) * self.page_size
    
    def compute_count(self,stmt:sa.Select,session:Session) -> int:
        """
        计算总数

        Args:
            stmt (sa.Select): 选择表达式
            session (Session): 数据库会话

        Returns:
            int: 总数
        """
        sub = stmt.options(sa_orm.lazyload("*")).order_by(None).subquery()
        count_stmt = sa.select(sa.func.count()).select_from(sub)
        return session.execute(count_stmt).scalar_one_or_none() or 0
    
    def rebuild(self,stmt:sa.Select) -> sa.Select:
        """
        重新构建选择表达式 

        Args:
            stmt (sa.Select): 选择表达式

        Returns:
            sa.Select: 选择表达式
        """
        new_stmt = stmt.limit(self.page_size).offset(self.offset)
        return new_stmt

