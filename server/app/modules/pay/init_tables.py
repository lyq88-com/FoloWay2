# -*- coding: utf-8 -*-
"""pay 模块建表（幂等）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.core.database import engine  # noqa: E402
from app.modules.pay.models import PayOrder, UserVip  # noqa: F401,E402

TABLES = [PayOrder.__table__, UserVip.__table__]


def init_pay_tables():
    for t in TABLES:
        t.create(bind=engine, checkfirst=True)
    print("[pay] tables ready:", [t.name for t in TABLES])


if __name__ == "__main__":
    init_pay_tables()
