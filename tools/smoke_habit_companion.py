# -*- coding: utf-8 -*-
"""
习惯-伙伴融合 冒烟测试

覆盖：创建 → 打卡(情绪差异化) → 未完成 → 暂停 → 重启 → 记忆 → 总开关
      → 负面情绪降频 → 危机自我否定 → 陪伴向复盘 → 话术红线

用法（在 liyeqing/server 目录下）:
    python -u ../tools/smoke_habit_companion.py
"""
import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from app.core.database import get_db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.habit import Habit  # noqa: E402
from app.models.achievement import UserBadge, Badge  # noqa: E402
from app.models.habit_companion import UserCompanionSetting  # noqa: E402
from app.models.emotion import EmotionRecord  # noqa: E402
from app.schemas.habit import HabitCreate, CheckinRequest  # noqa: E402
from app.api.v1.habit import (  # noqa: E402
    create_habit, checkin, pause_habit, resume_habit, mark_missed, habit_story,
    get_encouragement, verbal_parse, verbal_confirm,
)
from app.services.habit_companion_service import (  # noqa: E402
    HabitCompanionService as HCS, EVT_CHECKIN, EVT_PAUSE, EVT_RESUME, EVT_MISSED, EVT_CREATE,
    contains_banned,
)
from app.services.proactive_service import ProactiveService  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {detail}")


def no_banned(text):
    """话术红线：不得出现加油/努力/坚持住/别放弃等"""
    return not contains_banned(text or "")


