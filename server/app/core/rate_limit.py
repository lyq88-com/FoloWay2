# -*- coding: utf-8 -*-
"""
登录失败限流

【2026-11-15 新增】把 .env 里原有的 RATE_LIMIT_* 配置真正接上：
- 同一「账号 + 客户端 IP」在窗口期内连续失败达到上限后，暂时拒绝登录；
- 窗口期与次数都走配置（默认 5 次 / 15 分钟）；
- 登录成功立即清零，不影响正常用户。

存储复用 app/core/redis_client.py 的 KV 层（Redis 优先，内存兜底），
Redis 未启动时不会影响登录链路。
"""
import math

from app.core.config import settings
from app.core.redis_client import CacheKeys, kv_delete, kv_get, kv_incr, kv_ttl


def _window_seconds() -> int:
    return max(1, int(settings.rate_limit_window_minutes)) * 60


def _max_failures() -> int:
    return max(1, int(settings.rate_limit_login_max))


def _key(account: str, ip: str) -> str:
    account = (account or "").strip().lower()
    ip = (ip or "unknown").strip()
    return CacheKeys.rate_limit(f"{ip}:{account}", "login")


def login_blocked(account: str, ip: str):
    """
    检查是否已被限流。
    返回 (是否拦截, 还需等待的分钟数)
    """
    if not settings.rate_limit_enabled:
        return False, 0
    try:
        failures = int(kv_get(_key(account, ip)) or 0)
    except (TypeError, ValueError):
        failures = 0
    if failures < _max_failures():
        return False, 0
    ttl = kv_ttl(_key(account, ip))
    minutes = max(1, int(math.ceil((ttl if ttl > 0 else _window_seconds()) / 60.0)))
    return True, minutes


def record_login_failure(account: str, ip: str) -> int:
    """记录一次失败，返回窗口期内的失败次数"""
    if not settings.rate_limit_enabled:
        return 0
    return kv_incr(_key(account, ip), _window_seconds())


def clear_login_failures(account: str, ip: str):
    """登录成功后清零"""
    if not settings.rate_limit_enabled:
        return
    kv_delete(_key(account, ip))
