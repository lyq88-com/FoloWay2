# -*- coding: utf-8 -*-
"""
成就模型 - 徽章/用户徽章
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATE, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class Badge(Base):
    """徽章定义"""
    __tablename__ = "badges"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(VARCHAR(30), nullable=False, unique=True, comment="徽章代码")
    name = Column(VARCHAR(50), nullable=False, comment="徽章名称")
    description = Column(VARCHAR(255), nullable=False, default="", comment="描述")
    icon = Column(VARCHAR(20), nullable=False, default="", comment="图标emoji")
    condition_type = Column(VARCHAR(30), nullable=False, comment="条件类型 streak_days/all_done/checkin_count")
    condition_value = Column(INTEGER, nullable=False, default=1, comment="条件值")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class UserBadge(Base):
    """用户徽章记录"""
    __tablename__ = "user_badges"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    badge_id = Column(BigInteger, nullable=False, comment="徽章ID")
    earned_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="获得时间")
