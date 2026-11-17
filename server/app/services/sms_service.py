# -*- coding: utf-8 -*-
"""
短信验证码服务

【2026-11-15 新增】用于「忘记密码」的验证码下发与校验。

渠道策略：
- 默认 sms_provider=mock（开发/演示渠道）：
  * APP_ENV=development 时验证码会随响应返回 demoCode，并写日志，方便本地联调；
  * 生产环境不会返回验证码，而是直接提示「短信服务未配置」，避免出现“假装发送成功”。
- 接入真实渠道时实现 SmsProvider.send 并注册到 _PROVIDERS（如阿里云/腾讯云短信）。

存储：Redis 优先，Redis 不可用时自动降级进程内存（见 app/core/redis_client.py）。
"""
import json
import logging
import re
import secrets

from app.core.config import settings
from app.core.redis_client import (
    CacheKeys,
    CacheTTL,
    kv_delete,
    kv_get,
    kv_incr,
    kv_setex,
    kv_ttl,
)

logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
CODE_MAX_TRIES = 5


class SmsProvider:
    """短信渠道接口"""

    name = "base"

    def send(self, phone: str, code: str):
        raise NotImplementedError


class MockSmsProvider(SmsProvider):
    """开发渠道：不真正发短信，只打日志"""

    name = "mock"

    def send(self, phone: str, code: str):
        logger.info("[SMS-MOCK] 手机号 %s 的验证码：%s", phone, code)


_PROVIDERS = {
    "mock": MockSmsProvider(),
}


def _is_production() -> bool:
    return str(settings.app_env or "").strip().lower() not in (
        "development", "dev", "local", "test",
    )


def _get_provider() -> SmsProvider:
    provider = _PROVIDERS.get(str(settings.sms_provider or "").strip().lower())
    if provider is None:
        raise RuntimeError("短信渠道未配置")
    # 生产环境不允许用 mock 假装发送
    if provider.name == "mock" and _is_production():
        raise RuntimeError("短信服务未配置，请联系管理员")
    return provider


class SmsService:
    """短信验证码：发送 / 校验"""

    @staticmethod
    def send_code(phone: str, scene: str = "reset") -> dict:
        """
        发送验证码。
        返回 {"expireIn": 秒}，开发渠道额外返回 {"demoCode": "123456"}。
        """
        phone = (phone or "").strip()
        scene = (scene or "reset").strip().lower() or "reset"
        if not PHONE_RE.match(phone):
            raise ValueError("请输入正确的手机号")
        if scene not in ("reset", "login"):
            scene = "reset"

        # 60 秒内重复发送直接拦截
        if kv_get(CacheKeys.sms_limit(phone)):
            raise ValueError("验证码发送过于频繁，请稍后再试")

        # 单日发送上限
        sent_today = int(kv_get(CacheKeys.sms_count(phone)) or 0)
        if sent_today >= int(settings.sms_daily_limit):
            raise ValueError("今日验证码发送次数已达上限，请明天再试")

        provider = _get_provider()
        length = max(4, min(8, int(settings.sms_code_length or 6)))
        code = "".join(secrets.choice("0123456789") for _ in range(length))

        payload = json.dumps({"code": code, "scene": scene, "tries": 0})
        expire_seconds = max(1, int(settings.sms_code_expire_minutes)) * 60
        kv_setex(CacheKeys.sms_code(phone), expire_seconds, payload)
        kv_setex(CacheKeys.sms_limit(phone), CacheTTL.SMS_LIMIT, "1")
        kv_incr(CacheKeys.sms_count(phone), CacheTTL.SMS_COUNT)

        provider.send(phone, code)
        result = {"expireIn": expire_seconds}
        if provider.name == "mock":
            # 仅开发环境回传，生产环境不会走到这里（_get_provider 已拦截）
            result["demoCode"] = code
        return result

    @staticmethod
    def verify_code(phone: str, code: str, scene: str = "reset") -> bool:
        """校验验证码；校验成功即作废，失败累计次数，超过 5 次也作废"""
        phone = (phone or "").strip()
        code = (code or "").strip()
        scene = (scene or "reset").strip().lower() or "reset"
        if not PHONE_RE.match(phone) or not code:
            return False

        key = CacheKeys.sms_code(phone)
        raw = kv_get(key)
        if not raw:
            return False
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            kv_delete(key)
            return False

        if data.get("scene") != scene:
            return False
        if int(data.get("tries", 0)) >= CODE_MAX_TRIES:
            kv_delete(key)
            return False

        if secrets.compare_digest(str(data.get("code", "")), code):
            kv_delete(key)
            return True

        data["tries"] = int(data.get("tries", 0)) + 1
        ttl = kv_ttl(key)
        kv_setex(key, ttl if ttl > 0 else int(settings.sms_code_expire_minutes) * 60,
                 json.dumps(data))
        return False
