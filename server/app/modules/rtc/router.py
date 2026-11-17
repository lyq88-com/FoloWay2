# -*- coding: utf-8 -*-
"""
实时通话（RTC）接口（/api/v1/rtc/*）
====================================
  GET  /rtc/status   渠道状态（是否已配置、支持的能力、token 有效期）
  POST /rtc/token    签发当前用户在当前频道的通话 token（短 TTL + 限流）

未配置声网密钥时两个接口都返回明确的 503 业务错误，前端据此进入「演示模式」，
不会出现「假装已接通实时通话」的假成功。
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.modules.rtc.service import RTCService, RTCError
from app.schemas.common import ResponseBase
# 复用「小想法」模块的进程内限流器（独立 import，不改其代码）
from app.modules.idea.content_safety import limiter

router = APIRouter(prefix="/rtc", tags=["实时通话"])


class RTCTokenIn(BaseModel):
    """客户端只需给出本次通话的会话号；频道名与 uid 一律由服务端派生"""

    session_id: int = Field(0, ge=0, le=999999999)


@router.get("/status")
def rtc_status(user_id: int = Depends(get_current_user)):
    """实时通话渠道状态（不含任何密钥）"""
    return ResponseBase.success(RTCService.status())


@router.post("/token")
def rtc_token(req: Optional[RTCTokenIn] = None, user_id: int = Depends(get_current_user)):
    """签发通话 token：uid/频道强制绑定当前登录用户，防止串台偷听"""
    if not limiter.allow(f"rtc_token:{user_id}", 20, 300):
        return ResponseBase.error("请求过于频繁，请稍后再试", 429)
    session_id = req.session_id if req else 0
    try:
        data = RTCService.build_token(user_id, session_id)
    except RTCError as e:
        return ResponseBase.error(e.message, e.code)
    return ResponseBase.success(data)
