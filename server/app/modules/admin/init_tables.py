# -*- coding: utf-8 -*-
"""admin 模块建表（幂等，不动旧表）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.core.database import engine  # noqa: E402
from app.modules.admin.models import AdminLog, AdminReview  # noqa: F401,E402

TABLES = [AdminLog.__table__, AdminReview.__table__]


def init_admin_tables():
    for t in TABLES:
        t.create(bind=engine, checkfirst=True)
    print("[admin] tables ready:", [t.name for t in TABLES])


if __name__ == "__main__":
    init_admin_tables()
