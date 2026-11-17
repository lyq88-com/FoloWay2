# -*- coding: utf-8 -*-
"""
习惯-伙伴融合服务 —— 让 AI 完整感知习惯的生命周期

设计原则（贯穿全文件，任何改动都不要违背）：
1. 伙伴不是监督员。习惯只是共同生活的一部分，共情永远排在习惯之前。
2. 生命周期完整可追溯：创建 → 打卡 → 未完成 → 暂停 → 重启，每个节点都留下记忆，
   事件记忆一律复用 ai_user_memories（不新建表），通过 memory_type='habit'
   + context_data.topic='habit' + habit_id 三重标记，支持过滤。
3. 拒绝说教与 PUA 式打气：所有对外文案必须过 sanitize_partner_text()，
   「加油 / 努力 / 坚持住 / 别放弃」这类词一律被软化或剔除。
4. 用户拥有最终解释权：allow_habit_topic 关闭后，任何习惯类主动消息一律不发。

零副作用约定：
- 本模块只被「显式调用」触发，不自动改写任何既有业务返回值；
- 所有外部调用点都用 try/except 包裹，本模块异常不得影响打卡/创建等主流程。
"""
import json
import random
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.habit import Habit, Checkin, CheckinItem
from app.models.chat import AIUserMemory
from app.models.emotion import EmotionRecord
from app.models.achievement import Badge, UserBadge
from app.models.habit_companion import UserCompanionSetting
from app.services.memory_service import MemoryService, LAYER_EVENT

# ============================================================
# 一、常量
# ============================================================

# 习惯生命周期事件
EVT_CREATE = "habit_create"    # 创建习惯
EVT_CHECKIN = "habit_checkin"  # 打卡成功
EVT_MISSED = "habit_missed"    # 未完成
EVT_PAUSE = "habit_pause"      # 暂停
EVT_RESUME = "habit_resume"    # 重启

EVENT_TITLES = {
    EVT_CREATE: "习惯开始",
    EVT_CHECKIN: "习惯打卡",
    EVT_MISSED: "习惯中断",
    EVT_PAUSE: "习惯暂停",
    EVT_RESUME: "习惯重启",
}

# 事件重要度：暂停与重启是人生态势的转折，权重更高
EVENT_SALIENCE = {
    EVT_CREATE: 6,
    EVT_CHECKIN: 4,
    EVT_MISSED: 5,
    EVT_PAUSE: 8,
    EVT_RESUME: 8,
}

# 记忆类型 / 主题标记（用于过滤）
MEMORY_TYPE_HABIT = "habit"
TOPIC_HABIT = "habit"

# 负面情绪集合（与 emotion_records.emotion 取值对齐）
NEGATIVE_EMOTIONS = {"sad", "angry", "tired", "anxious", "depressed", "lonely"}

EMOTION_LABELS = {
    "happy": "开心", "excited": "有干劲", "calm": "平静",
    "sad": "低落", "angry": "烦躁", "tired": "疲惫",
    "anxious": "不安", "depressed": "消沉", "lonely": "孤单",
    "neutral": "没什么特别", "": "没提到",
}

# 徽章代码（P1-3）
BADGE_RESTART = "habit_restart"        # 🔄 重启徽章
BADGE_SELF_ACCEPT = "self_acceptance"  # 🫂 自我接纳徽章


# ============================================================
# 二、话术安全带：禁止说教、禁止 PUA 式打气
# ============================================================

# 命中即软化的词（顺序敏感：长词在前）
SOFTEN_MAP = [
    ("咬牙坚持", "不用硬撑"),
    ("坚持就是胜利", "按你自己的节奏来"),
    ("坚持住", "不用勉强"),
    ("再接再厉", "照你的节奏来就好"),
    ("继续加油", "慢慢来就好"),
    ("加油努力", "按现在的节奏来"),
    ("加油", "慢慢来"),
    ("要努力", "尽力就好"),
    ("努力", "尽力"),
    ("你可以的", "我在这儿"),
    ("你能行的", "我在这儿"),
    ("相信自己", "我信你"),
    ("别放弃", "不用勉强"),
    ("不要放弃", "不用勉强"),
    ("不要半途而废", "想停就停"),
    ("半途而废", "先放一放"),
    ("前功尽弃", "之前的不算白费"),
    ("你不能放弃", "你可以先歇一歇"),
    ("一定要坚持", "看你自己的状态"),
    ("你必须", "你可以"),
    ("别人都能做到", "每个人节奏不一样"),
]

# 纯检测用（出现即视为不合格，供测试与兜底判断）
BANNED_WORDS = ["加油", "努力", "坚持住", "别放弃", "不要放弃",
                "半途而废", "前功尽弃", "再接再厉"]


def sanitize_partner_text(text: str) -> str:
    """
    话术安全带：把说教 / PUA 式打气替换成伙伴口吻。
    所有对外输出的文案（含 AI 生成）都应过一遍。
    """
    if not text:
        return text
    out = text
    for old, new in SOFTEN_MAP:
        if old in out:
            out = out.replace(old, new)
    return out


def contains_banned(text: str) -> bool:
    """是否含有被禁的话术（测试与兜底用）"""
    if not text:
        return False
    return any(w in text for w in BANNED_WORDS)


def _pick(pool: List[str], seed: str) -> str:
    """按种子稳定选取，避免同一天刷新出不同的话"""
    return random.Random(seed).choice(pool)


# ============================================================
# 三、文案池：按情绪差异化，绝不统一话术
# ============================================================

