# -*- coding: utf-8 -*-
"""互动扭蛋 Schema（模块3）"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GachaQuestion(BaseModel):
    """剧本问答题"""
    question: str
    options: List[str] = []
    hint: str = ""


class GachaTemplateCreate(BaseModel):
    """用户创建扭蛋剧本"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="chat", description="companion/emotion/chat")
    opening_text: str = Field(default="", max_length=500)
    questions: List[GachaQuestion] = []


class GachaDrawRequest(BaseModel):
    """扭蛋抽取请求（可指定分类，不指定则全分类随机）"""
    category: str = Field(default="", description="空=全分类随机")


class GachaAnswerRequest(BaseModel):
    """剧本问答中用户的回答（驱动 AI 回应）"""
    record_id: int
    question_index: int = 0
    answer: str = ""
