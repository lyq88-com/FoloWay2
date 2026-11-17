# -*- coding: utf-8 -*-
"""
执行「打卡上下文延续」迁移（幂等，可重复运行）

等价于 sql/migration_habit_context.sql，用 Python 执行是为了在没有 mysql
客户端的机器上也能一键跑。

变更清单：
  user_companion_settings.muted_habits_json  TEXT  —— 按习惯的短期静默表
      （用户说「先不说这个了」之后该习惯静默 3 天）

chat_sessions.habit_id 是阶段J 就有的字段，语义正好是「本会话挂载的习惯上下文」，
本次直接复用，不新增列。

用法: python -u tools/apply_migration_habit_context.py
"""
import sys

import pymysql

DB = dict(host="127.0.0.1", port=3306, user="root", password="123456",
          database="ai_habit_partner", charset="utf8mb4", autocommit=True)

NEW_COLS = [
    ("user_companion_settings", "muted_habits_json",
     "TEXT NULL COMMENT '按习惯的短期静默表 {habit_id: 截止时刻}'",
     "habit_topic_off_at"),
]


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    dbname = DB["database"]
    changed = []

    for table, col, ddl, after in NEW_COLS:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
            (dbname, table, col))
        if cur.fetchone()[0]:
            print(f"  = {table}.{col} 已存在，跳过")
            continue
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {ddl} AFTER `{after}`")
        changed.append(f"{table}.{col}")
        print(f"  + {table}.{col} 已添加")

    # chat_sessions.habit_id 复用前的确认（缺了就补，正常环境不会走到）
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='chat_sessions' AND COLUMN_NAME='habit_id'",
        (dbname,))
    if cur.fetchone()[0]:
        print("  = chat_sessions.habit_id 已存在（复用为会话挂载的习惯上下文）")
    else:
        cur.execute("ALTER TABLE `chat_sessions` ADD COLUMN `habit_id` BIGINT NOT NULL DEFAULT 0 "
                    "COMMENT '会话当前挂载的习惯上下文ID(0=普通闲聊)'")
        changed.append("chat_sessions.habit_id")
        print("  + chat_sessions.habit_id 已补建")

    conn.close()
    print("\n迁移完成，本次变更 %d 项：%s" % (len(changed), ", ".join(changed) or "无（全部已就位）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
