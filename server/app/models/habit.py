# -*- coding: utf-8 -*-
"""
习惯任务模型 - 模板/习惯/打卡/难度日志
"""
from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DECIMAL, DATE, DATETIME, TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TaskTemplate(Base):
    """预设习惯模板"""
    __tablename__ = "task_templates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(VARCHAR(20), nullable=False, comment="习惯类型 morning/sport/read等")
    name = Column(VARCHAR(50), nullable=False, comment="习惯名称")
    icon = Column(VARCHAR(20), nullable=False, default="", comment="图标emoji")
    description = Column(VARCHAR(255), nullable=False, default="", comment="描述")
    default_target = Column(VARCHAR(100), nullable=False, default="", comment="默认目标描述")
    breakdown = Column(JSON, nullable=True, comment="任务拆解步骤数组")
    difficulty_targets = Column(JSON, nullable=True, comment='各难度目标 {"easy":"","medium":"","hard":""}')
    sort_order = Column(INTEGER, nullable=False, default=0, comment="排序值")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class Habit(Base):
    """用户选择的习惯"""
    __tablename__ = "habits"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    template_id = Column(BigInteger, nullable=False, default=0, comment="模板ID(0=自定义)")
    name = Column(VARCHAR(50), nullable=False, comment="习惯名称")
    icon = Column(VARCHAR(20), nullable=False, default="checkmark", comment="图标")
    description = Column(VARCHAR(255), nullable=False, default="", comment="描述")
    target = Column(VARCHAR(100), nullable=False, default="", comment="目标描述")
    difficulty = Column(VARCHAR(20), nullable=False, default="medium", comment="难度 easy/medium/hard")
    color = Column(VARCHAR(20), nullable=False, default="#4CAF50", comment="主题色")
    xp_value = Column(INTEGER, nullable=False, default=20, comment="经验值")
    reminder_time = Column(VARCHAR(10), nullable=False, default="", comment="提醒时间 HH:MM")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    sort_order = Column(INTEGER, nullable=False, default=0, comment="排序")
    # === 阶段J扩展字段 (习惯-AI全链路融合) ===
    emotion_status = Column(VARCHAR(20), nullable=False, default="neutral", comment="最近情绪状态 happy/excited/calm/sad/angry/tired/neutral")
    continuous_day = Column(INTEGER, nullable=False, default=0, comment="连续打卡天数")
    custom_remind_text = Column(VARCHAR(255), nullable=False, default="", comment="用户自定义AI提醒话术(空=使用角色默认)")
    habit_type = Column(VARCHAR(20), nullable=False, default="other", comment="习惯分类标签 study/sport/sleep/read/health/meditation/work/other")
    ai_style = Column(VARCHAR(20), nullable=False, default="gentle", comment="该习惯绑定的AI对话风格 gentle/analytical/humorous/calm")
    # === 习惯生命周期（伙伴视角：暂停/重启，数据保留不删除） ===
    is_paused = Column(TINYINT, nullable=False, default=0, comment="是否暂停 0进行中 1已暂停(不触发打卡校验/不推送提醒/数据保留)")
    paused_at = Column(DATETIME, nullable=True, comment="最近一次暂停时间")
    paused_reason = Column(VARCHAR(100), nullable=False, default="", comment="暂停时的状态备注 如 太累了/先放一放")
    resume_count = Column(INTEGER, nullable=False, default=0, comment="重启次数(暂停后重新开启累计)")
    last_resume_at = Column(DATETIME, nullable=True, comment="最近一次重启时间")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class Checkin(Base):
    """每日打卡主表"""
    __tablename__ = "checkins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    checkin_date = Column(DATE, nullable=False, comment="打卡日期")
    total_habits = Column(INTEGER, nullable=False, default=0, comment="当日习惯总数")
    completed_count = Column(INTEGER, nullable=False, default=0, comment="完成数")
    completion_rate = Column(DECIMAL(5, 2), nullable=False, default=0, comment="完成率(%)")
    streak_days = Column(INTEGER, nullable=False, default=0, comment="连续天数")
    note = Column(TEXT, nullable=True, comment="今日总评")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1正常 0已删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class CheckinItem(Base):
    """打卡明细"""
    __tablename__ = "checkin_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    checkin_id = Column(BigInteger, nullable=False, comment="打卡主表ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, comment="习惯ID")
    completed = Column(TINYINT, nullable=False, default=0, comment="是否完成 0否 1是")
    note = Column(VARCHAR(500), nullable=True, comment="打卡留言")
    image_url = Column(VARCHAR(500), nullable=False, default="", comment="打卡图片")
    difficulty_rating = Column(TINYINT, nullable=False, default=0, comment="难度感受 0未评 1简单 2适中 3困难")
    duration_min = Column(INTEGER, nullable=False, default=0, comment="耗时(分钟)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())

    # 关联打卡主表：stats.py 统计连续天数时需用 item.checkin.checkin_date
    checkin = relationship(
        "Checkin",
        primaryjoin="CheckinItem.checkin_id == Checkin.id",
        foreign_keys="[CheckinItem.checkin_id]",
        viewonly=True,
    )


class DifficultyLog(Base):
    """难度变化日志"""
    __tablename__ = "difficulty_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, comment="习惯ID")
    habit_name = Column(VARCHAR(50), nullable=False, default="", comment="习惯名称")
    old_difficulty = Column(VARCHAR(10), nullable=False, default="", comment="原难度")
    new_difficulty = Column(VARCHAR(10), nullable=False, default="", comment="新难度")
    change_type = Column(VARCHAR(10), nullable=False, default="keep", comment="变化类型 up/down/keep")
    old_target = Column(VARCHAR(100), nullable=False, default="", comment="原目标")
    new_target = Column(VARCHAR(100), nullable=False, default="", comment="新目标")
    recent_rate = Column(INTEGER, nullable=False, default=0, comment="触发时7天完成率(%)")
    change_date = Column(DATE, nullable=False, comment="变更日期")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
