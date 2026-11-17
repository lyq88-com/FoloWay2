# -*- coding: utf-8 -*-
"""
play 模块建表（幂等，不动旧表）

用法（server 目录下）：
    py -3.12 app/modules/play/init_tables.py
"""
import os
import sys

# 允许从 server 目录直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.core.database import engine  # noqa: E402
from app.modules.play.models import UserPlayState, UserCapsule, ShopOrder  # noqa: F401,E402

TABLES = [UserPlayState.__table__, UserCapsule.__table__, ShopOrder.__table__]


def init_tables():
    for t in TABLES:
        t.create(bind=engine, checkfirst=True)
    print("[play] tables ready:", [t.name for t in TABLES])


if __name__ == "__main__":
    init_tables()
