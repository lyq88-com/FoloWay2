# -*- coding: utf-8 -*-
"""世界世界观 + AI笔记 Schema（模块1 + 模块4）"""
from typing import List, Optional
from pydantic import BaseModel, Field


class WorldCreate(BaseModel):
    """创建虚拟世界"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    rules: str = ""
    is_public: int = Field(default=1, description="1公开 0私人")
    role_ids: List[int] = Field(default=[], description="加入世界的AI角色ID列表")
    custom_roles: List[str] = Field(default=[], description="自设角色名列表")
    checkin_target: int = Field(default=3, ge=1, le=30)


class WorldUpdate(BaseModel):
    """更新世界信息"""
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[str] = None
    is_public: Optional[int] = None
    checkin_target: Optional[int] = None


class JoinWorldRequest(BaseModel):
    """加入公开世界"""
    world_id: int


class AddRoleRequest(BaseModel):
    """向已有世界追加 AI 角色 / 自设角色"""
    role_id: int = Field(default=0, description="ai_roles.id（自设角色传0）")
    custom_name: str = Field(default="", description="自设角色名（role_id=0时使用）")


class NoteCreate(BaseModel):
    """发布世界笔记（用户打卡笔记/普通笔记）"""
    content: str = Field(..., min_length=1, max_length=1000)
    note_type: str = Field(default="normal", description="normal/checkin")


class CommentCreate(BaseModel):
    """笔记评论"""
    content: str = Field(..., min_length=1, max_length=500)
    reply_to_id: int = 0
