# -*- coding: utf-8 -*-
"""
习惯-AI 联动 Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class CheckinTriggerRequest(BaseModel):
    """打卡触发AI对话请求"""
    habit_id: int = Field(..., description="习惯ID")
    note: str = Field("", max_length=500, description="打卡留言")
    emotion: str = Field("", description="当前情绪 happy/excited/calm/sad/angry/tired/neutral")
    character_id: str = Field("linxi", description="AI角色ID")


class CustomRemindRequest(BaseModel):
    """自定义提醒话术请求"""
    habit_id: int = Field(..., description="习惯ID")
    custom_remind_text: str = Field("", max_length=255, description="自定义AI提醒话术")
    ai_style: str = Field("gentle", description="AI对话风格 gentle/analytical/humorous/calm")


class DiaryGenerateRequest(BaseModel):
    """日记生成请求"""
    habit_id: int = Field(..., description="习惯ID")
    note: str = Field("", max_length=500)
    emotion: str = Field("")
    date: Optional[str] = Field(None, description="指定日期 YYYY-MM-DD(默认今天)")


class MemoryWriteRequest(BaseModel):
    """记忆写入请求"""
    memory_type: str = Field(..., description="记忆类型 checkin/emotion/chat/achievement/crisis/plan")
    memory_content: str = Field(..., max_length=1000)
    habit_id: int = Field(0)
    emotion_id: int = Field(0)
    emotion_score: int = Field(5, ge=0, le=10)
    habit_status: str = Field("")
    is_long_term: bool = Field(False)
