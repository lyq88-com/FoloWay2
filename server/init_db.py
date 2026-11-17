# -*- coding: utf-8 -*-
"""
一键初始化数据库 (推荐新环境使用)

用法: 在 server 目录下执行
    py -3.12 init_db.py

做的事:
  1. 删除并重建 ai_habit_partner 数据库 (危险! 会清空所有数据)
  2. 用 SQLAlchemy ORM 模型 create_all 建全部表 (保证与代码一致, 解决 init.sql 与模型不同步问题)
  3. 导入 sql/seed_data.sql 种子数据 (管理员/任务模板/AI角色/徽章/配置/音频)

注意: 数据库连接参数读取 .env (DB_HOST/DB_PORT/DB_USER/DB_PASSWORD)
"""
import os
import sys
import pymysql
from sqlalchemy import create_engine

from app.core.config import settings
import app.models  # noqa: F401  确保所有模型注册到 Base.metadata
from app.core.database import Base


SEED_TABLES = [
    "admins", "task_templates", "ai_roles", "ai_role_assets",
    "badges", "app_configs", "audio_resources",
]


def add_server_defaults(engine):
    """
    模型里 default= 是 Python 侧默认值, 不会写进 DDL;
    裸 SQL 种子数据 INSERT 不带这些列时会报 1364。
    这里按模型里的 scalar default 给这些列补上 MySQL 服务端默认值。
    """
    from datetime import date, datetime

    def render(val):
        if isinstance(val, bool):
            return "1" if val else "0"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, (date, datetime)):
            return "'" + str(val) + "'"
        return "'" + str(val).replace("\\", "\\\\").replace("'", "\\'") + "'"

    stmts = []
    for t in SEED_TABLES:
        tbl = Base.metadata.tables.get(t)
        if tbl is None:
            continue
        for c in tbl.columns:
            if c.nullable or c.primary_key:
                continue
            if c.server_default is not None or c.default is None:
                continue
            if not getattr(c.default, "is_scalar", False):
                continue
            stmts.append(
                "ALTER TABLE %s ALTER COLUMN %s SET DEFAULT %s"
                % (t, c.name, render(c.default.arg))
            )
    with engine.begin() as conn:
        for s in stmts:
            conn.exec_driver_sql(s)
    return len(stmts)


def main():
    # 1. 删库重建
    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port,
        user=settings.db_user, password=settings.db_password,
        charset="utf8mb4",
    )
    with conn.cursor() as cur:
        cur.execute(
            f"DROP DATABASE IF EXISTS {settings.db_name}"
        )
        cur.execute(
            f"CREATE DATABASE {settings.db_name} "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
    conn.close()
    print("[1/3] 数据库已重建")

    # 2. 按 ORM 模型建表
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    table_count = len(Base.metadata.tables)
    print(f"[2/4] 已按 ORM 模型创建 {table_count} 张表")

    # 3. 给种子表的 NOT NULL 列补服务端默认值
    n = add_server_defaults(engine)
    print(f"[3/4] 已为 {n} 个列补充服务端默认值")

    # 4. 导入种子数据
    seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql", "seed_data.sql")
    with open(seed_path, "r", encoding="utf-8") as f:
        raw = f.read()
    # 去掉注释行, 按分号粗切分 (种子数据里 JSON 字符串不含分号)
    stmts = []
    buf = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    if buf:
        stmts.append("\n".join(buf))

    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port,
        user=settings.db_user, password=settings.db_password,
        database=settings.db_name, charset="utf8mb4",
    )
    with conn.cursor() as cur:
        for s in stmts:
            cur.execute(s)
    conn.commit()
    conn.close()
    print(f"[4/4] 已导入 {len(stmts)} 条种子数据语句")
    print("完成! 默认管理员: admin / admin123")


if __name__ == "__main__":
    sys.exit(main())
