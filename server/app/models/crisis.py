# -*- coding: utf-8 -*-
"""
危机干预模型 - 紧急联系人/情绪监测日志/心理资源库/隐私设置
"""
from sqlalchemy import Column, BigInteger, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class CrisisContact(Base):
    """紧急联系人(家人/朋友/心理医生)"""
    __tablename__ = "crisis_contacts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    name = Column(VARCHAR(30), nullable=False, comment="联系人姓名")
    relation = Column(VARCHAR(20), nullable=False, default="family", comment="关系 family/friend/doctor")
    phone = Column(VARCHAR(20), nullable=False, comment="联系电话")
    is_primary = Column(TINYINT, nullable=False, default=0, comment="是否首选联系人 0否 1是")
    notify_enabled = Column(TINYINT, nullable=False, default=1, comment="危机时是否通知 0否 1是")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class EmotionMonitorLog(Base):
    """情绪监测日志"""
    __tablename__ = "emotion_monitor_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    source = Column(VARCHAR(10), nullable=False, default="text", comment="监测来源 text/voice/diary/emotion")
    emotion = Column(VARCHAR(20), nullable=False, default="neutral", comment="识别情绪")
    risk_level = Column(VARCHAR(10), nullable=False, default="normal", comment="风险等级 normal/high/critical")
    score = Column(TINYINT, nullable=False, default=0, comment="风险分数 0-100")
    trigger_text = Column(TEXT, nullable=True, comment="触发文本(脱敏摘要)")
    action_taken = Column(VARCHAR(50), nullable=False, default="", comment="已采取干预 none/alert/modal/contact")
    resolved = Column(TINYINT, nullable=False, default=0, comment="是否已缓解 0否 1是")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class CrisisResource(Base):
    """心理资源库(文章/视频/书籍/测试/热线/咨询)"""
    __tablename__ = "crisis_resources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(VARCHAR(10), nullable=False, comment="资源类型 article/video/book/test/hotline/consult")
    title = Column(VARCHAR(100), nullable=False, comment="标题")
    description = Column(TEXT, nullable=True, comment="简介")
    url = Column(VARCHAR(500), nullable=False, default="", comment="链接/电话")
    cover_url = Column(VARCHAR(500), nullable=False, default="", comment="封面图")
    tags = Column(JSON, nullable=True, comment="标签数组")
    risk_level = Column(VARCHAR(10), nullable=False, default="all", comment="适用风险等级 all/normal/high/critical")
    sort = Column(INTEGER, nullable=False, default=0, comment="排序(越小越前)")
    is_free = Column(TINYINT, nullable=False, default=1, comment="是否免费")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1上架 0下架")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class UserPrivacySetting(Base):
    """用户隐私设置"""
    __tablename__ = "user_privacy_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_privacy_user"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID(唯一)")
    monitor_enabled = Column(TINYINT, nullable=False, default=1, comment="情绪监测开关 0关 1开")
    monitor_sensitivity = Column(VARCHAR(10), nullable=False, default="medium", comment="监测灵敏度 low/medium/high")
    encrypt_diary = Column(TINYINT, nullable=False, default=1, comment="日记内容加密存储 0否 1是")
    encrypt_emotion = Column(TINYINT, nullable=False, default=1, comment="情绪记录加密存储 0否 1是")
    data_retention_days = Column(INTEGER, nullable=False, default=365, comment="数据保留天数(0=永久)")
    allow_analytics = Column(TINYINT, nullable=False, default=1, comment="允许匿名统计分析 0否 1是")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
