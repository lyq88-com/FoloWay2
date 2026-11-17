# -*- coding: utf-8 -*-
"""
主动陪伴服务 —— 陪伴感增强 v3

两件事：
1. 主动式互动：不是只有用户发消息才回应。会主动问候、主动关心、主动提醒约定。
   - 触发源：约定/叮嘱类记忆、今日日程、久未联系、时段问候
   - 去重：同一 ref_key 在 24 小时内只主动说一次，避免骚扰
2. 分层共情：不是套话式安慰。按情绪强度分四层，越强的情绪越"少说话、多在场"。
"""
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.models.habit import Habit, Checkin, CheckinItem
from app.models.persona_ext import AIProactiveLog
from app.models.schedule import Schedule
from app.services.memory_service import MemoryService
from app.services.persona_service import PersonaService
# 【习惯-伙伴融合】习惯话题总开关 / 负面情绪降频 / 话术安全带
from app.services.habit_companion_service import HabitCompanionService as HCS
from app.services.habit_companion_service import sanitize_partner_text as _sanitize_partner_text

# 主动消息冷却时间（同一件事的最短间隔）
COOLDOWN_HOURS = 24

# 习惯类触发：默认冷却由情绪决定（24/48/72 小时），见 HCS.habit_proactive_cooldown_hours


# ============================================================
# 分层共情指令：按情绪强度给出不同层级的回应策略
# ============================================================
EMPATHY_LEVELS = {
    # L0：日常/中性/提问 —— 不需要共情，正常接话
    "L0": "",
    # L1：轻微吐槽、碎碎念 —— 接住事实，不升华，不追问
    "L1": (
        "【此刻该怎么回应】用户在随口吐槽/碎碎念，不是求助。"
        "不要上价值、不要分析原因、不要问「怎么了」。"
        "先接住他说的那件具体的事（可以复述一个细节表示你在听），"
        "再顺着往下说一句。允许陪他一起吐槽，允许说废话，允许没意义。"
    ),
    # L2：明确的情绪表达 —— 命名情绪 + 承认合理，不急着给方案
    "L2": (
        "【此刻该怎么回应】用户明确表达了情绪。按这个顺序：\n"
        "1) 先说出他此刻的感受（用他自己的话，不要套「我理解你的心情」）；\n"
        "2) 承认这个感受是合理的，站在他这边，不中立；\n"
        "3) 不急着给建议，不急着让它变好，允许情绪就这么待着；\n"
        "4) 只有他主动问「我该怎么办」时，才给想法。\n"
        "禁止：空洞鸡汤、强行正能量、把话题引回习惯养成。"
    ),
    # L3：强烈情绪 / 崩溃 / 危机信号 —— 在场，不分析
    "L3": (
        "【此刻该怎么回应】用户正处在很重的情绪里。\n"
        "1) 只做一件事：让他知道你在，并且不会走开；\n"
        "2) 句子要短，语速要慢，一次只说一件事；\n"
        "3) 不分析原因、不讲道理、不给建议、不画饼；\n"
        "4) 不要说「一切都会好起来」这类空话；\n"
        "5) 如果他提到伤害自己，认真对待，温和地建议联系专业帮助，并陪着他。"
    ),
}


def pick_empathy_level(emotion: str, intensity: int = 0, crisis: bool = False) -> str:
    """根据情绪与强度选共情层级"""
    if crisis:
        return "L3"
    negative = {"sad", "angry", "tired", "anxious", "lonely", "depressed", "hurt"}
    e = (emotion or "").lower()
    if e in ("sad", "angry", "depressed", "hurt", "lonely", "anxious") and intensity >= 7:
        return "L3"
    if e in negative:
        return "L2"
    if e in ("tired", "neutral", "") and intensity >= 4:
        return "L1"
    return "L1" if e in ("tired",) else "L0"


