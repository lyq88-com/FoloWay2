# -*- coding: utf-8 -*-
"""
Redis 客户端 - 统一缓存键管理

【2026-11-15 增量】新增带进程内存兜底的 KV 访问层（kv_get/kv_setex/kv_delete/kv_incr/kv_ttl）。
- Redis 可用时走 Redis（多进程共享）；
- Redis 未启动/连不上时自动降级为进程内存，保证验证码、登录限流等功能可用，
  不会因为 Redis 缺失导致登录链路报错。
目前的使用方：app/services/sms_service.py（短信验证码）、app/core/rate_limit.py（登录限流）。
"""
import logging
import threading
import time

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis 连接
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,   # 自动解码为字符串
    socket_timeout=5,
    socket_connect_timeout=5,
)

# ↓↓↓ 新增：运行期 KV 存储（Redis 优先，内存兜底） ↓↓↓
_memory_store = {}          # key -> (value, expire_at)
_memory_lock = threading.Lock()
_redis_usable = None        # None=未探测 True=可用 False=不可用


def _redis_ready() -> bool:
    """惰性探测 Redis 是否可用，只探测/告警一次"""
    global _redis_usable
    if _redis_usable is None:
        try:
            _redis_usable = bool(redis_client.ping())
        except Exception as exc:
            logger.warning("Redis 不可用，验证码/登录限流已降级为进程内存: %s", exc)
            _redis_usable = False
    return bool(_redis_usable)


def _mark_redis_down(exc: Exception):
    """Redis 运行期异常后标记不可用，后续请求直接走内存兜底"""
    global _redis_usable
    logger.warning("Redis 操作失败，改用内存兜底: %s", exc)
    _redis_usable = False


def _mem_purge(key: str):
    """清理已过期的内存键（调用方需持有锁）"""
    item = _memory_store.get(key)
    if item and item[1] and item[1] <= time.time():
        _memory_store.pop(key, None)


def kv_get(key: str):
    """读取字符串值，不存在/已过期返回 None"""
    if _redis_ready():
        try:
            return redis_client.get(key)
        except Exception as exc:
            _mark_redis_down(exc)
    with _memory_lock:
        _mem_purge(key)
        item = _memory_store.get(key)
        return item[0] if item else None


def kv_setex(key: str, ttl: int, value: str):
    """写入并设置过期时间（秒）"""
    if _redis_ready():
        try:
            redis_client.setex(key, max(1, int(ttl)), value)
            return
        except Exception as exc:
            _mark_redis_down(exc)
    with _memory_lock:
        _memory_store[key] = (str(value), time.time() + max(1, int(ttl)))


def kv_delete(key: str):
    """删除键"""
    if _redis_ready():
        try:
            redis_client.delete(key)
            return
        except Exception as exc:
            _mark_redis_down(exc)
    with _memory_lock:
        _memory_store.pop(key, None)


def kv_incr(key: str, ttl: int) -> int:
    """自增计数（键不存在时创建并设置过期时间），返回自增后的值"""
    if _redis_ready():
        try:
            count = int(redis_client.incr(key))
            if count == 1:
                redis_client.expire(key, max(1, int(ttl)))
            return count
        except Exception as exc:
            _mark_redis_down(exc)
    with _memory_lock:
        _mem_purge(key)
        item = _memory_store.get(key)
        if item:
            count = int(item[0]) + 1
            _memory_store[key] = (str(count), item[1])
            return count
        _memory_store[key] = ("1", time.time() + max(1, int(ttl)))
        return 1


def kv_ttl(key: str) -> int:
    """剩余存活秒数，-1 表示不存在/已过期"""
    if _redis_ready():
        try:
            ttl = int(redis_client.ttl(key))
            return ttl if ttl > 0 else -1
        except Exception as exc:
            _mark_redis_down(exc)
    with _memory_lock:
        _mem_purge(key)
        item = _memory_store.get(key)
        if not item:
            return -1
        return max(1, int(item[1] - time.time()))
# ↑↑↑ 新增结束 ↑↑↑


class CacheKeys:
    """Redis 缓存键定义

    2026-11-16 清理：仅保留当前实际使用的键。
    原登录 Token / 习惯 / 对话上下文 等键定义从未被任何代码启用，已移除，避免“空转配置”误导。
    """

    # 短信验证码
    @staticmethod
    def sms_code(phone: str) -> str:
        return f"ahp:sms:code:{phone}"

    @staticmethod
    def sms_limit(phone: str) -> str:
        return f"ahp:sms:limit:{phone}"

    @staticmethod
    def sms_count(phone: str) -> str:
        return f"ahp:sms:count:{phone}"

    # 接口限流
    @staticmethod
    def rate_limit(ip: str, api: str) -> str:
        return f"ahp:rate:{ip}:{api}"


# 过期时间常量(秒) —— 仅保留实际使用的项
class CacheTTL:
    SMS_LIMIT = 60              # 60秒
    SMS_COUNT = 86400           # 24小时
