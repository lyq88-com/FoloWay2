# -*- coding: utf-8 -*-
"""
互动扭蛋机模型（模块3）
- GachaTemplate: 扭蛋剧本模板（官方/用户自创）
- UserGachaWallet: 扭蛋币钱包（打卡赚取）
- UserGachaRecord: 抽取记录
- UserGachaFavorite: 用户收藏
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class GachaTemplate(Base):
    """扭蛋剧本模板"""
    __tablename__ = "gacha_templates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    creator_id = Column(BigInteger, nullable=False, default=0, comment="创建者(0=官方)")
    title = Column(VARCHAR(100), nullable=False, comment="剧本标题")
    description = Column(VARCHAR(500), nullable=False, default="", comment="剧本简介")
    category = Column(VARCHAR(20), nullable=False, default="chat", comment="companion/emotion/chat")
    opening_text = Column(VARCHAR(500), nullable=False, default="", comment="AI开场白")
    questions = Column(TEXT, nullable=True, comment="剧情问答JSON")
    is_official = Column(TINYINT, nullable=False, default=0, comment="是否官方")
    use_count = Column(INTEGER, nullable=False, default=0, comment="被抽取次数")
    favorite_count = Column(INTEGER, nullable=False, default=0, comment="收藏数")
    status = Column(TINYINT, nullable=False, default=1, comment="1上架 0下架")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class UserGachaWallet(Base):
    """扭蛋币钱包"""
    __tablename__ = "user_gacha_wallet"

    user_id = Column(BigInteger, primary_key=True, comment="用户ID")
    coin_balance = Column(INTEGER, nullable=False, default=0, comment="当前余额")
    total_earned = Column(INTEGER, nullable=False, default=0, comment="累计获得")
    total_cost = Column(INTEGER, nullable=False, default=0, comment="累计消耗")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class UserGachaRecord(Base):
    """扭蛋抽取记录"""
    __tablename__ = "user_gacha_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    template_id = Column(BigInteger, nullable=False, comment="抽中的剧本")
    cost = Column(INTEGER, nullable=False, default=10, comment="消耗币数")
    status = Column(VARCHAR(10), nullable=False, default="drawn", comment="drawn/finished")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    finished_at = Column(DATETIME, nullable=True, comment="完成时间")


class UserGachaFavorite(Base):
    """用户收藏扭蛋"""
    __tablename__ = "user_gacha_favorites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    template_id = Column(BigInteger, nullable=False)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
