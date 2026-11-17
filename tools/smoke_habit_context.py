# -*- coding: utf-8 -*-
"""
「打卡上下文延续 / 记忆串联整条习惯历程」冒烟测试

对照需求里的 6 条自测验收标准：
  1. 只打卡一次：AI 回复结合本次情绪 + 历史记忆，不是一句孤立鼓励
  2. 打卡之后继续在这条消息下面对话：AI 记得本次打卡事件
  3. 用户暂停习惯：后续回访是关怀，不是催恢复
  4. 总开关关闭：任何地方都不会主动冒出习惯相关内容
  5. 用户说不想聊：AI 立刻停止该习惯话题
  6. 不会出现「加油、坚持、你要努力、你失败了」这类说教话术

用法（在 liyeqing 目录下）:
    python -u tools/smoke_habit_context.py
"""
import os
import sys
import random
from datetime import datetime

SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server"))
# .env 是相对 cwd 读取的（db_password 写在 server/.env 里），
# 不切过去就会用默认口令 root 连库 → 1045 Access denied。
os.chdir(SERVER_DIR)
sys.path.insert(0, SERVER_DIR)

from app.core.database import get_db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.habit import Habit  # noqa: E402
from app.models.emotion import EmotionRecord  # noqa: E402
from app.schemas.habit import HabitCreate, CheckinRequest  # noqa: E402
from app.api.v1.habit import create_habit, checkin, pause_habit, resume_habit, mark_missed  # noqa: E402
from app.services.habit_companion_service import (  # noqa: E402
    HabitCompanionService as HCS, EVT_CHECKIN, EVT_MISSED, EVT_PAUSE, EVT_RESUME,
    contains_banned,
)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {detail}")


def no_banned(text):
    return not contains_banned(text or "")


