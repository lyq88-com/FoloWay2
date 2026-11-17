# -*- coding: utf-8 -*-
"""
语音日记模型 - 日记/分类
"""
from sqlalchemy import Column, BigInteger, ForeignKey
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATE, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class VoiceDiary(Base):
    """语音日记"""
    __tablename__ = "voice_diaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(VARCHAR(100), nullable=False, default="", comment="日记标题")
    content = Column(TEXT, nullable=True, comment="语音转写原文")
    content_edit = Column(TEXT, nullable=True, comment="用户编辑后的文本")
    audio_url = Column(VARCHAR(500), nullable=False, default="", comment="音频文件URL")
    audio_duration = Column(INTEGER, nullable=False, default=0, comment="音频时长(秒)")
    audio_size = Column(INTEGER, nullable=False, default=0, comment="音频大小(字节)")
    sample_rate = Column(INTEGER, nullable=False, default=16000, comment="采样率")
    language = Column(VARCHAR(10), nullable=False, default="zh", comment="识别语言 zh/en/ja...")
    translation = Column(TEXT, nullable=True, comment="译文(多语言翻译结果)")
    translate_lang = Column(VARCHAR(10), nullable=False, default="", comment="翻译目标语言")
    category = Column(VARCHAR(20), nullable=False, default="daily", comment="分类 daily/work/study/travel/mood/other")
    mood = Column(VARCHAR(20), nullable=False, default="neutral", comment="记录时情绪")
    sentiment_score = Column(TINYINT, nullable=False, default=0, comment="情感分数 -5~5")
    sentiment_label = Column(VARCHAR(10), nullable=False, default="neutral", comment="情感标签 positive/negative/neutral")
    is_encrypted = Column(TINYINT, nullable=False, default=0, comment="内容是否加密存储 0否 1是")
    remind_time = Column(VARCHAR(5), nullable=False, default="", comment="日记提醒时间 HH:MM(空=无提醒)")
    record_date = Column(DATE, nullable=False, comment="日记日期")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class VoiceDiaryCategory(Base):
    """语音日记自定义分类"""
    __tablename__ = "voice_diary_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    name = Column(VARCHAR(20), nullable=False, comment="分类名称")
    icon = Column(VARCHAR(10), nullable=False, default="📖", comment="分类图标(emoji)")
    color = Column(VARCHAR(10), nullable=False, default="#6B8E7B", comment="分类颜色")
    sort = Column(INTEGER, nullable=False, default=0, comment="排序值(越小越前)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
