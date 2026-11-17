# -*- coding: utf-8 -*-
r"""
用 Python 执行 .sql 迁移脚本（本机没装 mysql CLI 的替代方案）

用法：
    python -u tools\run_sql.py sql\migration_user_economy.sql
"""
import io
import sys

import pymysql


def main():
    if len(sys.argv) < 2:
        print("usage: python -u tools\\run_sql.py <sql-file>")
        return 1

    path = sys.argv[1]
    with io.open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                           password="123456", database="ai_habit_partner",
                           charset="utf8mb4", autocommit=True)
    try:
        with conn.cursor() as cur:
            # 按分号切分，逐条执行（建表脚本里没有含分号的字符串字面量）
            for stmt in sql.split(";"):
                s = stmt.strip()
                if not s:
                    continue
                cur.execute(s)
        print("[OK] 执行完成：" + path)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
