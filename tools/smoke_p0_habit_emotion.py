# -*- coding: utf-8 -*-
"""
P0 自测：打卡情绪 → emotion_records

覆盖：
1. 打卡带 emotion 且库里没有近期同情绪记录 → 写一条 emotion_records
2. 同一天同一情绪重复写 → 不新增（避免污染「近期负面情绪占比」统计）
3. 打卡留言带 emotion → 同样落 emotion_records
4. 情绪只补不覆盖：用户自己在情绪页记过的记录不会被改写

用法（在 liyeqing/server 目录下）:
    python -u ../tools/smoke_p0_habit_emotion.py
"""
import os
import sys
import random
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from app.core.database import get_db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.habit import Habit, Checkin, CheckinItem  # noqa: E402
from app.models.emotion import EmotionRecord  # noqa: E402
from app.schemas.habit import HabitCreate, CheckinRequest  # noqa: E402
from app.api.v1.habit import create_habit, checkin, save_diary  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  ({detail})" if detail else ""))


def count_emotion(db, uid, emotion, habit_id=None):
    q = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == uid,
        EmotionRecord.emotion == emotion,
        EmotionRecord.record_date == date.today(),
    )
    if habit_id:
        q = q.filter(EmotionRecord.habit_id == habit_id)
    return q.count()


def main():
    db = next(get_db())
    now = datetime.now()
    uname = "p0emo_%04d" % random.randint(1000, 9999)
    user = User(username=uname, nickname="自测", password_hash="x", phone="",
                register_time=now, last_login_time=now)
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    print(f"\n测试用户 id={uid} ({uname})\n")

    try:
        # ---------- 1. 打卡带情绪 → 落库 ----------
        print("[1] 打卡带情绪 → 写入 emotion_records")
        h1 = create_habit(req=HabitCreate(name="晚饭后散步", target="20分钟",
                                          hope="想让晚上松一点"),
                          user_id=uid, db=db).data["id"]
        r = checkin(req=CheckinRequest(habit_id=h1, emotion="tired", note="今天很累"),
                    user_id=uid, db=db)
        check("打卡成功", r.code == 200, r.message)
        n = count_emotion(db, uid, "tired", habit_id=h1)
        check("emotion_records 写入 1 条 tired", n == 1, f"count={n}")

        rec = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == uid, EmotionRecord.emotion == "tired"
        ).first()
        check("记录关联到该习惯", rec and rec.habit_id == h1, str(rec.habit_id if rec else None))
        check("记录带上留言描述", rec and ("累" in (rec.description or "")), (rec.description if rec else "")[:20])
        check("默认强度 5", rec and rec.intensity == 5, str(rec.intensity if rec else None))

        # ---------- 2. 只补不覆盖：已存在的不重复写 ----------
        print("\n[2] 同一天同一情绪不重复写")
        h2 = create_habit(req=HabitCreate(name="睡前拉伸", target="5分钟"),
                          user_id=uid, db=db).data["id"]
        checkin(req=CheckinRequest(habit_id=h2, emotion="tired"), user_id=uid, db=db)
        # 库里已有今天的 tired（来自 h1），不应再新增
        n2 = count_emotion(db, uid, "tired")
        check("第二次同情绪不新增", n2 == 1, f"count={n2}")

        # ---------- 3. 打卡留言带情绪 → 落库 ----------
        print("\n[3] 打卡留言带情绪 → 写入 emotion_records")
        n3_before = count_emotion(db, uid, "happy")
        res = save_diary(habit_id=h1, data={"content": "今天走得挺舒服", "emotion": "happy"},
                         user_id=uid, db=db)
        check("日记接口返回 200", res.code == 200, res.message)
        check("返回 emotion_id", bool((res.data or {}).get("emotion_id")),
              str((res.data or {}).get("emotion_id")))
        n3 = count_emotion(db, uid, "happy")
        check("emotion_records 写入 happy", n3 == n3_before + 1, f"before={n3_before} now={n3}")

        # 再发一次同情绪 → 仍然只有一条
        save_diary(habit_id=h1, data={"content": "又写了一句", "emotion": "happy"},
                   user_id=uid, db=db)
        n4 = count_emotion(db, uid, "happy")
        check("重复提交同情绪仍只有 1 条", n4 == n3_before + 1, f"count={n4}")

        # ---------- 4. 只在用户没记过时才补 ----------
        print("\n[4] 用户自己在情绪页记过 → 不覆盖他的记录")
        mine = EmotionRecord(user_id=uid, habit_id=0, emotion="sad", intensity=8,
                             description="我自己记的", record_date=date.today())
        db.add(mine)
        db.commit()
        db.refresh(mine)
        h3 = create_habit(req=HabitCreate(name="写三行日记", target="三行"),
                          user_id=uid, db=db).data["id"]
        checkin(req=CheckinRequest(habit_id=h3, emotion="sad"), user_id=uid, db=db)
        rows = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == uid,
            EmotionRecord.emotion == "sad",
            EmotionRecord.record_date == date.today(),
        ).all()
        check("没有新增重复记录", len(rows) == 1, f"count={len(rows)}")
        check("原有记录强度未被改写", rows and rows[0].intensity == 8,
              str(rows[0].intensity if rows else None))

    finally:
        print("\n[cleanup] 清理测试数据")
        db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).delete()
        items = db.query(CheckinItem).filter(CheckinItem.user_id == uid).all()
        for it in items:
            db.delete(it)
        db.query(Checkin).filter(Checkin.user_id == uid).delete()
        db.query(Habit).filter(Habit.user_id == uid).delete()
        db.query(User).filter(User.id == uid).delete()
        db.commit()
        db.close()

    print("\n" + "=" * 60)
    print(f"结果: PASS {len(PASS)} / FAIL {len(FAIL)}")
    for f in FAIL:
        print("  - " + f)
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
