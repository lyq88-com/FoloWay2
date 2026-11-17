# -*- coding: utf-8 -*-
"""
陪伴感增强 v3 扩展模型
- GachaCharacterPool: 扭蛋角色池（抽出即完整人设 + 独立记忆空间）
- AIProactiveLog: AI 主动互动记录（主动关心 / 约定提醒 / 主动分享）
"""
from sqlalchemy import Column, BigInteger, Integer
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class GachaCharacterPool(Base):
    """扭蛋角色池 - 每个角色自带完整独立人设"""
    __tablename__ = "gacha_character_pool"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(50), nullable=False, comment="角色名")
    avatar = Column(VARCHAR(32), nullable=False, default="", comment="头像emoji")
    rarity = Column(VARCHAR(16), nullable=False, default="R", comment="稀有度 N/R/SR/SSR")
    personality = Column(VARCHAR(255), nullable=False, default="", comment="一句话人设")
    backstory = Column(TEXT, nullable=True, comment="完整背景故事")
    personality_type = Column(VARCHAR(32), nullable=False, default="", comment="人格类型标签")
    traits = Column(VARCHAR(255), nullable=False, default="", comment="性格标签(顿号分隔)")
    speech_style = Column(VARCHAR(255), nullable=False, default="", comment="说话风格")
    quirks = Column(TEXT, nullable=True, comment="小癖好")
    taboos = Column(TEXT, nullable=True, comment="雷区/禁忌")
    expression_habits = Column(TEXT, nullable=True, comment="表达习惯")
    angry_style = Column(TEXT, nullable=True, comment="生气表现")
    happy_style = Column(TEXT, nullable=True, comment="开心表现")
    voice_tone = Column(VARCHAR(64), nullable=False, default="", comment="音色")
    catchphrase = Column(VARCHAR(100), nullable=False, default="", comment="口头禅/开场白")
    greeting = Column(TEXT, nullable=True, comment="初次见面台词")
    system_prompt_extra = Column(TEXT, nullable=True, comment="补充人设指令")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序值")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class AIProactiveLog(Base):
    """AI主动互动记录 - 避免同一件事反复打扰"""
    __tablename__ = "ai_proactive_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    role_key = Column(VARCHAR(64), nullable=False, default="", comment="角色标识")
    trigger_type = Column(VARCHAR(20), nullable=False, default="greeting",
                          comment="触发类型 greeting/care/remind/share")
    content = Column(TEXT, nullable=False, comment="主动说的话")
    ref_key = Column(VARCHAR(64), nullable=False, default="", comment="去重键")
    is_read = Column(TINYINT, nullable=False, default=0, comment="是否已读")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
