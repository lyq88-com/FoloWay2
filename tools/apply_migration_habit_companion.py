# -*- coding: utf-8 -*-
"""
执行「习惯-伙伴融合」迁移（幂等，可重复运行）

等价于 server/sql/migration_habit_companion.sql，用 Python 执行是为了
在没有 mysql 客户端的机器上也能一键跑。

用法: python -u tools/apply_migration_habit_companion.py
"""
import os
import sys

import pymysql

DB = dict(host="127.0.0.1", port=3306, user="root", password="123456",
          database="ai_habit_partner", charset="utf8mb4", autocommit=True)

# habits 新增字段
NEW_COLS = [
    ("is_paused", "TINYINT NOT NULL DEFAULT 0 COMMENT '是否暂停 0进行中 1已暂停(不触发打卡校验/不推送提醒/数据保留)'"),
    ("paused_at", "DATETIME NULL COMMENT '最近一次暂停时间'"),
    ("paused_reason", "VARCHAR(100) NOT NULL DEFAULT '' COMMENT '暂停时的状态备注'"),
    ("resume_count", "INT NOT NULL DEFAULT 0 COMMENT '重启次数'"),
    ("last_resume_at", "DATETIME NULL COMMENT '最近一次重启时间'"),
]

BADGES = [
    ("habit_restart", "重新出发", "停下来之后又把它捡起来了，重新开始同样值得被记住。", "🔄"),
    ("self_acceptance", "自我接纳", "在撑不住的时候选择先照顾自己，而不是硬扛。", "🫂"),
]


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    dbname = DB["database"]
    changed = []

    # 1) habits 加列
    for col, ddl in NEW_COLS:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='habits' AND COLUMN_NAME=%s",
            (dbname, col))
        if cur.fetchone()[0]:
            print(f"  = habits.{col} 已存在，跳过")
            continue
        cur.execute(f"ALTER TABLE `habits` ADD COLUMN `{col}` {ddl}")
        changed.append(f"habits.{col}")
        print(f"  + habits.{col} 已添加")

    # 2) 索引
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='habits' AND INDEX_NAME='idx_user_paused'",
        (dbname,))
    if cur.fetchone()[0]:
        print("  = idx_user_paused 已存在，跳过")
    else:
        cur.execute("ALTER TABLE `habits` ADD INDEX `idx_user_paused` (`user_id`, `is_paused`)")
        changed.append("idx_user_paused")
        print("  + idx_user_paused 已添加")

    # 3) 设置表
    cur.execute("SHOW TABLES LIKE 'user_companion_settings'")
    if cur.fetchone():
        print("  = user_companion_settings 已存在，跳过")
    else:
        cur.execute("""
            CREATE TABLE `user_companion_settings` (
              `id` BIGINT NOT NULL AUTO_INCREMENT,
              `user_id` BIGINT NOT NULL COMMENT '用户ID',
              `allow_habit_topic` TINYINT NOT NULL DEFAULT 1 COMMENT '【允许伙伴和我聊习惯相关的事】1是 0否',
              `habit_proactive_muted_until` DATETIME NULL COMMENT '习惯类主动消息降频截止时刻',
              `habit_topic_off_at` DATETIME NULL COMMENT '最近一次关闭习惯话题的时间',
              `note` TEXT NULL COMMENT '备注',
              `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `uk_user` (`user_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
              COMMENT='用户与伙伴相处偏好（习惯话题总开关等）'
        """)
        changed.append("user_companion_settings")
        print("  + user_companion_settings 已创建")

    # 4) 徽章种子
    for code, name, desc, icon in BADGES:
        cur.execute("SELECT id FROM badges WHERE code=%s", (code,))
        if cur.fetchone():
            print(f"  = 徽章 {code} 已存在，跳过")
            continue
        cur.execute(
            "INSERT INTO `badges` (`code`,`name`,`description`,`icon`,`condition_type`,`condition_value`,`status`) "
            "VALUES (%s,%s,%s,%s,'habit_event',1,1)",
            (code, name, desc, icon))
        changed.append(f"badge:{code}")
        print(f"  + 徽章 {code}（{name}）已插入")

    conn.close()
    print("\n迁移完成，本次变更 %d 项：%s" % (len(changed), ", ".join(changed) or "无"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
