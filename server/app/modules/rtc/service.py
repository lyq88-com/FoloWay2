# -*- coding: utf-8 -*-
"""
RTC 业务层：渠道状态 + 频道 token 签发
=====================================
设计原则（对齐「能力缺口」修复要求）：
- 未配置密钥时显式返回 503 + 原因，前端据此显示「演示模式」，绝不假装接通；
- 频道名由服务端按当前用户派生，客户端无法指定他人的频道（防串台/偷听）；
- uid 强制绑定当前登录用户，token 短 TTL、限流签发；
- App Certificate 只在服务端参与签名，响应里只有公开的 App ID 和 token。
"""
import re
import time

from app.core.config import settings
from app.modules.rtc.token_builder import build_rtc_token, is_valid_app_key

# 频道名白名单：字母数字下划线连字符（Agora 频道名要求）
_CHANNEL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class RTCError(Exception):
    """RTC 业务异常：转成统一响应 code/message"""

    def __init__(self, message: str, code: int = 503):
        super().__init__(message)
        self.message = message
        self.code = code


class RTCService:
    """实时通话渠道服务（当前支持声网 Agora）"""

    SUPPORTED_PROVIDERS = ("none", "agora")

    @staticmethod
    def provider_name() -> str:
        return (settings.rtc_provider or "none").strip().lower()

    @staticmethod
    def is_configured() -> bool:
        """是否具备签发真实 token 的条件"""
        if RTCService.provider_name() != "agora":
            return False
        return (is_valid_app_key(settings.agora_app_id)
                and is_valid_app_key(settings.agora_app_certificate))

    @staticmethod
    def _reason() -> str:
        provider = RTCService.provider_name()
        if provider == "none":
            return "未启用实时通话（RTC_PROVIDER=none）"
        if provider not in RTCService.SUPPORTED_PROVIDERS:
            return f"不支持的 RTC 渠道：{provider}"
        if not settings.agora_app_id or not settings.agora_app_certificate:
            return "实时通话未配置：缺少 AGORA_APP_ID / AGORA_APP_CERTIFICATE"
        return "AGORA_APP_ID / AGORA_APP_CERTIFICATE 格式不合法（需 32 位十六进制）"

    @staticmethod
    def status() -> dict:
        """渠道状态（前端随时可查，不含任何密钥）"""
        provider = RTCService.provider_name()
        configured = RTCService.is_configured()
        ttl = int(settings.rtc_token_ttl or 3600)
        return {
            "provider": provider,
            "configured": configured,
            "reason": "" if configured else RTCService._reason(),
            "token_ttl": ttl,
            # 能力声明：当前只做实时音频，数字人视频流不在本期范围
            "features": {"audio": configured, "video": False, "data": configured},
        }

    @staticmethod
    def channel_for(user_id: int, session_id: int = 0) -> str:
        """服务端派生频道名：call_u<uid>[_s<会话id>]，只允许本人所在频道"""
        channel = f"call_u{int(user_id)}"
        if session_id:
            channel = f"{channel}_s{int(session_id)}"
        if not _CHANNEL_RE.match(channel):
            # session_id 已在 schema 限制为整数，这里只是兜底
            raise RTCError("频道名不合法", 400)
        return channel

    @staticmethod
    def build_token(user_id: int, session_id: int = 0) -> dict:
        """签发当前用户在当前频道可用的 RTC token"""
        provider = RTCService.provider_name()
        if provider == "none":
            raise RTCError("实时通话未启用，请先配置 RTC_PROVIDER=agora", 503)
        if provider not in RTCService.SUPPORTED_PROVIDERS:
            raise RTCError(f"不支持的 RTC 渠道：{provider}", 500)
        if not RTCService.is_configured():
            raise RTCError(RTCService._reason(), 503)

        uid = int(user_id)
        if uid <= 0 or uid >= 2 ** 32:
            raise RTCError("用户标识不合法，无法签发 token", 400)

        ttl = int(settings.rtc_token_ttl or 3600)
        ttl = max(60, min(ttl, 86400))   # 限制在 1 分钟 ~ 24 小时，避免超长凭证
        channel = RTCService.channel_for(uid, session_id)

        try:
            token = build_rtc_token(
                settings.agora_app_id.strip(),
                settings.agora_app_certificate.strip(),
                channel, uid, expire=ttl,
            )
        except ValueError as e:
            raise RTCError(f"生成通话凭证失败：{e}", 500)

        return {
            "provider": provider,
            "app_id": settings.agora_app_id.strip(),   # App ID 是公开信息，证书不下发
            "channel": channel,
            "uid": uid,
            "token": token,
            "ttl": ttl,
            "expire_at": int(time.time()) + ttl,
        }
