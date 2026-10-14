# -*- coding: utf-8 -*-
"""
内存版 Redis（用于移除 Redis 外部依赖）。

实现 Redis 常用接口的内存子集，接口兼容 redis.Redis，使得项目在
不安装 Redis 的情况下也能独立运行（单机打包交付场景）。

仅用于单机/演示场景：数据保存在内存中，进程退出即清空。
"""

import fnmatch
import threading
import time


class MemoryRedis:
    """内存版 Redis，接口兼容 redis.Redis 常用方法。"""

    def __init__(self):
        self._data = {}      # key -> value（字符串或 dict，用于 hash/zset）
        self._expire = {}    # key -> 过期时间戳
        self._lock = threading.RLock()

    # ---- 内部工具 ----
    def _expired(self, key):
        exp = self._expire.get(key)
        return exp is not None and time.time() > exp

    def _cleanup(self):
        now = time.time()
        for k in list(self._expire):
            if self._expire[k] <= now:
                self._data.pop(k, None)
                self._expire.pop(k, None)

    def _to_str(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    def _to_bytes(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value.encode('utf-8')
        return value

    # ---- String ----
    def get(self, key):
        with self._lock:
            if self._expired(key):
                self._data.pop(key, None)
                self._expire.pop(key, None)
                return None
            return self._data.get(key)

    def set(self, key, value, ex=None, px=None):
        with self._lock:
            self._data[key] = self._to_str(value)
            if ex:
                if hasattr(ex, 'total_seconds'):
                    ex = ex.total_seconds()
                self._expire[key] = time.time() + ex
            elif px:
                self._expire[key] = time.time() + px / 1000.0
            else:
                self._expire.pop(key, None)
            return True

    def setex(self, key, ex, value):
        return self.set(key, value, ex=ex)

    def delete(self, *keys):
        with self._lock:
            n = 0
            for k in keys:
                if k in self._data:
                    self._data.pop(k, None)
                    self._expire.pop(k, None)
                    n += 1
            return n

    def keys(self, pattern='*'):
        with self._lock:
            self._cleanup()
            return [k for k in self._data if fnmatch.fnmatch(str(k), pattern)]

    def incr(self, key, amount=1):
        with self._lock:
            if self._expired(key):
                self._data[key] = '0'
                self._expire.pop(key, None)
            val = int(self._data.get(key, '0') or '0') + amount
            self._data[key] = str(val)
            return val

    def expire(self, key, seconds):
        with self._lock:
            self._expire[key] = time.time() + seconds
            return True

    def ttl(self, key):
        with self._lock:
            if key not in self._data:
                return -2
            exp = self._expire.get(key)
            if exp is None:
                return -1
            return max(0, int(exp - time.time()))

    # ---- Hash ----
    def hincrby(self, name, key, amount=1):
        with self._lock:
            h = self._data.setdefault(name, {})
            if not isinstance(h, dict):
                h = {}
                self._data[name] = h
            val = int(h.get(key, 0) or 0) + amount
            h[key] = val
            return val

    def hgetall(self, name):
        with self._lock:
            h = self._data.get(name, {})
            if isinstance(h, dict):
                return {str(k): str(v) for k, v in h.items()}
            return {}

    def hdel(self, name, *keys):
        with self._lock:
            h = self._data.get(name, {})
            if isinstance(h, dict):
                for k in keys:
                    h.pop(k, None)
            return len(keys)

    # ---- ZSet ----
    def zincrby(self, name, amount, value):
        with self._lock:
            z = self._data.setdefault(name, {})
            if not isinstance(z, dict):
                z = {}
                self._data[name] = z
            val = float(z.get(value, 0) or 0) + amount
            z[value] = val
            return val

    def zrevrange(self, name, start, end):
        with self._lock:
            z = self._data.get(name, {})
            if isinstance(z, dict):
                items = sorted(z.items(), key=lambda x: x[1], reverse=True)
                return [str(k) for k, _v in items[start:end + 1]]
            return []

    # ---- 其他 ----
    def flushdb(self):
        with self._lock:
            self._data.clear()
            self._expire.clear()
            return True

    def exists(self, *keys):
        with self._lock:
            return sum(1 for k in keys if k in self._data and not self._expired(k))

    # ---- 监控信息（兼容 redis.Redis，供缓存监控页使用）----
    def info(self, section=None):
        with self._lock:
            self._cleanup()
            if section == 'commandstats':
                return {}
            return {
                'redis_version': 'memory-1.0',
                'connected_clients': 1,
                'used_memory': 0,
                'used_memory_human': '0B',
                'keyspace_hits': 0,
                'keyspace_misses': 0,
            }

    def dbsize(self):
        with self._lock:
            self._cleanup()
            return len(self._data)

    # ---- 兼容别名（旧版封装方法，避免死代码调用时 AttributeError）----
    def get_cache_object(self, key):
        return self.get(key)

    def delete_object(self, key):
        return self.delete(key)


# 全局内存 Redis 单例（进程内共享）
memory_redis = MemoryRedis()
