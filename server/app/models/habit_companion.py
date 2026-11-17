# -*- coding: utf-8 -*-
"""
习惯-伙伴融合 模型

只新增「用户伙伴偏好设置」一张表；习惯生命周期相关的事件记忆
一律复用已有的 ai_user_memories（不新建事件表），
暂停状态则落在 habits.is_paused 上。
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class UserCompanionSetting(Base):
    """
    用户与伙伴相处的偏好设置（持久化开关）

    allow_habit_topic: 【允许伙伴和我聊习惯相关的事】总开关
        0 = 关闭：拦截全部习惯类主动消息，自由聊天里也不主动提起习惯
        1 = 开启（默认）
    habit_proactive_muted_until: 负面情绪较多时自动降频的截止时刻（到点自动恢复）
    """
    __tablename__ = "user_companion_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True, comment="用户ID")
    allow_habit_topic = Column(TINYINT, nullable=False, default=1, comment="允许伙伴聊习惯相关的事 1是 0否")
    habit_proactive_muted_until = Column(DATETIME, nullable=True, comment="习惯类主动消息降频截止时刻(负面情绪多时自动设置)")
    habit_topic_off_at = Column(DATETIME, nullable=True, comment="最近一次关闭习惯话题的时间")
    # ↓↓↓ 新增（2026-10-28 习惯-伙伴融合·打卡上下文延续） ↓↓↓
    # 用户明确表示「不想聊这条习惯」后，把该习惯静默 N 天（默认 3 天）：
    # 期间不进会话上下文、不主动提起。格式 {"<habit_id>": "YYYY-MM-DD HH:MM:SS"}
    muted_habits_json = Column(TEXT, nullable=True, comment="按习惯的短期静默表 {habit_id: 截止时刻}")
    # ↑↑↑ 新增结束 ↑↑↑
    note = Column(TEXT, nullable=True, comment="备注")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
