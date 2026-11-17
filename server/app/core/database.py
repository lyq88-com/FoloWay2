# -*- coding: utf-8 -*-
"""
数据库引擎与会话管理 - SQLAlchemy 2.0
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# 创建引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # 连接前检测有效性
    pool_recycle=3600,        # 连接回收周期(秒)
    pool_size=10,             # 连接池大小
    max_overflow=20,          # 最大溢出
    echo=settings.app_debug,  # 开发环境打印SQL
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入: 获取数据库会话"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
