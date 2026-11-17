# -*- coding: utf-8 -*-
"""
「专注」模块建表脚本
用法：cd liyeqing/server && python app/modules/focus/init_tables.py
只创建 focus_* 新表，绝不触碰任何既有表。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.database import engine  # noqa: E402
from app.modules.focus.models import (  # noqa: E402
    FocusTask, FocusStep, FocusSession, FocusRecord,
    FocusDynamic, FocusDynamicComment, FocusDynamicLike,
    FocusRemind, FocusFollow, FocusSetting,
)

TABLES = [FocusTask, FocusStep, FocusSession, FocusRecord,
          FocusDynamic, FocusDynamicComment, FocusDynamicLike,
          FocusRemind, FocusFollow, FocusSetting]


def main():
    from sqlalchemy.orm import configure_mappers
    import app.models  # noqa: F401  确保全部模型注册
    configure_mappers()

    from sqlalchemy import inspect
    insp = inspect(engine)
    created = []
    for t in TABLES:
        name = t.__tablename__
        if insp.has_table(name):
            print(f"跳过（已存在）: {name}")
            continue
        t.__table__.create(engine)
        created.append(name)
        print(f"已创建: {name}")
    print(f"\n完成，本次新建 {len(created)} 张表: {created}")


if __name__ == "__main__":
    main()
