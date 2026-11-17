# -*- coding: utf-8 -*-
"""
「小想法」独立建表脚本（不删库、不动旧表）
==========================================

用法（在 server 目录下）：
    py -3.12 app/modules/idea/init_tables.py

做的事：
  只对 idea 模块新增的表执行 Base.metadata.create_all，
  已存在的表不动，也不会 drop 任何数据。可安全重复执行。
"""
import os
import sys

# 允许从 server 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy import create_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.modules.idea import models as _idea_models  # noqa: F401,E402  注册模型


IDEA_TABLES = [
    "idea", "idea_resonance", "idea_like", "idea_setting",
    "idea_block", "idea_conversation", "idea_message", "idea_notification",
]


def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    # 只建这几张（create_all 幂等，已存在则跳过）
    sub = Base.metadata
    targets = [sub.tables[t] for t in IDEA_TABLES if t in sub.tables]
    Base.metadata.create_all(engine, tables=targets)
    print(f"[idea] 已确保 {len(targets)} 张表存在：")
    for t in IDEA_TABLES:
        print("   -", t)


if __name__ == "__main__":
    main()
