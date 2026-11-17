# -*- coding: utf-8 -*-
"""
admin 模块 ORM 模型（只新增两张表，旧表保持只读/原样）

  admin_logs    管理员操作日志
  admin_reviews 内容审核结果（聊天记录 / 打卡日记）
"""
from sqlalchemy import Column, BigInteger, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class AdminLog(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"
    __table_args__ = (
        Index("idx_admin_log_created", "created_at"),
        {"comment": "管理后台操作日志"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False, default=0, comment="管理员ID")
    admin_name = Column(VARCHAR(50), nullable=False, default="", comment="管理员名称快照")
    action = Column(VARCHAR(50), nullable=False, default="", comment="动作：登录/更新用户状态/审核内容等")
    target_type = Column(VARCHAR(20), nullable=False, default="", comment="对象类型 auth/user/template/role/content")
    target_id = Column(BigInteger, nullable=False, default=0, comment="对象ID")
    detail = Column(VARCHAR(255), nullable=False, default="", comment="详情")
    ip = Column(VARCHAR(45), nullable=False, default="", comment="操作IP")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        comment="操作时间")

    def to_dict(self):
        return {
            "id": self.id,
            "adminId": self.admin_id,
            "adminName": self.admin_name,
            "action": self.action,
            "targetType": self.target_type,
            "targetId": self.target_id,
            "detail": self.detail,
            "ip": self.ip,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class AdminReview(Base):
    """内容审核结果（同一条内容只保留一条最新结论）"""
    __tablename__ = "admin_reviews"
    __table_args__ = (
        UniqueConstraint("target_type", "target_id", name="uk_admin_review_target"),
        {"comment": "内容审核结果"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    target_type = Column(VARCHAR(20), nullable=False, comment="chat / checkin")
    target_id = Column(BigInteger, nullable=False, comment="聊天消息ID / 打卡日记ID")
    status = Column(VARCHAR(16), nullable=False, default="pending", comment="pending/approved/rejected")
    admin_id = Column(BigInteger, nullable=False, default=0, comment="审核人")
    remark = Column(TEXT, nullable=True, comment="审核备注")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
