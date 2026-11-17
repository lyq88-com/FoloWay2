# -*- coding: utf-8 -*-
"""纯本地玩法上云 - 请求体 Schema"""
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PlayStateItem(BaseModel):
    """单个玩法的状态（payload 结构由前端定义）"""
    key: str = Field(..., description="box/fragment/postcard")
    payload: Any = Field(default=None)
    version: int = Field(0, ge=0, description="客户端持有的版本号，0=首次上传")


class PlayStateBatchIn(BaseModel):
    """批量读写（最多 3 个玩法）"""
    items: List[PlayStateItem] = Field(default_factory=list)


class CapsuleCreateIn(BaseModel):
    title: str = Field("", max_length=40)
    content: str = Field(..., max_length=2000)
    openAt: Optional[str] = Field(None, description="YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，空=不设期限")


class ShopOrderIn(BaseModel):
    goodsId: str = Field(..., max_length=64)
    qty: int = Field(1, ge=1, le=10)