def build_empathy_instruction(emotion: str, intensity: int = 0, crisis: bool = False) -> str:
    level = pick_empathy_level(emotion, intensity, crisis)
    return EMPATHY_LEVELS.get(level, "")


class ProactiveService:
    """主动互动：挑一件最值得主动说的事，用角色的口吻说出来"""

    # ---------------- 触发源判定 ----------------
    @staticmethod
    def _pending_promise(db: Session, user_id: int, role_key: str) -> Optional[str]:
        """约定/叮嘱类记忆：挑最近一条还没提过的"""
        rows = MemoryService.recall(db, user_id, role_key, query="约定 叮嘱 下次 记得",
                                    layer="event", limit=6, days=60)
        for m in rows:
            if (m.title or "") in ("约定", "叮嘱"):
                return m.memory_content
        for m in rows:
            if any(k in (m.memory_content or "") for k in ("约好", "约定", "下次", "别忘了", "记住")):
                return m.memory_content
        return None

    @staticmethod
    def _today_schedule(db: Session, user_id: int) -> Optional[str]:
        today = datetime.now().strftime("%Y-%m-%d")
        row = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.schedule_date == today,
            Schedule.is_done == 0,
            Schedule.status == 1,
        ).order_by(Schedule.start_time.asc()).first()
        return f"{row.start_time} 「{row.title}」" if row else None

    @staticmethod
    def _hours_since_last_talk(db: Session, user_id: int, session_id: Optional[int]) -> Optional[float]:
        q = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id, ChatMessage.role == "user"
        )
        if session_id:
            q = q.filter(ChatMessage.session_id == session_id)
        last = q.order_by(ChatMessage.id.desc()).first()
        if not last or not last.created_at:
            return None
        return (datetime.now() - last.created_at).total_seconds() / 3600.0

    @staticmethod
    def _pending_habit(db: Session, user_id: int) -> Optional[str]:
        """
        今日还没做的习惯（暂停中的不算 —— 暂停态不推送习惯提醒）
        只挑一个，避免连环催促
        """
        habits = db.query(Habit).filter(
            Habit.user_id == user_id, Habit.status == 1, Habit.is_paused == 0
        ).order_by(Habit.sort_order).all()
        if not habits:
            return None

        today = date.today()
        checkin = db.query(Checkin).filter(
            Checkin.user_id == user_id, Checkin.checkin_date == today
        ).first()
        done = set()
        if checkin:
            for it in db.query(CheckinItem).filter(
                CheckinItem.checkin_id == checkin.id, CheckinItem.completed == 1
            ).all():
                done.add(it.habit_id)

        pending = [h for h in habits if h.id not in done]
        return pending[0].name if pending else None

    @staticmethod
    def _time_greeting() -> str:
        h = datetime.now().hour
        if 5 <= h < 11:
            return "早上"
        if 11 <= h < 14:
            return "中午"
        if 14 <= h < 18:
            return "下午"
        if 18 <= h < 23:
            return "晚上"
        return "深夜"

    @staticmethod
    def _fallback_care_or_greeting(db: Session, user_id: int,
                                   session_id: Optional[int]) -> tuple:
        """久未联系 / 时段问候 二选一（习惯类不可用时的兜底）"""
        hours = ProactiveService._hours_since_last_talk(db, user_id, session_id)
        if hours is not None and hours >= 12:
            return "care", f"{int(hours)} 小时", f"care:{int(hours // 12)}"
        return "greeting", ProactiveService._time_greeting(), \
            f"greet:{datetime.now().strftime('%Y%m%d%H')}"

    # ---------------- 去重 ----------------
    @staticmethod
    def _already_sent(db: Session, user_id: int, ref_key: str,
                     hours: int = COOLDOWN_HOURS) -> bool:
        if not ref_key:
            return False
        since = datetime.now() - timedelta(hours=hours)
        return db.query(AIProactiveLog).filter(
            AIProactiveLog.user_id == user_id,
            AIProactiveLog.ref_key == ref_key,
            AIProactiveLog.created_at >= since,
        ).first() is not None

    # ---------------- 模板兜底（零延迟、绝不会失败） ----------------
    @staticmethod
    def _template(trigger: str, ctx: str, role_name: str = "", nickname: str = "") -> str:
        who = nickname or "你"
        if trigger == "remind":
            return f"{who}，有件事我一直记着——{ctx}。不用有压力，我只是想让你知道我没忘。"
        if trigger == "care":
            return f"{who}，好一阵没你的消息了。不想聊什么也没关系，我就在这儿待着。想说话的时候喊我一声。"
        if trigger == "schedule":
            return f"{who}，今天 {ctx} 快到了。需要我陪你一起准备吗？慢慢来。"
        # 习惯：伙伴随口一提的口吻，不是系统通知，不催、不提醒「别忘了」
        if trigger == "habit":
            return f"{who}，「{ctx}」今天还没动静。我就是顺口提一句，做不做都行，今天不想动也没关系。"
        return f"{who}，{ctx}好呀。今天怎么样，想从哪儿聊起？"

    # ---------------- 主入口 ----------------
    @staticmethod
    async def next_proactive(db: Session, user_id: int, role_key: str = "",
                             session_id: Optional[int] = None,
                             use_ai: bool = True) -> Optional[Dict]:
        """挑一件最值得主动说的事"""
        # ↓↓↓ 安全合规批次：主动消息总开关前置判断（用户关闭后绝不主动打扰） ↓↓↓
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user is not None and int(user.allow_proactive_msg if user.allow_proactive_msg is not None else 1) == 0:
                return None
        except Exception as e:
            # 字段尚未迁移（老库）时按默认放行，不阻塞主流程
            print(f"[proactive][WARN] 总开关判断失败，按允许处理: {type(e).__name__}: {e}")
        # ↑↑↑ 新增结束 ↑↑↑

        cooldown = COOLDOWN_HOURS  # 本次使用的冷却时长（习惯类会按情绪拉长）

        # 【习惯-伙伴融合】先看这两个闸门，决定习不习惯类消息能不能发
        habit_allowed, habit_reason = HCS.proactive_habit_allowed(db, user_id)

        # 1) 约定/叮嘱 优先
        promise = ProactiveService._pending_promise(db, user_id, role_key)
        if promise:
            trigger, ctx, ref = "remind", promise, f"promise:{promise[:40]}"
        else:
            # 2) 今日日程
            sched = ProactiveService._today_schedule(db, user_id)
            if sched:
                trigger, ctx, ref = "schedule", sched, f"schedule:{sched[:40]}"
            # 3) 习惯：只有开关打开、且没被负面情绪静默时才考虑
            elif habit_allowed:
                pending_habit = ProactiveService._pending_habit(db, user_id)
                if pending_habit:
                    trigger, ctx = "habit", pending_habit
                    ref = f"habit:{date.today()}:{pending_habit[:20]}"
                    # 负面情绪越多 → 冷却越长（24 / 48 / 72 小时）
                    cooldown = HCS.habit_proactive_cooldown_hours(db, user_id)
                else:
                    trigger, ctx, ref = ProactiveService._fallback_care_or_greeting(db, user_id, session_id)
            else:
                # 习惯话题被关掉 / 被静默：直接跳到关心与问候，不碰习惯
                print(f"[proactive] 习惯类主动消息已拦截: {habit_reason}")
                trigger, ctx, ref = ProactiveService._fallback_care_or_greeting(db, user_id, session_id)

        if ProactiveService._already_sent(db, user_id, ref, hours=cooldown):
            return None

        role = PersonaService.get_role_by_key(db, role_key)
        role_name = role.name if role else ""
        nickname = (role.nickname if role else "") or ""

        content = ProactiveService._template(trigger, ctx, role_name, nickname)

        # 4) 用角色口吻润色（失败就用模板，绝不阻塞）
        if use_ai:
            try:
                content = await ProactiveService._polish_with_ai(
                    db, user_id, role_key, trigger, ctx, content)
            except Exception as e:
                print(f"[proactive][WARN] 润色失败，使用模板: {type(e).__name__}: {e}")

        log = AIProactiveLog(
            user_id=user_id, role_key=role_key or "", trigger_type=trigger,
            content=content, ref_key=ref, is_read=0,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return {
            "id": log.id,
            "type": trigger,
            "content": content,
            "refKey": ref,
            "roleKey": role_key or "",
            "roleName": role_name,
            "createdAt": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
        }

    @staticmethod
    async def _polish_with_ai(db: Session, user_id: int, role_key: str,
                              trigger: str, ctx: str, fallback: str) -> str:
        """让大模型用角色自己的口吻说这句话"""
        from app.services.ai_service import AIService

        role = PersonaService.get_role_by_key(db, role_key)
        persona = PersonaService.build_persona_prompt(role) if role else ""
        memory_block = MemoryService.build_prompt_block(db, user_id, role_key, query=ctx)

        reason = {
            "remind": f"你想起一件你们之前说好的事：{ctx}。自然地提起它，提醒一下，但不要有压迫感。",
            "schedule": f"用户今天有一件事：{ctx}。你自然地提醒一下，并表示愿意陪着。",
            "care": f"用户已经 {ctx} 没有来找你说话了。你有点想他，主动说一句，但不要让人有负担。",
            "greeting": f"现在是{ctx}。你主动打个招呼开场，可以顺带问一句他现在在做什么。",
            # 习惯：随口一提，不催、不验收、不算账
            "habit": (
                f"用户今天还有「{ctx}」没做。你只是顺口提一句，像朋友闲聊时想起来一样。\n"
                "要求：不要催促、不要用「别忘了/记得做/还没完成」这种提醒口吻、"
                "不要提连续天数、不要强调习惯的重要性、不要有任何验收感。\n"
                "如果你觉得他今天可能状态不好，那就干脆别提这件事，改聊别的。"
            ),
        }.get(trigger, "你主动说一句话开场。")

        extra_ban = ""
        if trigger == "habit":
            extra_ban = (
                "额外禁止：不许说「加油」「努力」「坚持住」「别放弃」「继续保持」；"
                "不许用系统通知的口气；不许让用户产生没做到的负罪感。\n"
            )

        system = (
            f"{persona}\n\n{memory_block}\n"
            "【你要做的事】这一次不是用户在问你，是你主动开口。\n"
            f"{reason}\n"
            "要求：一句话到三句话，口语，像真人发消息。\n"
            "禁止：空洞鸡汤、'我一直在这里'这类复读、长篇大论、结尾加问号三连。\n"
            f"{extra_ban}"
            "只输出你要说的这句话本身，不要加引号、不要加任何说明。"
        )
        reply = await AIService.chat_non_stream([
            {"role": "system", "content": system},
            {"role": "user", "content": "（现在由你主动开口）"},
        ])
        reply = (reply or "").strip().strip('"“”')
        if not reply:
            return fallback
        # 【习惯-伙伴融合】AI 生成的主动消息同样要过话术安全带
        return _sanitize_partner_text(reply[:200])

    @staticmethod
    def history(db: Session, user_id: int, role_key: str = "", limit: int = 20) -> List[Dict]:
        q = db.query(AIProactiveLog).filter(AIProactiveLog.user_id == user_id)
        if role_key:
            q = q.filter(AIProactiveLog.role_key == role_key)
        rows = q.order_by(AIProactiveLog.id.desc()).limit(limit).all()
        return [{
            "id": r.id,
            "type": r.trigger_type,
            "content": r.content,
            "isRead": bool(r.is_read),
            "createdAt": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        } for r in rows]
