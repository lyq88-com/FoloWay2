# -*- coding: utf-8 -*-
"""「专注」模块请求体 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List


class FocusPlanRequest(BaseModel):
    """备考计划生成入参"""
    exam_type: str = Field("", description="考试类型，如 考研/教资/CFA")
    exam_date: str = Field("", description="考试日期 YYYY-MM-DD")
    weakness: str = Field("", description="当前薄弱点")
    daily_minutes: int = Field(45, description="每日可用时长(分钟)")
    remind_time: str = Field("", description="每日提醒时间 HH:MM，空=不提醒")


class FocusTaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    tag: str = "学习"
    est_minutes: int = 25
    start_date: str = ""
    due_date: str = ""
    remind_time: str = ""


class FocusTaskStatusRequest(BaseModel):
    status: int = Field(..., description="0待办 1进行中 2已完成")


class FocusSplitRequest(BaseModel):
    prompt: str = Field(..., description="大任务描述（可来自语音转写）")
    mode: str = Field("simple", description="simple简单 / flow心流")


class FocusStepFinishRequest(BaseModel):
    step_id: int
    role_id: str = "companion"


class FocusSessionStartRequest(BaseModel):
    task_id: int = 0
    role_id: str = "companion"
    mode: str = "simple"
    tag: str = "学习"


class FocusSessionInterruptRequest(BaseModel):
    session_id: int
    count: int = 1


class FocusSessionFinishRequest(BaseModel):
    session_id: int
    duration: int
    interrupted: bool = False


class FocusRemindRequest(BaseModel):
    task_id: int = 0
    remind_at: str = Field(..., description="YYYY-MM-DD HH:MM")
    text: str = ""


class FocusGuideSaveRequest(BaseModel):
    record_id: int
    current_index: int = 1
    duration_seconds: int = 0
    finished_content: str = ""


class FocusDynamicRequest(BaseModel):
    content: str = ""
    image: str = ""
    visible_type: str = Field("self", description="self仅自己 / follow互关好友")


class FocusChatRequest(BaseModel):
    text: str
    history: Optional[List[dict]] = None
