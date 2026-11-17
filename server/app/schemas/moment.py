# -*- coding: utf-8 -*-
"""
朋友圈 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class MomentCreateRequest(BaseModel):
    """发布朋友圈动态(图片URL已先行上传获取)"""
    content: str = Field(default="", description="文字内容")
    images: List[str] = Field(default=[], description="图片URL数组")
    location: str = Field(default="", description="位置")


class MomentCommentCreate(BaseModel):
    """评论"""
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")
    reply_to_id: int = Field(default=0, description="回复的评论ID")