def main():
    db = next(get_db())

    # ---------- 准备一个隔离的测试用户 ----------
    uname = "smoke_habit_%04d" % random.randint(1000, 9999)
    now = datetime.now()
    user = User(username=uname, nickname="冒烟", password_hash="x", phone="",
                register_time=now, last_login_time=now)
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    print(f"\n测试用户 id={uid} ({uname})\n")

    try:
        # ============ 1. 创建习惯 → 写记忆 ============
        print("[1] 创建习惯")
        r = create_habit(
            req=HabitCreate(name="晚饭后散步", target="每天走 20 分钟",
                            hope="想让自己晚上不那么焦虑", habit_type="sport"),
            user_id=uid, db=db)
        check("创建习惯成功", r.code == 200, r.message)
        hid = r.data["id"]
        check("创建后返回伙伴口吻回复", bool(r.data.get("companion_reply")))
        check("创建回复不含禁用话术", no_banned(r.data.get("companion_reply", "")))

        mems = HCS.list_habit_memories(db, uid, habit_id=hid)
        check("创建写入事件记忆", any((m.context_data or {}).get("event") == EVT_CREATE for m in mems))
        check("记忆带 habit_id", all(m.habit_id == hid for m in mems))
        check("记忆 memory_type=habit", all(m.memory_type == "habit" for m in mems))
        check("记忆含目标与期待感受",
              any(("散步" in (m.memory_content or "")) and ("焦虑" in (m.memory_content or "")) for m in mems))

        # ============ 2. 打卡 + 情绪差异化 ============
        print("\n[2] 打卡与情绪差异化")
        r1 = checkin(req=CheckinRequest(habit_id=hid, emotion="tired", note="今天很累但还是走了"),
                     user_id=uid, db=db)
        check("打卡成功", r1.code == 200, r1.message)
        d1 = r1.data or {}
        check("打卡后带出情绪", d1.get("emotion") == "tired", str(d1.get("emotion")))
        check("打卡返回伙伴反馈", bool(d1.get("companion_reply")))
        check("打卡反馈不含禁用话术", no_banned(d1.get("companion_reply", "")))

        # 换一种情绪，文案必须不同
        hid2 = create_habit(req=HabitCreate(name="睡前阅读", target="读 10 页",
                                             hope="想睡得安稳一点"),
                            user_id=uid, db=db).data["id"]
        r2 = checkin(req=CheckinRequest(habit_id=hid2, emotion="happy"), user_id=uid, db=db)
        txt_tired = d1.get("companion_reply", "")
        txt_happy = (r2.data or {}).get("companion_reply", "")
        check("不同情绪给出不同文案", txt_tired != txt_happy,
              f"tired={txt_tired[:18]!r} / happy={txt_happy[:18]!r}")

        # 同一种情绪两次生成应稳定（同一天不跳变）
        a = HCS.build_checkin_encouragement(db.query(Habit).get(hid), emotion="tired", continuous_day=1)
        b = HCS.build_checkin_encouragement(db.query(Habit).get(hid), emotion="tired", continuous_day=1)
        check("同参数文案稳定", a == b)

        mems = HCS.list_habit_memories(db, uid, habit_id=hid)
        check("打卡写入事件记忆", any((m.context_data or {}).get("event") == EVT_CHECKIN for m in mems))
        check("打卡记忆记录了情绪", any("疲惫" in (m.memory_content or "") for m in mems))

        # ============ 3. 未完成 ============
        print("\n[3] 未完成")
        r3 = mark_missed(habit_id=hid, data={"emotion": "sad"}, user_id=uid, db=db)
        check("上报未完成成功", r3.code == 200, r3.message)
        check("未完成文案不含说教", no_banned(r3.data.get("companion_reply", "")))
        check("未完成不落 is_paused", db.query(Habit).get(hid).is_paused == 0)
        mems = HCS.list_habit_memories(db, uid, habit_id=hid)
        check("未完成写入事件记忆", any((m.context_data or {}).get("event") == EVT_MISSED for m in mems))

        # ============ 4. 暂停 ============
        print("\n[4] 暂停")
        r4 = pause_habit(habit_id=hid, data={"reason": "最近太累了"}, user_id=uid, db=db)
        check("暂停成功", r4.code == 200 and r4.data.get("changed"), r4.message)
        h = db.query(Habit).get(hid)
        check("is_paused 置为 1", h.is_paused == 1)
        check("paused_at 已记录", h.paused_at is not None)
        check("暂停原因已保存", h.paused_reason == "最近太累了")
        check("暂停文案不含说教", no_banned(r4.data.get("companion_reply", "")))

        mems = HCS.list_habit_memories(db, uid, habit_id=hid)
        check("暂停写入事件记忆", any((m.context_data or {}).get("event") == EVT_PAUSE for m in mems))
        check("暂停记忆标记非失败",
              any("不是半途而废" in (m.memory_content or "") for m in mems))

        got = db.query(UserBadge).join(Badge, UserBadge.badge_id == Badge.id).filter(
            UserBadge.user_id == uid, Badge.code == "self_acceptance").first()
        check("暂停授予自我接纳徽章", got is not None)

        # 暂停态：打卡应被拒绝
        r5 = checkin(req=CheckinRequest(habit_id=hid), user_id=uid, db=db)
        check("暂停中的习惯不可打卡", r5.code == 409, f"code={r5.code}")

        # 暂停态：不出现在今日待办
        from app.api.v1.habit import get_habits
        lst = get_habits(user_id=uid, db=db).data
        check("暂停的习惯不进今日待办", all(x["id"] != hid for x in lst))
        lst_all = get_habits(user_id=uid, db=db, include_paused=1).data
        check("include_paused=1 时可查到", any(x["id"] == hid for x in lst_all))

        # 暂停态：主动消息不再推这个习惯
        pending = ProactiveService._pending_habit(db, uid)
        check("主动提醒跳过暂停习惯", pending != "晚饭后散步", str(pending))

        # ============ 5. 重启 ============
        print("\n[5] 重启")
        r6 = resume_habit(habit_id=hid, data={}, user_id=uid, db=db)
        check("重启成功", r6.code == 200 and r6.data.get("changed"), r6.message)
        h = db.query(Habit).get(hid)
        check("is_paused 归零", h.is_paused == 0)
        check("resume_count = 1", h.resume_count == 1, str(h.resume_count))
        check("重启文案不含说教", no_banned(r6.data.get("companion_reply", "")))
        mems = HCS.list_habit_memories(db, uid, habit_id=hid)
        check("重启写入事件记忆", any((m.context_data or {}).get("event") == EVT_RESUME for m in mems))
        got = db.query(UserBadge).join(Badge, UserBadge.badge_id == Badge.id).filter(
            UserBadge.user_id == uid, Badge.code == "habit_restart").first()
        check("重启授予重启徽章", got is not None)

        # 重启后能正常打卡，且文案带出「重新拾起」的回忆
        # （hid 今天已经打过卡，这里用一个新习惯完整走一遍 暂停→重启→打卡）
        hid3 = create_habit(req=HabitCreate(name="早起喝水", target="一杯温水",
                                            hope="想让自己慢一点开始这一天"),
                            user_id=uid, db=db).data["id"]
        pause_habit(habit_id=hid3, data={"reason": "感冒了先歇两天"}, user_id=uid, db=db)
        resume_habit(habit_id=hid3, data={}, user_id=uid, db=db)
        r7 = checkin(req=CheckinRequest(habit_id=hid3, emotion="calm"), user_id=uid, db=db)
        check("重启后可打卡", r7.code == 200, r7.message)
        # RESUME_ECHO 三条变体分别用「之前/重新/断过」回溯，关键词要覆盖全
        txt7 = (r7.data or {}).get("companion_reply", "")
        check("重启后反馈提及过往",
              any(k in txt7 for k in ("重新", "之前", "停过", "断过", "捡起来", "拿起来")),
              txt7[:40])

        # ============ 6. 总开关 ============
        print("\n[6] 习惯话题总开关")
        check("默认允许聊习惯", HCS.habit_topic_allowed(db, uid) is True)
        HCS.set_allow_habit_topic(db, uid, False)
        check("关闭后 habit_topic_allowed=False", HCS.habit_topic_allowed(db, uid) is False)
        allowed, reason = HCS.proactive_habit_allowed(db, uid)
        check("关闭后习惯类主动消息被拦截", (not allowed) and reason == "topic_switch_off", reason)
        HCS.set_allow_habit_topic(db, uid, True)
        check("重新开启后恢复", HCS.proactive_habit_allowed(db, uid)[0] is True)

        # 负面情绪静默
        HCS.mute_habit_proactive(db, uid, 48)
        allowed, reason = HCS.proactive_habit_allowed(db, uid)
        check("静默期内拦截", (not allowed) and reason == "muted_by_negative_emotion", reason)
        db.query(UserCompanionSetting).filter(
            UserCompanionSetting.user_id == uid).update({"habit_proactive_muted_until": None})
        db.commit()

        # ============ 7. 负面情绪降频 ============
        print("\n[7] 负面情绪降频")
        # 前面的打卡会把情绪落进 emotion_records（这是预期行为），
        # 这里先清空，才能验证「完全没有情绪数据」时的默认冷却
        db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).delete()
        db.commit()
        base = HCS.habit_proactive_cooldown_hours(db, uid)
        check("无情绪数据时冷却=24h", base == 24, str(base))
        from datetime import date, timedelta
        for i in range(6):
            db.add(EmotionRecord(user_id=uid, emotion="sad", intensity=7,
                                 record_date=date.today() - timedelta(days=i)))
        for i in range(2):
            db.add(EmotionRecord(user_id=uid, emotion="calm", intensity=5,
                                 record_date=date.today() - timedelta(days=i)))
        db.commit()
        ratio, n = HCS.recent_negative_ratio(db, uid, days=7)
        cd = HCS.habit_proactive_cooldown_hours(db, uid)
        check("负面占比计算正确", ratio > 0.5, f"ratio={ratio} n={n}")
        check("负面情绪多时冷却拉长", cd >= 72, f"cooldown={cd}h")
        # 正面情绪为主 → 回到 24h
        db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).update({"emotion": "happy"})
        db.commit()
        check("正面情绪为主时回到 24h", HCS.habit_proactive_cooldown_hours(db, uid) == 24)

        # ============ 8. 危机：自我否定 ============
        print("\n[8] 自我否定联动")
        check("识别「坚持不下来」", HCS.detect_self_blame("我真的是坚持不下来"))
        check("识别「我没用」", HCS.detect_self_blame("我觉得我没用，什么都做不好"))
        check("正常句子不误伤", not HCS.detect_self_blame("今天天气不错，我去散步了"))
        relief = HCS.build_habit_relief_plan(db, uid)
        check("给出接纳语", bool(relief["acknowledge"]))
        check("接纳语不含说教", no_banned(relief["acknowledge"]))
        check("给出暂停选项", len(relief["options"]) >= 1, str(len(relief["options"])))
        check("选项动作是 pause", all(o["action"] == "pause" for o in relief["options"]))
        check("明确禁止劝硬坚持", "咬牙坚持" in relief["forbidden"])

        # ============ 9. 鼓励语接口 ============
        print("\n[9] /habit/encouragement")
        e1 = get_encouragement(data={"habit_id": hid, "action": "checkin", "emotion": "sad"},
                               user_id=uid, db=db)
        e2 = get_encouragement(data={"habit_id": hid, "action": "checkin", "emotion": "happy"},
                               user_id=uid, db=db)
        check("接口返回 200", e1.code == 200 and e2.code == 200)
        check("不同情绪返回不同话", e1.data["message"] != e2.data["message"])
        check("不再是「太棒了…继续保持」", "太棒了" not in e1.data["message"])
        check("鼓励语无禁用话术", no_banned(e1.data["message"]) and no_banned(e2.data["message"]))
        e3 = get_encouragement(data={"habit_id": hid, "action": "missed"}, user_id=uid, db=db)
        check("未完成话术无禁用词", no_banned(e3.data["message"]))

        # ============ 10. 语义打卡 ============
        print("\n[10] 口头打卡")
        hid4 = create_habit(req=HabitCreate(name="写三行日记", target="写三行就好",
                                            hope="想把脑子里的东西倒出来"),
                            user_id=uid, db=db).data["id"]
        vp = verbal_parse(data={"text": "今天我把写三行日记做完了"}, user_id=uid, db=db)
        check("识别出是口头打卡", vp.data["is_checkin"] is True)
        check("匹配到对应习惯", any(c["habit_id"] == hid4 for c in vp.data["candidates"]),
              str(vp.data["candidates"]))
        check("先询问而不是直接打卡",
              "吗" in vp.data["confirm_question"] or "哪一个" in vp.data["confirm_question"])
        vp2 = verbal_parse(data={"text": "今天天气真好"}, user_id=uid, db=db)
        check("普通闲聊不被误判", vp2.data["is_checkin"] is False)
        vc = verbal_confirm(data={"habit_id": hid4, "confirmed": True, "emotion": "calm"},
                            user_id=uid, db=db)
        check("确认后完成打卡", vc.data.get("checked") is True, str(vc.data.get("message")))
        check("口头打卡也写记忆",
              any((m.context_data or {}).get("event") == EVT_CHECKIN
                  for m in HCS.list_habit_memories(db, uid, habit_id=hid4)))
        vc2 = verbal_confirm(data={"habit_id": hid4, "confirmed": False}, user_id=uid, db=db)
        check("未确认则不打卡", vc2.data.get("checked") is False)

        # ============ 11. 习惯完整过往 ============
        print("\n[11] 习惯完整过往（不失忆）")
        st = habit_story(habit_id=hid, user_id=uid, db=db)
        check("story 接口 200", st.code == 200)
        s = st.data
        check("含开启时间", bool(s["created_at"]), s["created_at"])
        check("含重启次数", s["resume_count"] == 1, str(s["resume_count"]))
        check("含中断次数", s["missed_count"] >= 1, str(s["missed_count"]))
        check("含时间线", len(s["timeline"]) >= 4, str(len(s["timeline"])))
        check("brief 不打分成绩", "完成率" not in s["brief"], s["brief"])

        # ============ 12. 陪伴向复盘 ============
        print("\n[12] 陪伴向复盘")
        rev = HCS.build_companion_review(db, uid, days=30)
        check("复盘有文本", bool(rev["review"]))
        check("复盘不含完成率", "完成率" not in rev["review"])
        check("复盘不含打分", "评分" not in rev["review"] and "得分" not in rev["review"])
        check("复盘不含排名", "排名" not in rev["review"])
        check("复盘无禁用话术", no_banned(rev["review"]))
        mon = HCS.build_monthly_companion_review(db, uid)
        check("月度复盘有故事", bool(mon["story"]))
        check("月度复盘不含排名打分",
              all(k not in mon["story"] for k in ("排名", "评分", "得分", "完成率")))

        # ============ 13. 记忆过滤 ============
        print("\n[13] 记忆过滤")
        allm = HCS.list_habit_memories(db, uid, limit=100)
        only_pause = HCS.list_habit_memories(db, uid, event=EVT_PAUSE, limit=100)
        check("能筛出习惯记忆", len(allm) >= 5, str(len(allm)))
        check("能按事件细分", len(only_pause) >= 1 and len(only_pause) < len(allm),
              f"pause={len(only_pause)} all={len(allm)}")
        only_one = HCS.list_habit_memories(db, uid, habit_id=hid2, limit=100)
        check("能按习惯细分", all(m.habit_id == hid2 for m in only_one))

        # ============ 14. world 剧情碎片 ============
        print("\n[14] world 剧情碎片")
        frag = HCS.build_world_fragment(db, uid, hid)
        check("产出碎片素材", frag is not None)
        check("碎片提到重启经历", frag and ("重新走通" in frag["content"] or "断过" in frag["content"]),
              (frag or {}).get("content", ""))
        check("碎片无禁用话术", no_banned((frag or {}).get("content", "")))

    finally:
        # ---------- 清理测试数据 ----------
        print("\n[cleanup] 清理测试数据")
        db.query(UserBadge).filter(UserBadge.user_id == uid).delete()
        from app.models.chat import AIUserMemory
        db.query(AIUserMemory).filter(AIUserMemory.user_id == uid).delete()
        db.query(UserCompanionSetting).filter(UserCompanionSetting.user_id == uid).delete()
        db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).delete()
        from app.models.habit import Checkin, CheckinItem
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
    if FAIL:
        for f in FAIL:
            print("  - " + f)
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
