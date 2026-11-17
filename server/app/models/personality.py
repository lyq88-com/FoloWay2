# -*- coding: utf-8 -*-
"""
性格测评模型 - 用户性格测评结果(云端)

对应表: user_personality_results
设计要点:
  - 一个用户可以有多条历史记录(多次重测), 只有 is_active=1 的那条是当前生效结果
  - 单生效位由应用层保证: 写入新结果前先把该用户所有 is_active=1 的行置 0
    (MySQL 5.7 不支持"部分唯一索引", 无法用 UNIQUE(user_id, is_active) 直接约束,
     若升级 MySQL 8 可改用生成列实现数据库级约束)
"""
from sqlalchemy import Column, BigInteger, Text, Index
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class UserPersonalityResult(Base):
    """用户性格测评结果"""
    __tablename__ = "user_personality_results"
    __table_args__ = (
        Index("idx_upr_user_active", "user_id", "is_active"),
        Index("idx_upr_user_created", "user_id", "created_at"),
        {"comment": "用户性格测评结果(云端, is_active=1 为当前生效)"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(BigInteger, nullable=False, comment="用户ID(users.id)")

    # ---- 四维结果 ----
    personality = Column(VARCHAR(20), nullable=False, default="",
                         comment="性格特质 anxious/perfect/procrastinator/buddha")
    emotional_resilience = Column(VARCHAR(20), nullable=False, default="",
                                  comment="情绪韧性 low/medium/high")
    procrastination = Column(VARCHAR(20), nullable=False, default="",
                             comment="拖延程度 low/medium/high")
    companion_style = Column(VARCHAR(20), nullable=False, default="",
                             comment="陪伴偏好 warm/smart/energetic/creative")

    # ---- 过程数据(TEXT 存 JSON 字符串, 兼容 MySQL 5.6+) ----
    raw_scores = Column(Text, nullable=True, comment="四维原始分 JSON")
    answers = Column(Text, nullable=True, comment="8题作答明细 JSON(可为空)")

    # ---- 元数据 ----
    quiz_version = Column(VARCHAR(20), nullable=False, default="v1", comment="题库版本")
    source = Column(VARCHAR(20), nullable=False, default="app", comment="来源 app/admin/import/migrate")
    is_active = Column(TINYINT, nullable=False, default=1, comment="是否当前生效 1生效 0历史")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment="更新时间")
