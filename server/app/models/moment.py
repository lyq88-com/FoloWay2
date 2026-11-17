# -*- coding: utf-8 -*-
"""
朋友圈模型 - 动态/点赞/评论
"""
from sqlalchemy import Column, BigInteger, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, TEXT, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class Moment(Base):
    """朋友圈动态"""
    __tablename__ = "moments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="发布者用户ID")
    content = Column(TEXT, nullable=True, comment="文字内容")
    images = Column(TEXT, nullable=False, default="", comment="图片URL数组JSON")
    location = Column(VARCHAR(100), nullable=False, default="", comment="位置")
    like_count = Column(BigInteger, nullable=False, default=0, comment="点赞数(冗余计数)")
    comment_count = Column(BigInteger, nullable=False, default=0, comment="评论数(冗余计数)")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1正常 0已删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class MomentLike(Base):
    """朋友圈点赞"""
    __tablename__ = "moment_likes"
    __table_args__ = (
        # 同一用户对同一条动态只能点赞一次
        UniqueConstraint("moment_id", "user_id", name="uk_moment_user_like"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    moment_id = Column(BigInteger, nullable=False, comment="动态ID")
    user_id = Column(BigInteger, nullable=False, comment="点赞用户ID")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class MomentComment(Base):
    """朋友圈评论"""
    __tablename__ = "moment_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    moment_id = Column(BigInteger, nullable=False, comment="动态ID")
    user_id = Column(BigInteger, nullable=False, comment="评论用户ID")
    content = Column(VARCHAR(500), nullable=False, comment="评论内容")
    reply_to_id = Column(BigInteger, nullable=False, default=0, comment="回复的评论ID(0=直接评论)")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1正常 0已删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
