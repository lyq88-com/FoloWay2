# -*- coding: utf-8 -*-
"""
情绪记录Schema
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class EmotionRecordCreate(BaseModel):
    """创建情绪记录"""
    habit_id: int = 0
    emotion: str = Field(..., description="happy/excited/calm/sad/angry/tired")
    intensity: int = Field(default=5, ge=0, le=10)
    tags: List[str] = Field(default=[], description="触发标签")
    description: str = Field(default="", max_length=200)
    record_date: Optional[str] = Field(default=None, description="补录日期 YYYY-MM-DD")


class EmotionRecordOut(BaseModel):
    """情绪记录输出"""
    id: int
    user_id: int
    habit_id: int = 0
    emotion: str
    intensity: int
    tags: List[str] = []
    description: str = ""
    record_date: str
    created_at: str = ""


class EmotionTrendQuery(BaseModel):
    """情绪趋势查询"""
    period: str = "7d"
