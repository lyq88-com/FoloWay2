# -*- coding: utf-8 -*-
"""
用户模型 - C端用户 & B端管理员
"""
from sqlalchemy import Column, BigInteger, Text
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATE, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """C端注册用户"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(VARCHAR(20), nullable=True, unique=True, comment="手机号")
    username = Column(VARCHAR(50), nullable=True, unique=True, comment="登录用户名")
    email = Column(VARCHAR(100), nullable=True, unique=True, comment="邮箱")
    nickname = Column(VARCHAR(50), nullable=False, default="", comment="昵称")
    avatar = Column(VARCHAR(500), nullable=False, default="", comment="头像URL")
    signature = Column(VARCHAR(200), nullable=False, default="", comment="个性签名")
    password_hash = Column(VARCHAR(255), nullable=False, default="", comment="密码哈希")
    wx_openid = Column(VARCHAR(64), nullable=False, default="", comment="微信OpenID")
    wx_unionid = Column(VARCHAR(64), nullable=False, default="", comment="微信UnionID")
    gender = Column(TINYINT, nullable=False, default=0, comment="性别 0未知 1男 2女")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1正常 0禁用")
    # ↓↓↓ 安全合规批次新增（additive，由 sql/migration_proactive_teen.sql 补列） ↓↓↓
    allow_proactive_msg = Column(TINYINT, nullable=False, default=1, comment="允许AI主动消息 1允许 0关闭")
    teen_mode = Column(TINYINT, nullable=False, default=0, comment="青少年模式 1开启 0关闭")
    # ↑↑↑ 新增结束 ↑↑↑
    register_time = Column(DATETIME, nullable=False, comment="注册时间")
    last_login_time = Column(DATETIME, nullable=False, comment="最后登录时间")
    last_login_ip = Column(VARCHAR(45), nullable=False, default="", comment="最后登录IP")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class UserDataBackup(Base):
    """
    注销前用户数据备份（安全合规批次新增）
    用户申请注销时，先把可导出的个人数据打包成 JSON 存这里，再做逻辑清除；
    同时作为「导出我的数据」的留档，便于申诉期恢复。
    由 sql/migration_user_deletion_backup.sql 建表。
    """
    __tablename__ = "user_data_backups"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    backup_type = Column(VARCHAR(20), nullable=False, default="deactivate",
                         comment="备份类型 deactivate注销/export导出")
    data_json = Column(Text, nullable=False, comment="用户数据JSON快照")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class Admin(Base):
    """B端后台管理员"""
    __tablename__ = "admins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(50), nullable=False, unique=True, comment="登录用户名")
    password_hash = Column(VARCHAR(255), nullable=False, comment="密码哈希(bcrypt)")
    nickname = Column(VARCHAR(50), nullable=False, default="", comment="昵称")
    avatar = Column(VARCHAR(500), nullable=False, default="", comment="头像URL")
    role = Column(VARCHAR(20), nullable=False, default="admin", comment="角色 super_admin/admin/operator")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1正常 0禁用")
    last_login_time = Column(DATETIME, nullable=False, default="1970-01-01 00:00:00", comment="最后登录时间")
    last_login_ip = Column(VARCHAR(45), nullable=False, default="", comment="最后登录IP")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
