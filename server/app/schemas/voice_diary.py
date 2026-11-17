# -*- coding: utf-8 -*-
"""
语音日记 Schema - 请求/响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class VoiceDiaryCreate(BaseModel):
    """创建语音日记"""
    title: str = Field("", max_length=100, description="日记标题")
    content: str = Field("", description="语音转写原文")
    content_edit: Optional[str] = Field(None, description="用户编辑后的文本")
    audio_url: str = Field("", max_length=500, description="音频文件URL")
    audio_duration: int = Field(0, ge=0, le=7200, description="音频时长(秒)")
    audio_size: int = Field(0, ge=0, description="音频大小(字节)")
    sample_rate: int = Field(16000, description="采样率")
    language: str = Field("zh", max_length=10, description="识别语言")
    category: str = Field("daily", max_length=20, description="分类")
    mood: str = Field("neutral", max_length=20, description="记录时情绪")
    remind_time: str = Field("", max_length=5, description="提醒时间 HH:MM")
    record_date: Optional[str] = Field(None, description="日记日期 YYYY-MM-DD(补录)")


class VoiceDiaryUpdate(BaseModel):
    """更新语音日记"""
    title: Optional[str] = Field(None, max_length=100)
    content_edit: Optional[str] = None
    category: Optional[str] = Field(None, max_length=20)
    mood: Optional[str] = Field(None, max_length=20)
    remind_time: Optional[str] = Field(None, max_length=5)
    translation: Optional[str] = None
    translate_lang: Optional[str] = Field(None, max_length=10)


class TranscribeRequest(BaseModel):
    """语音转写请求"""
    file_id: str = Field(..., description="上传后的文件ID")
    language: str = Field("zh", max_length=10, description="识别语言")
    realtime: bool = Field(True, description="是否流式返回")


class TranslateRequest(BaseModel):
    """文本翻译请求"""
    text: str = Field(..., min_length=1, max_length=5000, description="待翻译文本")
    target_lang: str = Field("en", max_length=10, description="目标语言 en/ja/ko/fr/de/zh")


class CategoryCreate(BaseModel):
    """创建分类"""
    name: str = Field(..., min_length=1, max_length=20, description="分类名称")
    icon: str = Field("📖", max_length=10, description="图标emoji")
    color: str = Field("#6B8E7B", max_length=10, description="颜色")


class CategoryUpdate(BaseModel):
    """更新分类"""
    id: int = Field(..., description="分类ID")
    name: Optional[str] = Field(None, min_length=1, max_length=20)
    icon: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, max_length=10)
    sort: Optional[int] = None


class VoiceDiaryStatsQuery(BaseModel):
    """统计查询"""
    period: str = Field("30d", description="统计周期 7d/30d/90d")
