# -*- coding: utf-8 -*-
"""
AI对话Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ↓↓↓ 新增 ↓↓↓ 一次性非流式对话（业务触发式 AI：打卡/情绪/正念/地图节点）
# 前端 common/ai-cloud-service.js 已把「人设 system prompt + 用户数据 + 触发事件」拼好，
# 后端不做二次拼装，只做合法性校验与长度裁剪，然后透传给大模型。
class ChatQuickMessage(BaseModel):
    role: str = Field("user", max_length=20)
    content: str = Field("", max_length=8000)


class ChatQuickRequest(BaseModel):
    messages: List[ChatQuickMessage] = Field(default_factory=list)
# ↑↑↑ 新增结束 ↑↑↑


class ChatSendRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., max_length=2000)
    session_id: Optional[int] = None
    role_type: str = "cute"
    dialogue_style: str = "gentle"
    # 陪伴模式场景字段(前端 companion.js 携带; 普通对话不传则为空)
    scene_type: str = Field("", max_length=20, description="陪伴场景 sleep/study/work/sport/eat/custom/group_chat")
    scene_name: str = Field("", max_length=50, description="场景名称")
    # 语音多语言：BCP-47 语种码（zh-CN / en-US / ja-JP / ko-KR / fr-FR）
    # 空字符串 = 默认中文（保持原有行为，前端不传时零影响）
    language: str = Field("", max_length=10, description="回复语种 BCP-47")
    # ↓↓↓ 陪伴感增强 v3.1：真实角色标识（ai_roles.role_type，如 custom_12_ab12cd） ↓↓↓
    # 为什么单独加一个字段：role_type 在历史语义里是「对话风格 token」（relaxed/y2k/gentle…），
    # 前端一直用它传风格，导致后端 get_role_by_key(role_type) 永远查不到角色 → 人设从未注入。
    # 新增 role_key 专门承载角色标识；为空时回退到 role_type，老调用方行为完全不变。
    role_key: str = Field("", max_length=64, description="角色标识 ai_roles.role_type")
    # ↓↓↓ 新增（2026-10-28 打卡上下文延续） ↓↓↓
    # 本次对话要挂载的习惯上下文。
    #  - 传 ID ：进入/保持「习惯会话模式」，AI 全程带着这条习惯的完整历程
    #  - 不传  ：沿用该会话已挂载的 chat_sessions.habit_id（持久化，需求5）
    #  - 传 -1 ：显式退出习惯专题（等价于说出「先不说这个了」）
    habit_id: Optional[int] = Field(None, description="挂载的习惯上下文ID；-1=退出习惯专题")
    # ↓↓↓ 群聊场景 ↓↓↓
    # 前端拼好的群成员列表 + 最近发言，注入 system prompt 让 AI 知道群里有谁、刚才聊了什么。
    # 空串=不注入（老调用方行为完全不变）
    group_context: str = Field("", max_length=2000, description="群聊上下文：群成员列表+最近发言")


class ChatMessageOut(BaseModel):
    """消息输出"""
    id: int = 0
    session_id: int = 0
    role: str = "user"
    content: str = ""
    emotion: str = "neutral"
    ai_status: str = "chat"
    comfort_text: str = ""
    created_at: str = ""


class ChatHistoryQuery(BaseModel):
    """对话历史查询"""
    session_id: int = 0
    page: int = 1
    page_size: int = 30
