# -*- coding: utf-8 -*-
"""
世界世界观 + AI角色互动笔记模型（模块1 + 模块4）
- World:             虚拟世界（公开/私人）
- WorldRole:         世界成员（AI角色 + 用户，join_type 区分）
- WorldNote:         世界笔记（AI角色笔记 / 用户打卡笔记 / 打卡AI反馈）
- WorldNoteComment:  笔记评论（AI互评 / 用户评论）
- WorldPlot:         世界剧情碎片（打卡任务解锁）
- WorldPlotUnlock:   用户剧情解锁记录
- WorldRelation:     AI角色关系（同世界互评产生变化）
"""
from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class World(Base):
    """虚拟世界"""
    __tablename__ = "worlds"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    creator_id = Column(BigInteger, nullable=False, comment="创建者用户ID")
    name = Column(VARCHAR(100), nullable=False, comment="世界名字")
    description = Column(VARCHAR(1000), nullable=False, default="", comment="世界描述")
    rules = Column(TEXT, nullable=True, comment="世界观规则")
    cover = Column(VARCHAR(500), nullable=False, default="", comment="封面图")
    is_public = Column(TINYINT, nullable=False, default=1, comment="1公开 0私人")
    member_count = Column(INTEGER, nullable=False, default=1, comment="成员数")
    note_count = Column(INTEGER, nullable=False, default=0, comment="笔记数")
    checkin_target = Column(INTEGER, nullable=False, default=3, comment="解锁剧情所需打卡数")
    checkin_total = Column(INTEGER, nullable=False, default=0, comment="世界累计打卡数")
    status = Column(TINYINT, nullable=False, default=1, comment="1正常 0删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class WorldRole(Base):
    """世界成员（AI角色 / 用户）"""
    __tablename__ = "world_roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_id = Column(BigInteger, nullable=False, comment="世界ID")
    role_id = Column(BigInteger, nullable=False, default=0, comment="AI角色ID（自设为0）")
    role_name = Column(VARCHAR(50), nullable=False, default="", comment="角色名")
    role_avatar = Column(VARCHAR(500), nullable=False, default="", comment="头像emoji/URL")
    is_custom = Column(TINYINT, nullable=False, default=0, comment="是否自设角色")
    join_type = Column(VARCHAR(10), nullable=False, default="ai", comment="ai / user")
    user_id = Column(BigInteger, nullable=False, default=0, comment="用户成员ID")
    is_active = Column(TINYINT, nullable=False, default=1, comment="是否在世界内")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class WorldNote(Base):
    """世界笔记（AI笔记 / 用户打卡笔记 / 打卡AI反馈）"""
    __tablename__ = "world_notes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_id = Column(BigInteger, nullable=False, comment="世界ID")
    author_role_id = Column(BigInteger, nullable=False, default=0, comment="AI作者ID")
    author_user_id = Column(BigInteger, nullable=False, default=0, comment="用户作者ID")
    author_name = Column(VARCHAR(50), nullable=False, default="", comment="作者显示名")
    author_avatar = Column(VARCHAR(500), nullable=False, default="", comment="作者头像")
    note_type = Column(VARCHAR(20), nullable=False, default="normal", comment="normal/checkin/feedback/system")
    content = Column(VARCHAR(1000), nullable=False, comment="笔记内容")
    related_user_id = Column(BigInteger, nullable=False, default=0, comment="关联用户")
    related_habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯")
    comment_count = Column(INTEGER, nullable=False, default=0, comment="评论数")
    status = Column(TINYINT, nullable=False, default=1, comment="1正常 0删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class WorldNoteComment(Base):
    """世界笔记评论（AI互评 / 用户评论）"""
    __tablename__ = "world_note_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    note_id = Column(BigInteger, nullable=False, comment="笔记ID")
    author_role_id = Column(BigInteger, nullable=False, default=0, comment="AI评论者")
    author_user_id = Column(BigInteger, nullable=False, default=0, comment="用户评论者")
    author_name = Column(VARCHAR(50), nullable=False, default="")
    author_avatar = Column(VARCHAR(500), nullable=False, default="")
    content = Column(VARCHAR(500), nullable=False, comment="评论内容")
    reply_to_id = Column(BigInteger, nullable=False, default=0, comment="回复评论ID")
    status = Column(TINYINT, nullable=False, default=1)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class WorldPlot(Base):
    """世界剧情碎片"""
    __tablename__ = "world_plots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_id = Column(BigInteger, nullable=False, comment="世界ID")
    title = Column(VARCHAR(100), nullable=False, comment="剧情标题")
    content = Column(TEXT, nullable=False, comment="剧情内容")
    required_checkins = Column(INTEGER, nullable=False, default=3, comment="解锁所需打卡数")
    sort_order = Column(INTEGER, nullable=False, default=0)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class WorldPlotUnlock(Base):
    """用户剧情解锁记录"""
    __tablename__ = "world_plot_unlocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    plot_id = Column(BigInteger, nullable=False)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class WorldRelation(Base):
    """AI角色关系"""
    __tablename__ = "world_relations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    world_id = Column(BigInteger, nullable=False)
    role_a_id = Column(BigInteger, nullable=False, comment="角色A")
    role_b_id = Column(BigInteger, nullable=False, comment="角色B")
    relation_label = Column(VARCHAR(50), nullable=False, default="初识", comment="关系标签")
    score = Column(INTEGER, nullable=False, default=0, comment="关系分值")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
