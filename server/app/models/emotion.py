# -*- coding: utf-8 -*-
"""
情绪记录模型 - 与习惯打卡融合的情绪数据
"""
from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATE, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class EmotionRecord(Base):
    """情绪打卡记录(与习惯打卡融合)"""
    __tablename__ = "emotion_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯ID(0=独立情绪记录)")
    emotion = Column(VARCHAR(20), nullable=False, comment="情绪 happy/excited/calm/sad/angry/tired")
    intensity = Column(TINYINT, nullable=False, default=5, comment="情绪强度 0-10")
    tags = Column(JSON, nullable=True, comment='触发标签 ["work","study","life","family","entertainment"]')
    description = Column(VARCHAR(200), nullable=False, default="", comment="情绪描述(200字内)")
    record_date = Column(DATE, nullable=False, comment="记录日期(支持补录)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
