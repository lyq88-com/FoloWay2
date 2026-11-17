# -*- coding: utf-8 -*-
"""
正念练习模型 - 练习记录/计划/音频资源
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATE, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class MindfulnessSession(Base):
    """正念练习记录"""
    __tablename__ = "mindfulness_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    session_type = Column(VARCHAR(30), nullable=False, comment="练习类型 breath/body_scan/meditation/anxiety")
    duration_min = Column(INTEGER, nullable=False, default=10, comment="练习时长(分钟)")
    audio_id = Column(BigInteger, nullable=False, default=0, comment="使用的音频ID")
    emotion_before = Column(VARCHAR(20), nullable=False, default="", comment="练习前情绪")
    emotion_after = Column(VARCHAR(20), nullable=False, default="", comment="练习后情绪")
    intensity_before = Column(TINYINT, nullable=False, default=0, comment="练习前强度 0-10")
    intensity_after = Column(TINYINT, nullable=False, default=0, comment="练习后强度 0-10")
    completed = Column(TINYINT, nullable=False, default=1, comment="是否完成 1是 0否")
    session_date = Column(DATETIME, nullable=False, comment="练习时间")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class MindfulnessPlan(Base):
    """正念练习计划"""
    __tablename__ = "mindfulness_plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    plan_type = Column(VARCHAR(30), nullable=False, comment="计划类型 daily/weekly")
    session_type = Column(VARCHAR(30), nullable=False, comment="练习类型 breath/body_scan/meditation/anxiety")
    reminder_time = Column(VARCHAR(10), nullable=False, default="08:00", comment="提醒时间 HH:MM")
    week_days = Column(VARCHAR(20), nullable=False, default="", comment="周几(逗号分隔 1-7, 仅weekly)")
    active = Column(TINYINT, nullable=False, default=1, comment="是否启用 1是 0否")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class AudioResource(Base):
    """音频资源库"""
    __tablename__ = "audio_resources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(100), nullable=False, comment="音频标题")
    audio_type = Column(VARCHAR(30), nullable=False, comment="类型 breath/body_scan/meditation/anxiety")
    duration_min = Column(INTEGER, nullable=False, default=10, comment="时长(分钟)")
    audio_url = Column(VARCHAR(500), nullable=False, comment="音频文件URL")
    cover_url = Column(VARCHAR(500), nullable=False, default="", comment="封面图URL")
    description = Column(TEXT, nullable=True, comment="音频描述")
    narrator = Column(VARCHAR(50), nullable=False, default="", comment="旁白人")
    sort_order = Column(INTEGER, nullable=False, default=0, comment="排序值")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
