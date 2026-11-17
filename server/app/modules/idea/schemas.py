# -*- coding: utf-8 -*-
"""「小想法」请求体 Schema（仅入参校验，出参统一走 ResponseBase）"""
from typing import Optional
from pydantic import BaseModel, Field


class IdeaPublishRequest(BaseModel):
    content: str = Field(default="", description="想法文字，前端限 200 字")
    image: str = Field(default="", description="已上传得到的图片 URL / 相对路径，可空")
    is_anonymous: bool = Field(default=False, description="是否匿名发布")


class IdeaLightRequest(BaseModel):
    """点亮：传共鸣记录 id（前端卡片维度操作）"""
    resonance_id: int = Field(..., description="共鸣记录 idea_resonance.id")


class IdeaQuickReactRequest(BaseModel):
    idea_id: int = Field(..., description="被互动的想法ID")
    action_type: str = Field(..., description="good/agree/highfive/pat")


class IdeaSettingRequest(BaseModel):
    accept_resonance: bool = Field(..., description="是否接受共鸣匹配")


class IdeaMessageRequest(BaseModel):
    content: str = Field(..., description="私聊消息内容")
    msg_type: str = Field(default="text", description="text/react")


class IdeaReadRequest(BaseModel):
    notification_id: Optional[int] = Field(default=0, description="单条已读；0=全部已读")
