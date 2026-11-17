# -*- coding: utf-8 -*-
"""
习惯打卡Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class HabitCreate(BaseModel):
    """创建习惯"""
    template_id: Optional[int] = 0   # 允许 null/不传 → 视为不使用模板
    name: str = Field(..., max_length=50)
    icon: str = "checkmark"
    description: str = ""
    target: str = ""
    difficulty: str = "medium"
    color: str = "#4CAF50"
    reminder_time: str = ""
    # === 习惯-伙伴融合（可选，不传则走默认） ===
    hope: str = ""            # 期待获得的感受，会写进长效记忆
    role_key: str = ""        # 归属伙伴（角色隔离；空=共享记忆）
    habit_type: str = "other" # study/sport/sleep/read/health/meditation/work/other
    ai_style: str = "gentle"  # gentle/analytical/humorous/calm


class HabitUpdate(BaseModel):
    """更新习惯"""
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    target: Optional[str] = None
    difficulty: Optional[str] = None
    color: Optional[str] = None
    reminder_time: Optional[str] = None
    sort_order: Optional[int] = None


class CheckinRequest(BaseModel):
    """打卡请求"""
    habit_id: int
    note: str = Field(default="", max_length=500)
    difficulty_rating: int = Field(default=0, ge=0, le=3)
    duration_min: int = 0
    # === 习惯-伙伴融合（可选） ===
    emotion: str = ""         # 本次打卡时的情绪 happy/excited/calm/sad/angry/tired/anxious
    role_key: str = ""        # 归属伙伴（角色隔离）
    emotion_id: int = 0       # 已存在的情绪记录ID；为0时按 emotion 字段处理


class CheckinItemOut(BaseModel):
    """打卡明细输出"""
    id: int
    habit_id: int
    completed: int
    note: str = ""
    difficulty_rating: int = 0
    duration_min: int = 0
    created_at: str = ""


class MakeupRequest(BaseModel):
    """补卡请求"""
    habit_id: int
    makeup_date: Optional[str] = None  # "YYYY-MM-DD" 字符串，None 时后端默认昨天
    note: str = Field(default="", max_length=500)