def main():
    db = next(get_db())

    uname = "smoke_ctx_%04d" % random.randint(1000, 9999)
    now = datetime.now()
    # phone 上有 UNIQUE 索引，空串会被已存在的历史数据占用 → 必须给一个唯一号码，
    # 否则下一个冒烟脚本会撞 1062 Duplicate entry '' for key 'users.phone'。
    user = User(username=uname, nickname="上下文冒烟", password_hash="x",
                phone="139%08d" % random.randint(0, 99999999),
                register_time=now, last_login_time=now)
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    print(f"\n测试用户 id={uid} ({uname})\n")

    try:
        # ============ 1. 打卡 → 不是一句孤立鼓励 ============
        print("[1] 打卡一次：回复要结合本次情绪，不是孤立鼓励")
        r = create_habit(
            req=HabitCreate(name="睡前读书", target="每天读 20 页",
                            hope="想让自己睡前不看手机", habit_type="study"),
            user_id=uid, db=db)
        check("创建习惯成功", r.code == 200, r.message)
        hid = r.data["id"]

        r1 = checkin(req=CheckinRequest(habit_id=hid, emotion="tired", note="眼睛都快睁不开了"),
                     user_id=uid, db=db)
        check("打卡成功", r1.code == 200, r1.message)
        d1 = r1.data or {}
        reply = d1.get("companion_reply", "")
        check("打卡回复非空", bool(reply), reply[:40])
        check("回复结合本次情绪（疲惫→安抚）",
              any(w in reply for w in ("累", "疲惫", "辛苦", "撑", "歇")), reply[:40])
        check("回复不是孤立鼓励（不出现「太棒了/真厉害」这类空夸）",
              not any(w in reply for w in ("太棒了", "真厉害", "好厉害", "为你骄傲")))
        check("回复不含说教话术", no_banned(reply))

        # ============ 2. 打卡事件可被聊天页带走 ============
        print("\n[2] 打卡上下文载荷（前端挂在气泡上、回传给 /chat/send）")
        ctx = d1.get("chat_context") or {}
        check("返回 chat_context", bool(ctx))
        check("chat_context 带 habit_id", ctx.get("habit_id") == hid, str(ctx.get("habit_id")))
        check("chat_context 带习惯名", ctx.get("habit_name") == "睡前读书", str(ctx.get("habit_name")))
        check("chat_context 带事件类型", ctx.get("event") == EVT_CHECKIN, str(ctx.get("event")))
        check("chat_context 带本次情绪", ctx.get("emotion") == "tired", str(ctx.get("emotion")))
        check("chat_context 带情绪中文标签", ctx.get("emotion_label") == "疲惫", str(ctx.get("emotion_label")))
        check("chat_context 带打卡明细 id", int(ctx.get("item_id") or 0) > 0)
        check("chat_context 带基调", ctx.get("tone") == "done_tired", str(ctx.get("tone")))

        # ============ 3. 记忆串联：整条习惯历程 ============
        print("\n[3] 记忆调用规则：串联整条习惯历程，而不是零散单条")
        habit = db.query(Habit).filter(Habit.id == hid).first()
        block = HCS.build_habit_timeline_block(db, uid, habit)
        check("历程块包含习惯名", "睡前读书" in block)
        check("历程块包含起点时间", "从 20" in block or "开始" in block)
        check("历程块包含完成次数", "完成过" in block, block[:80].replace("\n", " "))
        check("历程块包含创建事件", "习惯开始" in block)
        check("历程块包含打卡事件", "习惯打卡" in block)
        check("历程块包含心情轨迹", "一路上的心情" in block)
        check("历程块带「怎么用这段历程」规则", "不要孤立看待单次打卡结果" in block)
        check("历程块禁止报数罗列", "禁止把上面的条目逐条复述" in block)

        # ============ 4. 打卡后继续对话：记得本次事件 ============
        print("\n[4] 打卡之后接着聊：AI 记得本次打卡事件")
        focus = HCS.build_habit_focus_block(db, uid, habit, event=EVT_CHECKIN, emotion="tired")
        check("focus 块包含整条历程", "完整历程" in focus)
        check("focus 块包含「刚刚发生的这一件事」", "刚刚发生的这一件事" in focus)
        check("focus 块带上本次情绪", "疲惫" in focus)
        check("focus 块带上本次基调", HCS.TONE_INSTRUCTION["done_tired"][:8] in focus)
        check("focus 块要求顺着这件事聊", "顺着它聊" in focus)

        # 再来几次打卡（不同情绪），心情轨迹应有多段
        for emo in ("happy", "anxious"):
            h2 = create_habit(
                req=HabitCreate(name=f"临时习惯_{emo}", target="x", habit_type="other"),
                user_id=uid, db=db)
            checkin(req=CheckinRequest(habit_id=h2.data["id"], emotion=emo), user_id=uid, db=db)
        block2 = HCS.build_habit_timeline_block(db, uid, habit)
        check("多段情绪后轨迹仍在（单条习惯隔离，不串其它习惯）",
              "睡前读书" in block2 and "临时习惯" not in block2)

        # ============ 5. 四大类基调互不相同 ============
        print("\n[5] 四大类场景的回复基调必须区分，禁止统一模板")
        t_happy = HCS.tone_of(EVT_CHECKIN, "happy")
        t_tired = HCS.tone_of(EVT_CHECKIN, "tired")
        t_missed = HCS.tone_of(EVT_MISSED, "sad")
        t_paused = HCS.tone_of(EVT_PAUSE, "")
        check("完成+开心 → done_happy", t_happy == "done_happy", t_happy)
        check("完成+疲惫 → done_tired", t_tired == "done_tired", t_tired)
        check("未完成+挫败 → missed_hurt", t_missed == "missed_hurt", t_missed)
        check("暂停 → paused", t_paused == "paused", t_paused)
        check("四种基调互不相同", len({t_happy, t_tired, t_missed, t_paused}) == 4)

        r_happy = HCS.build_event_reply(EVT_CHECKIN, habit, emotion="happy", seed="s1")
        r_tired = HCS.build_event_reply(EVT_CHECKIN, habit, emotion="tired", seed="s1")
        r_missed = HCS.build_event_reply(EVT_MISSED, habit, emotion="sad", seed="s1")
        r_pause = HCS.build_event_reply(EVT_PAUSE, habit, seed="s1")
        texts = [r_happy, r_tired, r_missed, r_pause]
        check("四类文案两两不同", len(set(texts)) == 4, " / ".join(t[:12] for t in texts))
        check("四类文案都不含说教话术", all(no_banned(t) for t in texts))

        # ============ 6. 未完成是接纳，不是催补卡 ============
        print("\n[6] 未完成 + 挫败：接纳共情、商量调整，绝不催补卡")
        check("未完成文案给出口（调低目标/先暂停）",
              any(w in r_missed for w in ("改小一点", "调轻一点", "重新商量", "先放一放")))
        check("未完成文案不催补卡",
              not any(w in r_missed for w in ("赶紧", "快点补", "补上就行", "别落下")))
        check("未完成文案不指责", not any(w in r_missed for w in ("你怎么", "又没做到", "失败")))
        r_missed_empty = HCS.build_event_reply(EVT_MISSED, habit, emotion="", seed="s2")
        check("未完成（无负面情绪）不强行加商量句", len(r_missed_empty) < len(r_missed))

        # ============ 7. 暂停是关怀，不是催恢复 ============
        print("\n[7] 暂停习惯：认可自我照顾，不催恢复")
        check("暂停文案认可自我照顾",
              any(w in r_pause for w in ("照顾自己", "放一放", "停下", "休息", "歇")))
        check("暂停文案不催恢复",
              not any(w in r_pause for w in ("赶紧恢复", "早点回来", "继续打卡", "补回来")))
        pr = pause_habit(habit_id=hid, data={"reason": "最近太累了"}, user_id=uid, db=db)
        check("暂停接口返回 chat_context", bool((pr.data or {}).get("chat_context")))
        check("暂停 chat_context 事件是 habit_pause",
              (pr.data or {}).get("chat_context", {}).get("event") == EVT_PAUSE)
        check("暂停回复不含说教话术", no_banned((pr.data or {}).get("companion_reply", "")))

        rr = resume_habit(habit_id=hid, data={}, user_id=uid, db=db)
        check("重启接口返回 chat_context",
              (rr.data or {}).get("chat_context", {}).get("event") == EVT_RESUME)
        mr = mark_missed(habit_id=hid, data={"emotion": "sad"}, user_id=uid, db=db)
        check("未完成接口返回 chat_context",
              (mr.data or {}).get("chat_context", {}).get("event") == EVT_MISSED)

        # ============ 8. 退出话题：立刻停止 + 短期静默 ============
        print("\n[8] 用户说不想聊：立刻停止该习惯话题，并短期静默")
        check("识别「先不说这个了」", HCS.detect_exit_habit_topic("先不说这个了"))
        check("识别「不想聊这个」", HCS.detect_exit_habit_topic("算了不想聊这个"))
        check("识别「聊点别的」", HCS.detect_exit_habit_topic("我们聊点别的吧"))
        check("识别「别再提这个」", HCS.detect_exit_habit_topic("别再提这个了"))
        check("普通句子不误判", not HCS.detect_exit_habit_topic("今天工作好累"))
        check("提到「放一放」的表达命中", HCS.detect_exit_habit_topic("这个先放一放吧"))
        check("退出固定回应存在", HCS.EXIT_REPLY == "好，那我们先不说这个啦。", HCS.EXIT_REPLY)

        check("静默前未被静默", not HCS.is_habit_muted(db, uid, hid))
        HCS.mute_habit_topic(db, uid, hid)
        check("静默后 is_habit_muted=True", HCS.is_habit_muted(db, uid, hid))
        check("静默天数默认 3 天", HCS.HABIT_MUTE_DAYS == 3)
        HCS.clear_habit_mute(db, uid, hid)
        check("解除静默后恢复", not HCS.is_habit_muted(db, uid, hid))
        # 过期静默自动失效
        HCS.mute_habit_topic(db, uid, hid, days=0)
        check("0 天静默视为未静默（已过期）", not HCS.is_habit_muted(db, uid, hid))

        # ============ 9. 总开关关闭 ============
        print("\n[9] 总开关关闭：习惯话题全部禁用")
        check("默认允许聊习惯", HCS.habit_topic_allowed(db, uid))
        HCS.set_allow_habit_topic(db, uid, False)
        check("关闭后 habit_topic_allowed=False", not HCS.habit_topic_allowed(db, uid))
        ok, reason = HCS.proactive_habit_allowed(db, uid)
        check("关闭后主动消息被拦截", (not ok) and reason == "topic_switch_off", reason)
        HCS.set_allow_habit_topic(db, uid, True)
        ok2, reason2 = HCS.proactive_habit_allowed(db, uid)
        check("重新打开后恢复", ok2 and reason2 == "ok", reason2)

        # ============ 10. 取不到的习惯要安全降级 ============
        print("\n[10] 边界：取不到 / 别人的习惯 → 降级为普通闲聊")
        check("不存在的习惯 → None", HCS.resolve_focus_habit(db, uid, 99999999) is None)
        check("habit_id=0 → None", HCS.resolve_focus_habit(db, uid, 0) is None)
        check("自己的习惯 → 可取", HCS.resolve_focus_habit(db, uid, hid) is not None)

        # 清理本用户产生的情绪记录，避免影响其它冒烟的降频判定
        db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).delete()
        db.commit()

    finally:
        # 清干净，别给后面的冒烟脚本留脏数据（尤其 users.phone 的唯一索引）
        try:
            db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).delete()
            db.query(Habit).filter(Habit.user_id == uid).delete()
            db.query(User).filter(User.id == uid).delete()
            db.commit()
        except Exception as e:
            print(f"[cleanup][WARN] {type(e).__name__}: {e}")
            db.rollback()
        print(f"\n结果：PASS {len(PASS)} / FAIL {len(FAIL)}")
        if FAIL:
            print("失败项：")
            for f in FAIL:
                print("  - " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
