# -*- coding: utf-8 -*-
"""
习惯-情绪关联接口 端到端验证脚本
1) 注册临时用户 -> 取 token
2) 建 3 个习惯
3) 直连 DB 造 10 天打卡 + 10 天情绪记录（HTTP 的补卡只允许昨天，故历史数据直接落库）
4) 打 GET /api/v1/stats/emotion/habit-correlation 看是否返回「每个习惯一行」的数组
"""
import sys
import json
import random
from datetime import date, timedelta, datetime

import requests

sys.path.insert(0, r"C:\Users\小青\Desktop\新建文件夹\liyeqing\server")

BASE = "http://127.0.0.1:8000/api/v1"
STAMP = datetime.now().strftime("%m%d%H%M%S")
USERNAME = "corr_%s" % STAMP


def new_user():
    r = requests.post(BASE + "/auth/register-username",
                      json={"username": USERNAME, "password": "test123456"},
                      timeout=10)
    d = r.json()
    if d.get("code") != 200:
        raise SystemExit("注册失败: %s" % d)
    return d["data"]["access_token"], d["data"]["user"]["id"]


def create_habit(token, name, icon):
    r = requests.post(BASE + "/habit/create",
                      headers={"Authorization": "Bearer " + token},
                      json={"template_id": 0, "name": name, "icon": icon,
                            "description": "", "target": "", "difficulty": "medium",
                            "color": "#4CAF50", "reminder_time": ""},
                      timeout=10)
    d = r.json()
    if d.get("code") != 200:
        raise SystemExit("建习惯失败: %s" % d)
    return d["data"]["id"]


def add_emotion(token, day, emotion, intensity):
    r = requests.post(BASE + "/emotion/create",
                      headers={"Authorization": "Bearer " + token},
                      json={"emotion": emotion, "intensity": intensity,
                            "record_date": str(day), "description": "E2E"},
                      timeout=10)
    d = r.json()
    if d.get("code") != 200:
        print("  情绪记录失败(%s): %s" % (day, d))


def seed_history(uid, habits):
    from app.core.database import SessionLocal
    from app.models.habit import Checkin, CheckinItem

    today = date.today()
    days = [today - timedelta(days=i) for i in range(9, -1, -1)]  # 10 天，升序

    db = SessionLocal()
    try:
        for idx, d in enumerate(days):
            ck = Checkin(user_id=uid, checkin_date=d, total_habits=len(habits),
                         completed_count=0, completion_rate=0, streak_days=0)
            db.add(ck)
            db.flush()

            # habit A: 前 6 天完成；habit B: 后 6 天完成；habit C: 天天完成
            plan = {habits[0]: idx < 6, habits[1]: idx >= 4, habits[2]: True}
            for hid, ok in plan.items():
                db.add(CheckinItem(checkin_id=ck.id, user_id=uid, habit_id=hid,
                                   completed=1 if ok else 0))
        db.commit()
    finally:
        db.close()
    return days


def main():
    token, uid = new_user()
    print("用户: %s (id=%s)" % (USERNAME, uid))

    names = [("习惯A早起", "🌅"), ("习惯B跑步", "🏃"), ("习惯C阅读", "📖")]
    habits = [create_habit(token, n, i) for n, i in names]
    print("习惯: %s" % habits)

    days = seed_history(uid, habits)
    # 习惯A 完成的前6天 -> 开心高强度；未完成 -> 疲惫低强度
    for idx, d in enumerate(days):
        if idx < 6:
            add_emotion(token, d, "happy", 8)
        else:
            add_emotion(token, d, "tired", 7)

    r = requests.get(BASE + "/stats/emotion/habit-correlation",
                     headers={"Authorization": "Bearer " + token},
                     params={"period": "30d"}, timeout=15)
    print("\nHTTP %s" % r.status_code)
    body = r.json()
    print("code=%s  message=%s" % (body.get("code"), body.get("message")))
    data = body.get("data")
    print("data 类型 = %s" % type(data).__name__)
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # 断言
    assert body.get("code") == 200, "接口未返回 200"
    assert isinstance(data, list), "返回不是数组，前端组件会显示暂无数据"
    assert len(data) == 3, "应包含 3 个习惯"
    m = {x["habit_name"]: x for x in data}
    assert m["习惯A早起"]["correlation"] > 0.7, "A 应呈强正向关联"
    assert m["习惯A早起"]["improvement"] > 0, "A 改善应为正"
    assert m["习惯B跑步"]["correlation"] < 0.7, "B 打卡日情绪更差，关联应偏低"
    print("\n✅ 全部断言通过 —— 接口已返回逐习惯真实关联数据")


if __name__ == "__main__":
    main()
