# -*- coding: utf-8 -*-
"""
虚拟经济模型 - 用户金币/礼物背包/扭蛋券/装扮解锁/账单(云端)

对应表: user_economy
设计要点:
  - 一个用户一行（user_id 唯一），把前端 common/economy.js 里 localStorage 的
    xuntu_economy 状态整体搬到云端，避免清缓存/换设备后资产清零。
  - bills 只保留最近若干条（前端常量 MAX_BILLS=300），避免单行无限膨胀。
  - 复杂结构（礼物背包 / 已解锁装扮 / 账单）用 TEXT 存 JSON 字符串，
    兼容 MySQL 5.6+（本机 5.7 无 JSON 列的生成列能力）。
"""
from sqlalchemy import Column, BigInteger, Text, Index
from sqlalchemy.dialects.mysql import INTEGER, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class UserEconomy(Base):
    """用户虚拟经济状态"""
    __tablename__ = "user_economy"
    __table_args__ = (
        Index("idx_ue_user", "user_id", unique=True),
        {"comment": "用户虚拟经济状态(云端, 替代 localStorage xuntu_economy)"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, nullable=False, comment="用户ID(users.id)")

    # ---- 标量字段（单独成列，便于 SQL 直接统计） ----
    coins = Column(INTEGER, nullable=False, default=0, comment="金币余额")
    gacha_tickets = Column(INTEGER, nullable=False, default=0, comment="扭蛋券数量")
    total_checkin_rewarded = Column(INTEGER, nullable=False, default=0, comment="累计打卡奖励次数")
    gifted_count = Column(INTEGER, nullable=False, default=0, comment="累计送礼次数")

    # ---- JSON 字段 ----
    gift_inventory = Column(Text, nullable=True, comment="礼物背包 JSON {giftId: count}")
    unlocked_decos = Column(Text, nullable=True, comment="已解锁装扮/气泡/背景 id 数组 JSON")
    bills = Column(Text, nullable=True, comment="收支账单 JSON 数组(最多保留最近300条)")

    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment="更新时间")
