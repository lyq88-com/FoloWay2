# -*- coding: utf-8 -*-
"""
日程提醒模型（模块2）
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATE, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class Schedule(Base):
    """用户日程"""
    __tablename__ = "schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="所属用户ID")
    title = Column(VARCHAR(100), nullable=False, comment="日程标题")
    description = Column(VARCHAR(500), nullable=False, default="", comment="备注")
    schedule_date = Column(DATE, nullable=False, comment="日程日期")
    start_time = Column(VARCHAR(5), nullable=False, default="08:00", comment="开始时间 HH:MM")
    end_time = Column(VARCHAR(5), nullable=False, default="09:00", comment="结束时间 HH:MM")
    habit_id = Column(BigInteger, nullable=False, default=0, comment="绑定习惯ID")
    is_done = Column(TINYINT, nullable=False, default=0, comment="是否完成 0否 1是")
    source = Column(VARCHAR(10), nullable=False, default="manual", comment="manual / ai")
    remind_minutes = Column(INTEGER, nullable=False, default=5, comment="提前提醒分钟")
    reminded = Column(TINYINT, nullable=False, default=0, comment="是否已推送提醒")
    status = Column(TINYINT, nullable=False, default=1, comment="1正常 0删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
