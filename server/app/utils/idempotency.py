# -*- coding: utf-8 -*-
"""
幂等防重（idempotency）—— 安全合规批次新增

用途：
- habit 打卡：同一用户同一习惯同一天，重复点击只生效一次（原有「查今日记录」的
  上一道保险之外，再加一道并发窗口内的硬闸门）；
- chat 发消息：同一用户相同内容在短窗口内重复提交，只处理一次。

实现：进程内 TTL 字典（单进程 uvicorn 部署够用；多实例部署时可平滑替换为
Redis SETNX，接口签名保持不变）。
"""
import threading
import time
from typing import Dict, Optional, Tuple

_lock = threading.Lock()
_store: Dict[str, float] = {}   # key -> expire_at (time.monotonic)

# 清理阈值：超过这个数量才触发一次全表清理，避免每次加锁扫描
_CLEAN_THRESHOLD = 4096


def _cleanup_locked(now: float) -> None:
    """清理过期 key（调用方需已持有锁）"""
    expired = [k for k, exp in _store.items() if exp <= now]
    for k in expired:
        _store.pop(k, None)


def try_acquire(key: str, ttl_seconds: int = 60) -> bool:
    """
    尝试占住一个幂等 key。
    - 首次调用返回 True（业务继续执行）；
    - TTL 内重复调用返回 False（业务方直接拒绝：视为重复提交）。
    """
    if not key:
        return True
    now = time.monotonic()
    with _lock:
        if len(_store) > _CLEAN_THRESHOLD:
            _cleanup_locked(now)
        exp = _store.get(key)
        if exp is not None and exp > now:
            return False
        _store[key] = now + max(int(ttl_seconds), 1)
        return True


def release(key: str) -> None:
    """业务失败时主动释放，允许用户立刻重试"""
    if not key:
        return
    with _lock:
        _store.pop(key, None)


def checkin_key(user_id: int, habit_id: int, day: str = "") -> str:
    """打卡幂等 key（day 不传默认今天，调用方一般自己传 date.today().isoformat()）"""
    return f"checkin:{user_id}:{habit_id}:{day}"


def chat_key(user_id: int, content: str, window_seconds: int = 10) -> Tuple[str, int]:
    """
    聊天幂等 key：同一用户 + 内容指纹，短窗口内去重。
    返回 (key, window_seconds)，由调用方 try_acquire(key, window_seconds)。
    """
    try:
        import hashlib
        fingerprint = hashlib.md5((content or "").encode("utf-8")).hexdigest()[:16]
    except Exception:
        fingerprint = str(abs(hash(content or "")))[:16]
    return f"chat:{user_id}:{fingerprint}", window_seconds
