# -*- coding: utf-8 -*-
"""
活动模型 - 每日签到(user_signin)
对应前端 frontend/pages/activity/activity.vue
"""
from sqlalchemy import Column, BigInteger, INTEGER, DATE
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class UserSignin(Base):
    """用户每日签到（一个用户一行）"""
    __tablename__ = "user_signin"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    last_date = Column(DATE, nullable=True, comment="最近一次签到日期")
    streak = Column(INTEGER, nullable=False, default=0, comment="当前连续签到天数")
    max_streak = Column(INTEGER, nullable=False, default=0, comment="历史最长连续天数")
    total_days = Column(INTEGER, nullable=False, default=0, comment="累计签到天数")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "last_date": str(self.last_date) if self.last_date else "",
            "streak": self.streak or 0,
            "max_streak": self.max_streak or 0,
            "total_days": self.total_days or 0,
        }
