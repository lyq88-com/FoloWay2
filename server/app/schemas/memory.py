# -*- coding: utf-8 -*-
"""记忆相关 Schema（陪伴感增强 v3）"""
from typing import Optional

from pydantic import BaseModel, Field


class MemoryAddRequest(BaseModel):
    """手动添加一条记忆"""
    content: str = Field(..., min_length=1, max_length=500, description="记忆内容")
    layer: str = Field(default="event", description="profile/event/preference")
    title: str = Field(default="", max_length=64, description="短标签")
    salience: int = Field(default=7, ge=1, le=10, description="重要度")
    role_key: str = Field(default="", max_length=64, description="归属角色，空=共享")


class MemoryUpdateRequest(BaseModel):
    """编辑一条记忆"""
    content: Optional[str] = Field(default=None, max_length=500)
    title: Optional[str] = Field(default=None, max_length=64)
    layer: Optional[str] = Field(default=None)
    salience: Optional[int] = Field(default=None, ge=1, le=10)


class MemoryExtractRequest(BaseModel):
    """从一段文本里抽取记忆"""
    text: str = Field(..., min_length=1, max_length=2000)
    role_key: str = Field(default="", max_length=64)
