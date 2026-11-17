# -*- coding: utf-8 -*-
"""日程提醒 Schema（模块2）"""
from typing import Optional
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """创建日程"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    schedule_date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = "08:00"
    end_time: str = "09:00"
    habit_id: int = 0
    remind_minutes: int = Field(default=5, ge=0, le=120)


class ScheduleUpdate(BaseModel):
    """更新日程（全部字段可选）"""
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    habit_id: Optional[int] = None
    is_done: Optional[int] = None
    remind_minutes: Optional[int] = None


class ScheduleAiGenerate(BaseModel):
    """AI 伙伴生成日程请求"""
    for_date: str = Field(..., description="生成哪一天的日程 YYYY-MM-DD")
