# -*- coding: utf-8 -*-
"""
危机干预 Schema - 请求/响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class MonitorCheckRequest(BaseModel):
    """实时情绪监测请求"""
    text: Optional[str] = Field(None, max_length=2000, description="待监测文本")
    voice_sentiment: Optional[str] = Field(None, description="语音情绪特征 positive/negative/neutral")
    voice_volume: Optional[float] = Field(None, ge=0, le=1, description="语音平均音量0-1")
    voice_speed: Optional[float] = Field(None, ge=0, le=3, description="语速(字/秒倍率)")
    source: str = Field("text", description="来源 text/voice/diary/emotion")


class CrisisContactCreate(BaseModel):
    """创建紧急联系人"""
    name: str = Field(..., min_length=1, max_length=30)
    relation: str = Field("family", description="关系 family/friend/doctor")
    phone: str = Field(..., min_length=5, max_length=20)
    is_primary: bool = False
    notify_enabled: bool = True


class CrisisContactUpdate(BaseModel):
    """更新紧急联系人"""
    id: int
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    relation: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=5, max_length=20)
    is_primary: Optional[bool] = None
    notify_enabled: Optional[bool] = None


class PrivacySettingUpdate(BaseModel):
    """更新隐私设置"""
    monitor_enabled: Optional[bool] = None
    monitor_sensitivity: Optional[str] = Field(None, description="low/medium/high")
    encrypt_diary: Optional[bool] = None
    encrypt_emotion: Optional[bool] = None
    data_retention_days: Optional[int] = Field(None, ge=0, le=3650)
    allow_analytics: Optional[bool] = None


class DataDeleteRequest(BaseModel):
    """数据删除请求"""
    types: List[str] = Field(..., description="要删除的数据类型 diary/emotion/monitor/chat/all")