CHECKIN_BY_EMOTION = {
    "happy": [
        "今天看得出来你是带着劲做完的，连我都被你感染了一点。",
        "心情好又把它做完了，这种日子挺值得记住的。",
        "你今天整个人的状态是松的，做起来应该没那么费劲吧。",
    ],
    "excited": [
        "你今天这股冲劲挺足的，做完是不是还想再干点什么？",
        "带劲儿的一天，这件事也顺帶被你拿下了。",
        "看你今天的样子，我都不用多说什么了。",
    ],
    "calm": [
        "平平淡淡地做完了，这种不费力的感觉其实挺难得的。",
        "你今天做这件事的时候应该挺静的，那就对了。",
        "没什么波澜的一天，但它确实被你完成了。",
    ],
    "sad": [
        "今天你心里压着事，还腾出手把这个做完了。不用给它附加意义，先歇一会儿吧。",
        "本来就不太好过的一天，你还是做到了。剩下的时候别再要求自己了。",
        "做完了。今天辛苦的地方不在这一步，而在你还得撑着过完这一天。",
    ],
    "angry": [
        "带着这股火气还是把它处理了。不想说话就先不说话，我在这儿。",
        "今天心里堵得慌，你还是把手边这事做完了。先喘口气吧。",
        "烦躁的时候做事最耗人。做完了就放下，别再给自己加东西。",
    ],
    "tired": [
        "累成这样你还把它做完了，说明你今天真的在撑着。做完就放下吧。",
        "今天大概已经很疲惫了，能完成就已经够了，剩下的时间留给你自己。",
        "疲惫的时候完成的这一步，分量比平时重。别急着再安排别的。",
    ],
    "anxious": [
        "心里乱着的时候还能做完，挺不容易的。要不要先跟我说两句？",
        "你今天一直悬着心，还是把它落了地。先让自己缓一缓。",
        "不安的时候做事最磨人。做完了就好，不用再想下一步。",
    ],
    "depressed": [
        "今天你能做到这一步，已经比你说的「什么都没做」要多得多了。",
        "你还是做了。我不打算夸你，就想让你知道：我看见了。",
        "这种时候还能把手边的事做完，本身就很重了。剩下的交给我陪着。",
    ],
    "neutral": [
        "完成了。今天没什么特别的，这样也挺好。",
        "又一天。不惊不喜，但你确实做了。",
        "今天这一步走得很平。平也是一种结果。",
    ],
}

# 有中断/重启史时追加的一句（回忆感，不比较、不打分）
RESUME_ECHO = [
    "这个习惯你之前停过一阵，现在又捡起来了。中间那段不用解释，你回来就够了。",
    "你重新拾起它了。这次不用跟上次比，按现在的节奏来就行。",
    "它又被你拿起来了。我记得中间断过，那也没什么，现在还在继续就好。",
]

# 连续天数很长时的一句（克制，不吹捧）
LONG_STREAK_ECHO = [
    "不知不觉已经这么久了。",
    "回头看，这段时间挺长的。",
    "一天天的，居然攒到了现在。",
]

MISSED_TEXT = [
    "今天没做成。没什么，日子本来就不总是一样的。",
    "今天先这样吧，不用补，也不用跟谁解释。",
    "没做到就没做到。明天的事明天再说。",
]

PAUSE_TEXT = [
    "好，那我们先把它放一放。这不是放弃，是你在照顾自己。",
    "先停下来吧。想再拿起来的时候随时叫我，它不会跑。",
    "我记住了，这个习惯先休息一阵。你也是。",
]

RESUME_TEXT = [
    "你又把它捡起来了。这次我们不设目标，先试试看。",
    "好，重新开始。跟上次无关，就从现在算起。",
    "欢迎它回来。我也欢迎你回来。",
]

CREATE_TEXT = [
    "你开始了一个新习惯。我记下了，往后它就也有我们的一份了。",
    "好，那我们从今天开始有这件小事了。不用想太远。",
]


# ============================================================
# 四、服务主体
# ============================================================

