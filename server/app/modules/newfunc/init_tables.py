# -*- coding: utf-8 -*-
"""newfunc 模块自动建表（幂等，参照 focus 模块模式）"""
from app.core.database import engine
from app.modules.newfunc.models import (
    PushRecord, PushSetting, UserDiaryMood, AIBotInfo, AIBotMemory,  # noqa: F401
)

TABLES = [PushRecord.__table__, PushSetting.__table__, UserDiaryMood.__table__,
          AIBotInfo.__table__, AIBotMemory.__table__]


def init_tables():
    for t in TABLES:
        t.create(bind=engine, checkfirst=True)
    print("[newfunc] tables ready:", [t.name for t in TABLES])


if __name__ == "__main__":
    init_tables()
