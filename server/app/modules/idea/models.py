# -*- coding: utf-8 -*-
"""
「小想法 · 共鸣匹配」ORM 模型

命名严格遵循需求：idea / idea_resonance / idea_like
另附 5 张支撑表（总开关 / 拉黑 / 私聊会话 / 私聊消息 / 通知），
均为本模块独有，不与任何既有表产生外键耦合，保证隔离。

字段类型沿用项目既有风格（BigInteger 主键 + mysql 方言 VARCHAR/TINYINT/DATETIME/TEXT）。
"""
from sqlalchemy import Column, BigInteger, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


# ============================================================
# 1. 小想法主表
# ============================================================
class Idea(Base):
    """一条「小想法」：一句话碎念（支持单张配图、可匿名）"""
    __tablename__ = "idea"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="发布用户ID")
    content = Column(VARCHAR(500), nullable=False, default="", comment="想法文字(前端限 200 字)")
    image = Column(VARCHAR(500), nullable=False, default="", comment="单图相对路径, 空=无图")
    is_anonymous = Column(TINYINT, nullable=False, default=0, comment="是否匿名发布 0否 1是")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="发布时间")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除 0正常 1已删除")
    expire_time = Column(DATETIME, nullable=True, comment="过期时间(预留, 当前不启用)")

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "content": self.content or "",
            "image": self.image or "",
            "is_anonymous": self.is_anonymous or 0,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else "",
        }


# ============================================================
# 2. 共鸣匹配记录
# ============================================================
class IdeaResonance(Base):
    """
    共鸣匹配记录：把「本人的想法」与「匹配到的他人想法」配对。
    - idea_id        : 本人的想法
    - target_idea_id : 匹配到的、属于 target_uid 的想法
    - source_uid     : 本条记录归属者（= 本人的想法发布者）
    双向发布时会为双方各写一条，双方才能各自看到对方并回点亮。
    """
    __tablename__ = "idea_resonance"
    __table_args__ = (
        UniqueConstraint("idea_id", "target_idea_id", name="uk_idea_resonance_pair"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    idea_id = Column(BigInteger, nullable=False, comment="本人的想法ID")
    target_idea_id = Column(BigInteger, nullable=False, comment="匹配到的他人想法ID")
    source_uid = Column(BigInteger, nullable=False, comment="本人用户ID(记录归属)")
    target_uid = Column(BigInteger, nullable=False, comment="对方用户ID")
    resonance_score = Column(INTEGER, nullable=False, default=0, comment="语义相似度 0-10000")
    is_viewed = Column(TINYINT, nullable=False, default=0, comment="是否已查看 0否 1是")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 3. 点亮 / 轻互动记录
# ============================================================
class IdeaLike(Base):
    """
    点亮与轻互动。
    action_type 枚举：
      light    点亮（核心，用于判定双向点亮）
      good     好棒
      agree    同意
      highfive 击掌
      pat      摸摸头
    唯一约束：同一用户 × 同一条 idea × 同一种 action 只能提交一次。
    """
    __tablename__ = "idea_like"
    __table_args__ = (
        UniqueConstraint("idea_id", "from_uid", "action_type", name="uk_idea_like_action"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    idea_id = Column(BigInteger, nullable=False, comment="被操作的想法ID")
    from_uid = Column(BigInteger, nullable=False, comment="发起用户ID")
    to_uid = Column(BigInteger, nullable=False, comment="想法归属用户ID")
    action_type = Column(VARCHAR(20), nullable=False, comment="light/good/agree/highfive/pat")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 4. 用户级总开关
# ============================================================
class IdeaSetting(Base):
    """「接受共鸣匹配」总开关（关闭后：不被匹配到，发布也不再推送共鸣）"""
    __tablename__ = "idea_setting"
    __table_args__ = (UniqueConstraint("user_id", name="uk_idea_setting_user"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID(唯一)")
    accept_resonance = Column(TINYINT, nullable=False, default=1, comment="接受共鸣匹配 0关 1开")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())


# ============================================================
# 5. 全局拉黑
# ============================================================
class IdeaBlock(Base):
    """全局拉黑关系（单向）。拉黑后双方想法/共鸣/点亮互不匹配、互不可见。"""
    __tablename__ = "idea_block"
    __table_args__ = (UniqueConstraint("user_id", "blocked_uid", name="uk_idea_block_pair"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="发起拉黑者")
    blocked_uid = Column(BigInteger, nullable=False, comment="被拉黑者")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 6. 双向点亮后的真人私聊
# ============================================================
class IdeaConversation(Base):
    """真人私聊会话（双方 ID 恒按 小-大 归一键，保证唯一）"""
    __tablename__ = "idea_conversation"
    __table_args__ = (
        UniqueConstraint("user_a", "user_b", name="uk_idea_conv_pair"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_a = Column(BigInteger, nullable=False, comment="用户A(较小ID)")
    user_b = Column(BigInteger, nullable=False, comment="用户B(较大ID)")
    idea_a = Column(BigInteger, nullable=False, default=0, comment="A的想法ID(来源)")
    idea_b = Column(BigInteger, nullable=False, default=0, comment="B的想法ID(来源)")
    last_message = Column(VARCHAR(200), nullable=False, default="", comment="最后一条消息摘要")
    last_time = Column(DATETIME, nullable=True, comment="最后消息时间")
    unread_a = Column(INTEGER, nullable=False, default=0, comment="A未读数")
    unread_b = Column(INTEGER, nullable=False, default=0, comment="B未读数")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class IdeaMessage(Base):
    """真人私聊消息"""
    __tablename__ = "idea_message"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, nullable=False, comment="会话ID")
    from_uid = Column(BigInteger, nullable=False)
    to_uid = Column(BigInteger, nullable=False)
    content = Column(VARCHAR(1000), nullable=False, default="")
    msg_type = Column(VARCHAR(20), nullable=False, default="text", comment="text/react")
    is_read = Column(TINYINT, nullable=False, default=0)
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 7. 通知（与消息小红点打通）
# ============================================================
class IdeaNotification(Base):
    """点亮 / 双向匹配 / 轻互动 通知。type 用于前端分类展示。"""
    __tablename__ = "idea_notification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="接收者")
    ntype = Column(VARCHAR(20), nullable=False, comment="light/matched/react")
    title = Column(VARCHAR(100), nullable=False, default="")
    content = Column(VARCHAR(255), nullable=False, default="")
    ref_id = Column(BigInteger, nullable=False, default=0, comment="关联会话ID或想法ID")
    is_read = Column(TINYINT, nullable=False, default=0)
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