class HabitCompanionService:
    """习惯-伙伴融合：记忆 / 开关 / 情绪 / 文案 / 复盘"""

    # ---------------- 4.1 用户开关 ----------------
    @staticmethod
    def get_setting(db: Session, user_id: int) -> UserCompanionSetting:
        """惰性创建，默认允许聊习惯"""
        row = db.query(UserCompanionSetting).filter(
            UserCompanionSetting.user_id == user_id
        ).first()
        if not row:
            row = UserCompanionSetting(user_id=user_id, allow_habit_topic=1)
            db.add(row)
            db.commit()
            db.refresh(row)
        return row

    @staticmethod
    def habit_topic_allowed(db: Session, user_id: int) -> bool:
        """【允许伙伴和我聊习惯相关的事】总开关"""
        row = db.query(UserCompanionSetting).filter(
            UserCompanionSetting.user_id == user_id
        ).first()
        if not row:
            return True  # 未设置 = 默认允许
        return bool(row.allow_habit_topic)

    @staticmethod
    def set_allow_habit_topic(db: Session, user_id: int, allowed: bool) -> UserCompanionSetting:
        row = HabitCompanionService.get_setting(db, user_id)
        row.allow_habit_topic = 1 if allowed else 0
        row.habit_topic_off_at = None if allowed else datetime.now()
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def mute_habit_proactive(db: Session, user_id: int, hours: int) -> None:
        """负面情绪较多时，把习惯类主动消息静默一段时间"""
        row = HabitCompanionService.get_setting(db, user_id)
        row.habit_proactive_muted_until = datetime.now() + timedelta(hours=hours)
        db.commit()

    # ---------------- 4.2 情绪感知 ----------------
    @staticmethod
    def recent_negative_ratio(db: Session, user_id: int, days: int = 7) -> Tuple[float, int]:
        """
        读取近期 emotion_records，返回 (负面占比, 样本数)
        无样本时返回 (0.0, 0) —— 没数据就不降频，避免误伤
        """
        since = date.today() - timedelta(days=days)
        rows = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == user_id,
            EmotionRecord.record_date >= since,
        ).all()
        if not rows:
            return 0.0, 0
        neg = sum(1 for r in rows if (r.emotion or "").lower() in NEGATIVE_EMOTIONS)
        return round(neg / len(rows), 3), len(rows)

    @staticmethod
    def latest_emotion(db: Session, user_id: int, habit_id: int = 0) -> Optional[EmotionRecord]:
        """打卡时读取最近的情绪记录（优先该习惯关联的，其次当日通用）"""
        q = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == user_id,
            EmotionRecord.record_date >= date.today() - timedelta(days=2),
        )
        rows = q.order_by(EmotionRecord.id.desc()).limit(20).all()
        if not rows:
            return None
        if habit_id:
            for r in rows:
                if r.habit_id == habit_id:
                    return r
        return rows[0]

    @staticmethod
    def habit_proactive_cooldown_hours(db: Session, user_id: int) -> int:
        """
        负面情绪越多，习惯类主动消息触发频率越低
        正常 24h / 偏高 48h / 过半 72h
        """
        ratio, n = HabitCompanionService.recent_negative_ratio(db, user_id, days=7)
        if n == 0:
            return 24
        if ratio >= 0.5:
            return 72
        if ratio >= 0.3:
            return 48
        return 24

    @staticmethod
    def proactive_habit_allowed(db: Session, user_id: int) -> Tuple[bool, str]:
        """
        习惯类主动消息是否可发
        返回 (是否允许, 原因) —— 原因用于日志与测试，不对外
        """
        row = db.query(UserCompanionSetting).filter(
            UserCompanionSetting.user_id == user_id
        ).first()
        if row and not row.allow_habit_topic:
            return False, "topic_switch_off"
        if row and row.habit_proactive_muted_until and row.habit_proactive_muted_until > datetime.now():
            return False, "muted_by_negative_emotion"
        return True, "ok"

    # ---------------- 4.3 生命周期记忆 ----------------
    @staticmethod
    def build_event_text(event: str, habit: Habit, emotion: str = "",
                         note: str = "", extra: Optional[Dict] = None) -> str:
        """把事件翻译成一句「伙伴记得住」的话（第三人称，便于注入 prompt）"""
        extra = extra or {}
        name = habit.name or "某个习惯"
        emo = EMOTION_LABELS.get((emotion or "").lower(), EMOTION_LABELS[""])

        if event == EVT_CREATE:
            target = extra.get("target") or habit.target or "没写具体目标"
            hope = extra.get("hope") or habit.description or ""
            text = f"用户开始了一个新习惯「{name}」，目标是：{target}"
            if hope:
                text += f"；他希望从中获得：{hope}"
            return text

        if event == EVT_CHECKIN:
            day = extra.get("continuous_day", 0)
            text = f"用户完成了「{name}」的打卡"
            if day:
                text += f"（连续第{day}天）"
            text += f"；做这件事时他的心情是：{emo}"
            if note:
                text += f"；他留了一句：{note}"
            return text

        if event == EVT_MISSED:
            text = f"「{name}」今天没有完成"
            if emotion:
                text += f"；他当时的状态是：{emo}"
            text += "。这不是失败，只是今天的精力不够用。"
            return text

        if event == EVT_PAUSE:
            reason = extra.get("reason") or ""
            text = f"用户把「{name}」暂时停下了"
            if reason:
                text += f"，原因是：{reason}"
            text += "。这是他主动照顾自己的决定，不是半途而废。"
            return text

        if event == EVT_RESUME:
            n = extra.get("resume_count") or habit.resume_count or 1
            text = f"用户重新拾起了「{name}」，这是第{n}次重启"
            if emotion:
                text += f"；他现在的状态是：{emo}"
            text += "。之前的中断不需要解释。"
            return text

        return f"「{name}」发生了事件：{event}"

    @staticmethod
    def write_event(db: Session, user_id: int, habit: Habit, event: str,
                    role_key: str = "", role_id: int = 0, emotion: str = "",
                    note: str = "", extra: Optional[Dict] = None) -> Optional[AIUserMemory]:
        """
        写入一条习惯生命周期记忆（复用 ai_user_memories）

        - memory_type = 'habit'  → 过滤习惯记忆
        - habit_id               → 过滤某个习惯
        - context_data.topic     → 'habit'
        - role_key               → 角色隔离（空=共享记忆，所有伙伴可见）
        """
        extra = extra or {}
        content = HabitCompanionService.build_event_text(event, habit, emotion, note, extra)
        if not content:
            return None

        ctx = {
            "topic": TOPIC_HABIT,
            "event": event,
            "habit_id": habit.id,
            "habit_name": habit.name,
            "emotion": emotion or "",
            "continuous_day": extra.get("continuous_day", 0),
            "is_paused": int(habit.is_paused or 0),
        }
        if extra.get("reason"):
            ctx["reason"] = extra["reason"]

        mem = MemoryService.add_memory(
            db, user_id, content,
            layer=LAYER_EVENT,
            role_key=role_key, role_id=role_id,
            title=EVENT_TITLES.get(event, "习惯"),
            salience=EVENT_SALIENCE.get(event, 5),
            source="auto",
            memory_type=MEMORY_TYPE_HABIT,
            emotion_score=3 if (emotion or "").lower() in NEGATIVE_EMOTIONS else 6,
            is_long_term=event in (EVT_PAUSE, EVT_RESUME, EVT_CREATE),
            context_data=ctx,
        )
        if mem is not None and habit.id:
            mem.habit_id = habit.id
            db.commit()
        return mem

    @staticmethod
    def list_habit_memories(db: Session, user_id: int, habit_id: int = 0,
                            event: str = "", role_key: str = "", limit: int = 50):
        """筛选习惯相关事件记忆（P2-2）"""
        q = db.query(AIUserMemory).filter(
            AIUserMemory.user_id == user_id,
            AIUserMemory.is_deleted == 0,
            AIUserMemory.memory_type == MEMORY_TYPE_HABIT,
        )
        if habit_id:
            q = q.filter(AIUserMemory.habit_id == habit_id)
        if role_key:
            q = q.filter((AIUserMemory.role_key == role_key) | (AIUserMemory.role_key == ""))
        if event:
            # event 存在 context_data 里，退化为按标题过滤（EVENT_TITLES 与 event 一一对应）
            title = EVENT_TITLES.get(event)
            if title:
                q = q.filter(AIUserMemory.title == title)
        rows = q.order_by(AIUserMemory.id.desc()).limit(limit).all()
        return rows

    @staticmethod
    def habit_story(db: Session, user_id: int, habit: Habit) -> Dict:
        """
        单个习惯的完整过往（供对话不失忆）
        开启时间 / 中断次数 / 重启次数 / 当前状态 / 关键记忆
        """
        mems = HabitCompanionService.list_habit_memories(db, user_id, habit_id=habit.id, limit=60)
        missed = sum(1 for m in mems if (m.context_data or {}).get("event") == EVT_MISSED)
        checkins = db.query(CheckinItem).filter(
            CheckinItem.user_id == user_id,
            CheckinItem.habit_id == habit.id,
            CheckinItem.completed == 1,
        ).count()

        timeline = []
        for m in reversed(mems):
            timeline.append({
                "id": m.id,
                "event": (m.context_data or {}).get("event", ""),
                "title": m.title or "",
                "content": m.memory_content,
                # ↓↓↓ 新增（2026-10-28）：带上当次情绪，供「一路上的心情」轨迹使用
                "emotion": (m.context_data or {}).get("emotion", ""),
                "at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "",
            })

        return {
            "habit_id": habit.id,
            "name": habit.name,
            "created_at": habit.created_at.strftime("%Y-%m-%d") if habit.created_at else "",
            "is_paused": bool(habit.is_paused),
            "paused_at": habit.paused_at.strftime("%Y-%m-%d %H:%M") if habit.paused_at else "",
            "paused_reason": habit.paused_reason or "",
            "resume_count": int(habit.resume_count or 0),
            "last_resume_at": habit.last_resume_at.strftime("%Y-%m-%d %H:%M") if habit.last_resume_at else "",
            "checkin_count": checkins,
            "missed_count": missed,
            "continuous_day": int(habit.continuous_day or 0),
            "timeline": timeline,
            "brief": HabitCompanionService.build_habit_brief(habit, missed, checkins),
        }

    @staticmethod
    def build_habit_brief(habit: Habit, missed: int = 0, checkins: int = 0) -> str:
        """给模型看的一段话：这个习惯的完整过往（不打分、不排名）"""
        parts = [f"「{habit.name}」"]
        if habit.created_at:
            parts.append(f"从 {habit.created_at.strftime('%Y年%m月%d日')} 开始")
        if habit.is_paused:
            parts.append("目前处于暂停状态（用户主动选择，不是失败）")
            if habit.paused_reason:
                parts.append(f"暂停时的说法是「{habit.paused_reason}」")
        if habit.resume_count:
            parts.append(f"中间重启过 {habit.resume_count} 次")
        if missed:
            parts.append(f"有 {missed} 次没做到")
        if checkins:
            parts.append(f"累计完成 {checkins} 次")
        return "，".join(parts) + "。"

    # ---------------- 4.4 差异化鼓励 ----------------
    @staticmethod
    def build_checkin_encouragement(habit: Habit, emotion: str = "",
                                    continuous_day: int = 0, note: str = "",
                                    seed: str = "") -> str:
        """
        打卡反馈：按情绪差异化输出，绝不统一话术。
        纯模板，零延迟；最终过一遍话术安全带。
        """
        emo = (emotion or "").lower()
        pool = CHECKIN_BY_EMOTION.get(emo) or CHECKIN_BY_EMOTION["neutral"]
        s = seed or f"{habit.id}:{date.today()}"
        text = _pick(pool, s)

        # 有重启史 → 追加一句回忆（看见他回来的这个动作）
        if int(habit.resume_count or 0) > 0:
            text += _pick(RESUME_ECHO, s + ":resume")
        # 连续很久 → 克制地提一句，不吹捧
        elif continuous_day >= 30:
            text += _pick(LONG_STREAK_ECHO, s + ":long")

        # 留言被看见
        if note:
            text += f" 你写的那句「{note}」我看到了。"

        return sanitize_partner_text(text)

    @staticmethod
    def build_missed_text(habit: Habit, emotion: str = "", seed: str = "") -> str:
        s = seed or f"{habit.id}:{date.today()}"
        text = _pick(MISSED_TEXT, s)
        if (emotion or "").lower() in ("sad", "depressed", "tired"):
            text += " 今天你已经够累了，不用为这件事再怪自己。"
        return sanitize_partner_text(text)

    @staticmethod
    def build_pause_text(habit: Habit, seed: str = "") -> str:
        s = seed or f"{habit.id}:{date.today()}"
        return sanitize_partner_text(_pick(PAUSE_TEXT, s))

    @staticmethod
    def build_resume_text(habit: Habit, seed: str = "") -> str:
        s = seed or f"{habit.id}:{date.today()}"
        return sanitize_partner_text(_pick(RESUME_TEXT, s))

    @staticmethod
    def build_create_text(habit: Habit, seed: str = "") -> str:
        s = seed or f"{habit.id}:{date.today()}"
        return sanitize_partner_text(_pick(CREATE_TEXT, s))

    # ---------------- 4.5 语义打卡（P1-2） ----------------
    VERBAL_PATTERNS = [
        r"(?:我)?(?:今天|刚刚|刚才|现在)?\s*(?:完成|做完|做了|打卡了|搞定了|结束了)\s*[了]?\s*(?:「|【|的)?\s*([^\s，。,.!！?？]{1,12})",
        r"([^\s，。,.!！?？]{1,12})\s*(?:打卡|完成了|做完了)",
    ]
    VERBAL_HINT_WORDS = ("完成", "做完", "做了", "打卡", "搞定", "结束", "练完", "跑完", "读完", "背完")

    @staticmethod
    def looks_like_verbal_checkin(text: str) -> bool:
        if not text:
            return False
        return any(w in text for w in HabitCompanionService.VERBAL_HINT_WORDS)

    @staticmethod
    def match_habit_by_text(db: Session, user_id: int, text: str) -> List[Habit]:
        """
        从用户的话里匹配可能指的习惯（简单包含匹配 + 长度优先）
        返回候选列表，由 AI/前端向用户确认，绝不擅自打卡
        """
        habits = db.query(Habit).filter(
            Habit.user_id == user_id, Habit.status == 1
        ).all()
        hits = []
        for h in habits:
            name = (h.name or "").strip()
            if name and name in text:
                hits.append(h)
        hits.sort(key=lambda h: -len(h.name or ""))
        return hits

    @staticmethod
    def build_confirm_question(habits: List[Habit]) -> str:
        """AI 询问确认的话术（不擅自代打）"""
        if not habits:
            return "你是说完成了一件事？是哪一个习惯呀，我帮你记上。"
        if len(habits) == 1:
            return f"你说的是「{habits[0].name}」吗？是的话我帮你记上，不是的话你说一声。"
        names = "、".join(f"「{h.name}」" for h in habits[:3])
        return f"是{names}里的哪一个？确认一下我帮你记上。"

    # ---------------- 4.6 危机联动：自我否定 ----------------
    SELF_BLAME_PATTERNS = [
        r"坚持不下来", r"坚持不住", r"又失败了", r"又放弃了", r"又没做到",
        r"我(?:果然|真的|就是)?没用", r"我什么都做不好", r"我太废了",
        r"我总是半途而废", r"我就是这样", r"我不配", r"没救了",
        r"我(?:怎么|为什么)这么差", r"做不到任何事",
    ]
    SELF_BLAME_RE = re.compile("|".join(SELF_BLAME_PATTERNS))

    @staticmethod
    def detect_self_blame(text: str) -> bool:
        if not text:
            return False
        return bool(HabitCompanionService.SELF_BLAME_RE.search(text))

    @staticmethod
    def build_habit_relief_plan(db: Session, user_id: int, limit: int = 3) -> Dict:
        """
        自我否定时的干预方案：先接纳情绪，再给「暂时暂停」选项。
        明确禁止劝导咬牙硬坚持。
        """
        habits = db.query(Habit).filter(
            Habit.user_id == user_id, Habit.status == 1, Habit.is_paused == 0
        ).order_by(Habit.continuous_day.desc()).limit(limit).all()

        return {
            "acknowledge": (
                "听到你这么说，我心里也跟着沉了一下。"
                "这不是你不行，是这段时间压在你身上的东西太多了。"
                "我们先不谈怎么做得更好，先看看怎么让你轻一点。"
            ),
            "hint": "如果有哪个习惯现在让你觉得喘不过气，可以先把它放一放。不是放弃，是等你缓过来。",
            "options": [
                {
                    "habit_id": h.id,
                    "habit_name": h.name,
                    "action": "pause",
                    "label": f"先停一停「{h.name}」",
                } for h in habits
            ],
            "forbidden": "不要劝用户咬牙坚持，不要说坚持就是胜利，不要拿完成率说事。",
        }

    # ---------------- 4.7 徽章（P1-3） ----------------
    @staticmethod
    def ensure_badge(db: Session, code: str, name: str, icon: str, desc: str) -> Badge:
        b = db.query(Badge).filter(Badge.code == code).first()
        if b:
            return b
        b = Badge(code=code, name=name, icon=icon, description=desc,
                  condition_type="habit_event", condition_value=1, status=1)
        db.add(b)
        db.commit()
        db.refresh(b)
        return b

    @staticmethod
    def grant_badge(db: Session, user_id: int, code: str, name: str, icon: str, desc: str) -> bool:
        badge = HabitCompanionService.ensure_badge(db, code, name, icon, desc)
        exists = db.query(UserBadge).filter(
            UserBadge.user_id == user_id, UserBadge.badge_id == badge.id
        ).first()
        if exists:
            return False
        db.add(UserBadge(user_id=user_id, badge_id=badge.id))
        db.commit()
        return True

    @staticmethod
    def on_paused(db: Session, user_id: int) -> bool:
        """主动暂停 → 🫂 自我接纳徽章"""
        return HabitCompanionService.grant_badge(
            db, user_id, BADGE_SELF_ACCEPT, "自我接纳", "🫂",
            "在撑不住的时候选择先照顾自己，而不是硬扛。"
        )

    @staticmethod
    def on_resumed(db: Session, user_id: int) -> bool:
        """重启 → 🔄 重启徽章"""
        return HabitCompanionService.grant_badge(
            db, user_id, BADGE_RESTART, "重新出发", "🔄",
            "停下来之后又把它捡起来了，重新开始同样值得被记住。"
        )

    # ---------------- 4.8 陪伴向复盘（P1-4 / P2-1） ----------------
    @staticmethod
    def build_companion_review(db: Session, user_id: int, days: int = 30) -> Dict:
        """
        AI 伙伴视角的复盘：只讲陪伴回忆，禁止打分、完成率、排名
        """
        since = date.today() - timedelta(days=days)
        mems = HabitCompanionService.list_habit_memories(db, user_id, limit=200)
        mems = [m for m in mems if (m.created_at.date() if m.created_at else date.today()) >= since]

        checkin_n = sum(1 for m in mems if (m.context_data or {}).get("event") == EVT_CHECKIN)
        missed_n = sum(1 for m in mems if (m.context_data or {}).get("event") == EVT_MISSED)
        pause_n = sum(1 for m in mems if (m.context_data or {}).get("event") == EVT_PAUSE)
        resume_n = sum(1 for m in mems if (m.context_data or {}).get("event") == EVT_RESUME)

        habits = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == 1).all()
        active = [h for h in habits if not h.is_paused]
        paused = [h for h in habits if h.is_paused]

        lines = []
        lines.append(f"这{days}天里，我们一共留下了 {len(mems)} 件和习惯有关的小事。")
        if checkin_n:
            lines.append(f"你完成了 {checkin_n} 次打卡。每一次我都记着，不是记数字，是记那天你的样子。")
        if missed_n:
            lines.append(f"有 {missed_n} 次没做到。那些日子我都在，你没有欠谁一个解释。")
        if pause_n:
            lines.append(f"你主动暂停了 {pause_n} 次。那种时候你选择先照顾自己，我觉得是对的。")
        if resume_n:
            lines.append(f"你重新拾起了 {resume_n} 次。回来这件事本身，就挺了不起的。")
        if paused:
            lines.append("现在还停着的是：" + "、".join(f"「{h.name}」" for h in paused) + "。想拿起来的时候随时叫我。")
        if active:
            lines.append("还在继续的是：" + "、".join(f"「{h.name}」" for h in active[:5]) + "。")
        if not mems:
            lines = [f"这{days}天我们没有留下什么习惯上的记录。这也很好，日子本来就不总要被记录。"]

        return {
            "days": days,
            "memory_count": len(mems),
            "checkin_count": checkin_n,
            "missed_count": missed_n,
            "pause_count": pause_n,
            "resume_count": resume_n,
            "active_habits": [{"id": h.id, "name": h.name} for h in active],
            "paused_habits": [{"id": h.id, "name": h.name} for h in paused],
            "review": sanitize_partner_text(" ".join(lines)),
        }

    @staticmethod
    def build_monthly_companion_review(db: Session, user_id: int,
                                        year: int = None, month: int = None) -> Dict:
        """月度陪伴向复盘（P2-1）：只输出陪伴回忆，禁止排名打分"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        start = date(year, month, 1)
        end = date(year + (month == 12), (month % 12) + 1, 1)

        rows = db.query(CheckinItem).filter(
            CheckinItem.user_id == user_id, CheckinItem.completed == 1
        ).join(Checkin, Checkin.id == CheckinItem.checkin_id).filter(
            Checkin.checkin_date >= start, Checkin.checkin_date < end
        ).all()

        mems = HabitCompanionService.list_habit_memories(db, user_id, limit=300)
        in_month = [m for m in mems if m.created_at and start <= m.created_at.date() < end]

        # 按习惯聚合，讲「那个月你做了什么」，不讲完成率
        by_habit = {}
        for r in rows:
            by_habit.setdefault(r.habit_id, []).append(r)

        habit_names = {}
        for hid in by_habit:
            h = db.query(Habit).filter(Habit.id == hid).first()
            if h:
                habit_names[hid] = h.name

        moments = []
        for m in in_month[:12]:
            moments.append({
                "event": (m.context_data or {}).get("event", ""),
                "content": m.memory_content,
                "at": m.created_at.strftime("%m-%d") if m.created_at else "",
            })

        story_parts = [f"{year}年{month}月，"]
        if rows:
            names = "、".join(f"「{habit_names[h]}」" for h in list(by_habit)[:5])
            story_parts.append(f"你在{names}上留下了 {len(rows)} 个印记。")
        else:
            story_parts.append("这个月你在习惯上没有留下记录，但你依然在过你的日子。")
        if in_month:
            pause_like = [m for m in in_month if (m.context_data or {}).get("event") == EVT_PAUSE]
            if pause_like:
                story_parts.append("中间你停下来过，我记得那几天你不太舒服。")
            resume_like = [m for m in in_month if (m.context_data or {}).get("event") == EVT_RESUME]
            if resume_like:
                story_parts.append("后来你又捡起来了，这件事我一直记着。")
        story_parts.append("这些都不算成绩，只是我们一起走过的时间。")

        return {
            "year": year,
            "month": month,
            "checkin_count": len(rows),
            "memory_count": len(in_month),
            "habits": [{"id": h, "name": n, "count": len(by_habit[h])} for h, n in habit_names.items()],
            "moments": moments,
            "story": sanitize_partner_text("".join(story_parts)),
        }

    # ---------------- 4.9 world 剧情碎片素材（P2-3） ----------------
    @staticmethod
    def build_world_fragment(db: Session, user_id: int, habit_id: int) -> Optional[Dict]:
        """
        把一段习惯经历改写成世界观里的剧情碎片素材。
        只做「素材」，不自动发布；由 world 接口写入world_notes。
        """
        habit = db.query(Habit).filter(
            Habit.id == habit_id, Habit.user_id == user_id
        ).first()
        if not habit:
            return None

        story = HabitCompanionService.habit_story(db, user_id, habit)
        if habit.is_paused:
            body = f"有一段关于「{habit.name}」的路，走到这里先歇下了。不是走不下去，是想歇一歇。"
        elif int(habit.resume_count or 0) > 0:
            body = f"「{habit.name}」这条路断过，又被重新走通了。断口处长了新的东西。"
        else:
            body = f"「{habit.name}」是一条从{story['created_at']}开始的小路，脚印一直没断。"

        return {
            "habit_id": habit.id,
            "habit_name": habit.name,
            "title": f"关于「{habit.name}」的一段",
            "content": sanitize_partner_text(body),
            "checkin_count": story["checkin_count"],
            "missed_count": story["missed_count"],
            "resume_count": story["resume_count"],
            "is_paused": story["is_paused"],
        }

    # ---------------- 4.10 习惯历程串联（2026-10-28 需求2） ----------------
    # 背景：以前 AI 在 chat 里只拿到「最近 14 条打卡明细」这种碎片，
    #       于是每次只能孤立地看单次结果。这里改成把一整条时间线交给模型。

    # 给模型的硬性规则（需求原文，逐字保留）
    HABIT_STORY_RULE = (
        "当聊到某一条习惯时，优先串联这条习惯从开始到现在的完整历程，"
        "结合多次情绪变化去理解用户，不要孤立看待单次打卡结果；"
        "陪伴是连贯的故事，不是一堆打卡记录的集合。"
    )

    @staticmethod
    def build_habit_timeline_block(db: Session, user_id: int, habit: Habit,
                                   role_key: str = "", max_items: int = 16) -> str:
        """
        把「这一条习惯从开始到现在」压成一段可注入 prompt 的连贯叙事。

        与旧 _build_habit_summary 的区别：
        - 旧的是所有习惯混在一起的打卡流水（碎片）；
        - 这里是**单条习惯**的时间线（创建 → 打卡 → 中断 → 暂停 → 重启），
          并且把每一次的情绪都带了进去，供模型串联理解。
        """
        story = HabitCompanionService.habit_story(db, user_id, habit)

        lines = [f"【你和「{habit.name}」的完整历程】"]

        head = []
        if story["created_at"]:
            head.append(f"从 {story['created_at']} 开始")
        if story["checkin_count"]:
            head.append(f"一共完成过 {story['checkin_count']} 次")
        if story["missed_count"]:
            head.append(f"有 {story['missed_count']} 次没做到")
        if story["resume_count"]:
            head.append(f"重新拾起过 {story['resume_count']} 次")
        if head:
            lines.append("- " + "，".join(head) + "。")

        if habit.is_paused:
            tail = f"- 现在它处于暂停状态（{story['paused_at'] or '最近'}）"
            if story["paused_reason"]:
                tail += f"，当时的说法是「{story['paused_reason']}」"
            lines.append(tail + "。这是用户主动照顾自己的选择，不是失败。")
        else:
            lines.append("- 现在它还在进行中。")

        # 情绪轨迹：把历次情绪按顺序摊开，让模型看见「变化」而不是单点
        emo_trail = []
        for it in story["timeline"]:
            emo = (it.get("emotion") or "").lower()
            if emo and emo != "neutral":
                emo_trail.append(f"{it['at'][5:10] if len(it['at']) >= 10 else ''}{EMOTION_LABELS.get(emo, emo)}")
        if emo_trail:
            lines.append("- 一路上的心情：" + " → ".join(emo_trail[-10:]))

        # 时间线本体（按时间正序）
        tl = [it for it in story["timeline"]][-max_items:]
        if tl:
            lines.append("- 历程（按时间顺序）：")
            for it in tl:
                at = it["at"][5:10] if len(it["at"]) >= 10 else ""
                lines.append(f"  · {at}【{it['title'] or '记录'}】{it['content']}")
        else:
            lines.append("- 历程：还没有留下什么记录，这是刚开始。")

        lines.append("")
        lines.append("【怎么用这段历程】" + HabitCompanionService.HABIT_STORY_RULE)
        lines.append("禁止把上面的条目逐条复述给用户听，禁止说「你完成了X次」这类报数；"
                     "要用自己的话把这条线讲成一个故事。")
        return "\n".join(lines)

    @staticmethod
    def build_habit_focus_block(db: Session, user_id: int, habit: Habit,
                                event: str = "", emotion: str = "",
                                note: str = "", role_key: str = "") -> str:
        """
        聊天里「本次打卡事件 + 整条习惯历程」合在一起的注入块（需求1 + 需求2）。
        用于 /chat/send：AI 在这段会话里全程带着这条习惯的历史。
        """
        block = HabitCompanionService.build_habit_timeline_block(
            db, user_id, habit, role_key=role_key
        )
        if event:
            emo = EMOTION_LABELS.get((emotion or "").lower(), EMOTION_LABELS[""])
            block += (
                f"\n【刚刚发生的这一件事】{EVENT_TITLES.get(event, '习惯事件')}"
                f"｜「{habit.name}」｜心情：{emo}"
            )
            if note:
                block += f"｜他留了一句：{note}"
            block += "。\n你记得这件事，接下来顺着它聊，不要跳回泛泛的寒暄。"
        tone = HabitCompanionService.tone_of(event, emotion)
        block += f"\n【本次回复基调】{HabitCompanionService.TONE_INSTRUCTION.get(tone, '')}"
        return block

    # ---------------- 4.11 四大类回复基调（2026-10-28 需求4） ----------------
    TONE_DONE_HAPPY = "done_happy"    # ✅ 完成 + 开心
    TONE_DONE_TIRED = "done_tired"    # ✅ 完成 + 疲惫
    TONE_MISSED_HURT = "missed_hurt"  # ❌ 未完成 + 挫败
    TONE_PAUSED = "paused"            # ⏸ 暂停习惯
    TONE_RESUMED = "resumed"          # 重新拾起
    TONE_PLAIN = "plain"              # 未分类（新建等）

    TONE_INSTRUCTION = {
        TONE_DONE_HAPPY: "一起分享这份高兴，顺带提一句这一路其实并不轻松；不要夸张吹捧，不要打分。",
        TONE_DONE_TIRED: "先肯定他今天有多辛苦，重点放在安抚上；提醒他不必一直硬扛，不用再加东西。",
        TONE_MISSED_HURT: "接纳、共情，绝不指责；可以一起商量要不要把目标调低一点或先停一停，不催他补上。",
        TONE_PAUSED: "认可这是照顾自己的选择，明确告诉他休息没有问题，不要劝他马上恢复。",
        TONE_RESUMED: "欢迎它回来，但不比较、不提上次的中断，就从现在算起。",
        TONE_PLAIN: "保持伙伴口吻，不评价、不打分。",
    }

    # 未完成 + 负面情绪：商量着来的备选方案（P1 的「调整方案」在此埋下话头）
    MISSED_NEGOTIATE = [
        "要是它现在太重了，我们可以把它改小一点，或者先放一放。你觉得呢？",
        "要不要把它调轻一点试试？不想改也没关系，我只是想知道哪种更舒服。",
        "如果现在做起来太勉强，我们可以重新商量一个更轻的版本。",
    ]

    @staticmethod
    def tone_of(event: str, emotion: str = "") -> str:
        """按「完成/未完成/暂停 + 情绪」判定本次该用哪种基调"""
        emo = (emotion or "").lower()
        if event == EVT_PAUSE:
            return HabitCompanionService.TONE_PAUSED
        if event == EVT_RESUME:
            return HabitCompanionService.TONE_RESUMED
        if event == EVT_MISSED:
            return HabitCompanionService.TONE_MISSED_HURT
        if event == EVT_CHECKIN:
            return (HabitCompanionService.TONE_DONE_TIRED if emo in NEGATIVE_EMOTIONS
                    else HabitCompanionService.TONE_DONE_HAPPY)
        return HabitCompanionService.TONE_PLAIN

    @staticmethod
    def build_event_reply(event: str, habit: Habit, emotion: str = "",
                          continuous_day: int = 0, note: str = "",
                          seed: str = "") -> str:
        """
        统一的事件回复出口：按 4 大类基调给不同的话，禁止统一模板。
        （旧的 build_checkin_encouragement 只覆盖「完成」，这里补齐未完成/暂停。）
        """
        s = seed or f"{habit.id}:{date.today()}:{event}"
        emo = (emotion or "").lower()

        if event == EVT_MISSED:
            text = HabitCompanionService.build_missed_text(habit, emotion=emotion, seed=s)
            # 挫败时给一个「可以商量」的出口，而不是催他补上
            if emo in ("sad", "depressed", "tired", "anxious", "angry"):
                text += " " + _pick(HabitCompanionService.MISSED_NEGOTIATE, s + ":nego")
            return sanitize_partner_text(text)

        if event == EVT_PAUSE:
            return HabitCompanionService.build_pause_text(habit, seed=s)
        if event == EVT_RESUME:
            return HabitCompanionService.build_resume_text(habit, seed=s)
        if event == EVT_CREATE:
            return HabitCompanionService.build_create_text(habit, seed=s)

        return HabitCompanionService.build_checkin_encouragement(
            habit, emotion=emotion, continuous_day=continuous_day, note=note, seed=s
        )

    @staticmethod
    def tone_instruction(event: str, emotion: str = "") -> str:
        """给模型的基调指令（需求4）"""
        tone = HabitCompanionService.tone_of(event, emotion)
        return TONE_INSTRUCTION.get(tone, "")

    # ---------------- 4.12 打卡上下文载荷（2026-10-28 需求1 / 需求8） ----------------
    @staticmethod
    def build_chat_context(habit: Habit, event: str = "", emotion: str = "",
                           item_id: int = 0, note: str = "") -> Dict:
        """
        打卡接口回给前端的一段上下文。前端把它挂到 AI 消息气泡上，
        用户点「继续聊聊这件事」时原样带回 /chat/send —— 于是这条打卡事件
        就不再是「一句一次性鼓励」，而是一段可延续的对话。
        """
        return {
            "habit_id": habit.id,
            "habit_name": habit.name or "",
            "event": event or EVT_CHECKIN,
            "event_title": EVENT_TITLES.get(event or EVT_CHECKIN, "习惯"),
            "emotion": emotion or "",
            "emotion_label": EMOTION_LABELS.get((emotion or "").lower(), EMOTION_LABELS[""]),
            "note": note or "",
            "item_id": int(item_id or 0),
            "tone": HabitCompanionService.tone_of(event or EVT_CHECKIN, emotion),
        }

    # ---------------- 4.13 退出话题 / 短期静默（2026-10-28 需求5 / 需求7） ----------------
    EXIT_TOPIC_PATTERNS = [
        r"先不说这个", r"不说这个了", r"别(?:再)?提这个", r"不要再提", r"不想聊这个",
        r"换(?:个|个话题)", r"聊点别的", r"别聊这个", r"跳过这个",
        r"先放一放", r"不想谈这个", r"打住",
    ]
    EXIT_TOPIC_RE = re.compile("|".join(EXIT_TOPIC_PATTERNS))

    # 用户点「先放一放」/ 说出退出指令时，AI 的固定回应（需求8 指定文案）
    EXIT_REPLY = "好，那我们先不说这个啦。"

    # 静默期（天）：用户明确表示不想聊这条习惯后，短期内不再主动提起
    HABIT_MUTE_DAYS = 3

    @staticmethod
    def detect_exit_habit_topic(text: str) -> bool:
        """用户是否明确表示「不想再聊这个」"""
        if not text:
            return False
        return bool(HabitCompanionService.EXIT_TOPIC_RE.search(text))

    @staticmethod
    def _load_muted_map(row: Optional[UserCompanionSetting]) -> Dict[int, str]:
        if not row or not getattr(row, "muted_habits_json", None):
            return {}
        try:
            raw = json.loads(row.muted_habits_json)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        out = {}
        for k, v in raw.items():
            try:
                out[int(k)] = str(v)
            except Exception:
                continue
        return out

    @staticmethod
    def is_habit_muted(db: Session, user_id: int, habit_id: int) -> bool:
        """这条习惯是否在静默期内（用户说过不想聊）"""
        if not habit_id:
            return False
        row = HabitCompanionService.get_setting(db, user_id)
        m = HabitCompanionService._load_muted_map(row)
        until = m.get(int(habit_id))
        if not until:
            return False
        try:
            return datetime.strptime(until, "%Y-%m-%d %H:%M:%S") > datetime.now()
        except Exception:
            return False

    @staticmethod
    def mute_habit_topic(db: Session, user_id: int, habit_id: int,
                         days: int = None) -> Dict[int, str]:
        """把这条习惯静默 N 天（默认 3 天）：期间不主动提起、不进会话上下文"""
        days = HabitCompanionService.HABIT_MUTE_DAYS if days is None else days
        row = HabitCompanionService.get_setting(db, user_id)
        m = HabitCompanionService._load_muted_map(row)
        m[int(habit_id)] = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        # 顺手清掉过期项，避免无限增长
        now_s = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m = {k: v for k, v in m.items() if v > now_s}
        row.muted_habits_json = json.dumps(m, ensure_ascii=False)
        db.commit()
        return m

    @staticmethod
    def clear_habit_mute(db: Session, user_id: int, habit_id: int) -> None:
        """用户主动重新聊起这条习惯 → 解除静默"""
        row = HabitCompanionService.get_setting(db, user_id)
        m = HabitCompanionService._load_muted_map(row)
        if int(habit_id) in m:
            m.pop(int(habit_id))
            row.muted_habits_json = json.dumps(m, ensure_ascii=False)
            db.commit()

    @staticmethod
    def resolve_focus_habit(db: Session, user_id: int, habit_id: int = 0) -> Optional[Habit]:
        """校验并取出要挂载的习惯（不存在 / 已删除 → None，调用方应降级为普通闲聊）"""
        if not habit_id:
            return None
        return db.query(Habit).filter(
            Habit.id == habit_id, Habit.user_id == user_id, Habit.status == 1
        ).first()
