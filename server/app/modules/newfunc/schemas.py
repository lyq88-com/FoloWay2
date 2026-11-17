# -*- coding: utf-8 -*-
"""newfunc 模块请求模型（pydantic）"""
from typing import List, Optional

from pydantic import BaseModel


class PushSettingUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    checkin_push_enabled: Optional[bool] = None
    checkin_push_time: Optional[str] = None
    todo_push_enabled: Optional[bool] = None
    ai_push_enabled: Optional[bool] = None
    ai_frequency: Optional[str] = None
    quiet_enabled: Optional[bool] = None
    quiet_start: Optional[str] = None
    quiet_end: Optional[str] = None
    # 【模块4·群推送】群聊消息提醒开关
    group_push_enabled: Optional[bool] = None


class BindCidRequest(BaseModel):
    client_id: str = ""


class DiarySaveRequest(BaseModel):
    date: str
    mood_tags: Optional[List[str]] = None
    mood_score: Optional[int] = None
    diary_text: Optional[str] = None


class DiarySummaryRequest(BaseModel):
    date: str
    summary: str


class DiaryDateRequest(BaseModel):
    date: str


class AuthorizeRequest(BaseModel):
    enabled: bool


class BotCreateRequest(BaseModel):
    name: str
    avatar: str = "🌿"
    personality: str = ""
    speak_style: str = ""
    self_intro: str = ""
    taboo: str = ""
    allow_push: bool = True


class BotUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    personality: Optional[str] = None
    speak_style: Optional[str] = None
    self_intro: Optional[str] = None
    taboo: Optional[str] = None
    allow_push: Optional[bool] = None


class BotChatRequest(BaseModel):
    text: str
    history: List[dict] = []


class BotProactiveRequest(BaseModel):
    save_record: bool = True


class BotMemoryCreateRequest(BaseModel):
    content: str
    mem_type: str = "fact"          # fact / preference / emotion / dialogue
    importance: int = 5             # 1-10，手动写入默认中等重要度
