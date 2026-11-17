# -*- coding: utf-8 -*-
r"""校验陪伴感增强 v3 的迁移结果（只读）"""
import io
import sys

import pymysql

CHECKS = {
    "ai_user_memories": ["memory_layer", "role_key", "role_id", "title",
                         "salience", "source", "is_deleted", "updated_at"],
    "ai_roles": ["backstory", "speech_style", "quirks", "mood", "mood_note",
                 "mood_updated_at", "taboos", "expression_habits", "angry_style",
                 "happy_style", "voice_tone", "nickname", "origin", "creator_id"],
}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                           password="123456", database="ai_habit_partner",
                           charset="utf8mb4")
    ok = True
    try:
        with conn.cursor() as cur:
            for table, cols in CHECKS.items():
                cur.execute(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s", (table,))
                have = {r[0] for r in cur.fetchall()}
                missing = [c for c in cols if c not in have]
                print(f"[{'OK ' if not missing else 'FAIL'}] {table}: "
                      f"{len(cols) - len(missing)}/{len(cols)} 列存在"
                      + (f"，缺失 {missing}" if missing else ""))
                ok = ok and not missing

            cur.execute("SELECT COUNT(*) FROM gacha_character_pool WHERE status = 1")
            print(f"[OK ] gacha_character_pool 角色数: {cur.fetchone()[0]}")

            cur.execute("SELECT role_type, name, mood, voice_tone, "
                        "IFNULL(LEFT(backstory, 18), '') FROM ai_roles ORDER BY id")
            for r in cur.fetchall():
                print(f"      role={r[0]:<10} name={r[1]:<6} mood={r[2]:<8} "
                      f"voice={r[3]:<7} backstory={r[4]}...")
    finally:
        conn.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
