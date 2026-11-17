# -*- coding: utf-8 -*-
"""查询某个用户名在 user_economy 里的当前行（用于验证前端是否真的推上来了）"""
import io
import os
import sys

import pymysql

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_economy_row.txt")


def main():
    username = sys.argv[1]
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root",
                           password="123456", database="ai_habit_partner",
                           charset="utf8mb4")
    lines = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT u.username, e.coins, e.gacha_tickets, e.gift_inventory, "
                "e.unlocked_decos, e.total_checkin_rewarded, e.gifted_count, "
                "e.bills, e.updated_at "
                "FROM user_economy e JOIN users u ON u.id = e.user_id "
                "WHERE u.username = %s", (username,))
            row = cur.fetchone()
            if not row:
                lines.append("未找到 %s 的经济行" % username)
            else:
                bills = row[7] or ""
                n = bills.count('"desc"')
                lines.append("username      = %s" % row[0])
                lines.append("coins         = %s" % row[1])
                lines.append("gachaTickets  = %s" % row[2])
                lines.append("giftInventory = %s" % row[3])
                lines.append("unlockedDecos = %s" % row[4])
                lines.append("totalCheckinRewarded = %s" % row[5])
                lines.append("giftedCount   = %s" % row[6])
                lines.append("bills 条数    = %s" % n)
                lines.append("updatedAt     = %s" % row[8])
    finally:
        conn.close()
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
