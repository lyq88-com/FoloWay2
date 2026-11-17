# -*- coding: utf-8 -*-
"""
正念练习Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class MindfulnessSessionCreate(BaseModel):
    """创建正念练习记录"""
    session_type: str = Field(..., description="breath/body_scan/meditation/anxiety")
    duration_min: int = 10
    audio_id: int = 0
    emotion_before: str = ""
    emotion_after: str = ""
    intensity_before: int = Field(default=0, ge=0, le=10)
    intensity_after: int = Field(default=0, ge=0, le=10)
    completed: int = 1
    # ↓↓↓ 模块2 新增：前端呼吸检测采集结果（可选，不传则原有逻辑不变） ↓↓↓
    breath_rate: Optional[float] = Field(default=None, description="平均呼吸频率 次/分钟")
    breath_anomalies: Optional[str] = Field(default=None, description="异常类型 JSON 字符串")
    # ↑↑↑ 模块2 新增结束 ↑↑↑


class MindfulnessPlanCreate(BaseModel):
    """创建正念练习计划"""
    plan_type: str = "daily"
    session_type: str = "meditation"
    reminder_time: str = "08:00"
    week_days: str = ""


class AudioResourceOut(BaseModel):
    """音频资源输出"""
    id: int
    title: str
    audio_type: str
    duration_min: int
    audio_url: str
    cover_url: str = ""
    description: str = ""
    narrator: str = ""
