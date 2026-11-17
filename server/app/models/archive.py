# -*- coding: utf-8 -*-
"""
成长档案模型 - 报告/档案/打卡日记/危机干预
"""
from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATE, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class EmotionReport(Base):
    """情绪分析报告"""
    __tablename__ = "emotion_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    period_type = Column(VARCHAR(10), nullable=False, comment="周期 7d/30d/90d")
    start_date = Column(DATE, nullable=False, comment="开始日期")
    end_date = Column(DATE, nullable=False, comment="结束日期")
    report_data = Column(JSON, nullable=True, comment="报告数据(趋势/分布/关联分析)")
    pdf_url = Column(VARCHAR(500), nullable=False, default="", comment="PDF文件URL")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class GrowthArchive(Base):
    """成长档案(长期追踪)"""
    __tablename__ = "growth_archives"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    period_type = Column(VARCHAR(10), nullable=False, comment="周期 monthly/quarterly/yearly")
    period_start = Column(DATE, nullable=False, comment="周期开始")
    period_end = Column(DATE, nullable=False, comment="周期结束")
    summary = Column(TEXT, nullable=True, comment="AI生成摘要")
    highlights = Column(JSON, nullable=True, comment="成长亮点")
    suggestions = Column(JSON, nullable=True, comment="改进建议")
    emotion_trend = Column(JSON, nullable=True, comment="情绪变化趋势数据")
    archive_data = Column(JSON, nullable=True, comment="完整数据(加密存储)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class CheckinDiary(Base):
    """打卡日记(AI生成)"""
    __tablename__ = "checkin_diaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    checkin_id = Column(BigInteger, nullable=False, comment="打卡记录ID")
    habit_id = Column(BigInteger, nullable=False, comment="习惯ID")
    content = Column(TEXT, nullable=True, comment="日记内容")
    ai_comic_url = Column(VARCHAR(500), nullable=False, default="", comment="AI漫画图URL")
    emotion = Column(VARCHAR(20), nullable=False, default="", comment="打卡时情绪")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class CrisisInterventionLog(Base):
    """危机干预记录"""
    __tablename__ = "crisis_intervention_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    trigger_message = Column(TEXT, nullable=True, comment="触发消息内容")
    emotion_level = Column(VARCHAR(10), nullable=False, default="high", comment="情绪级别 high/critical")
    intervention = Column(TEXT, nullable=True, comment="干预话术")
    resources = Column(JSON, nullable=True, comment="提供的紧急联系方式")
    resolved = Column(TINYINT, nullable=False, default=0, comment="是否已处理 0否 1是")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
