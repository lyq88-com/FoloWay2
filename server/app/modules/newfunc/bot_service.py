# -*- coding: utf-8 -*-
"""
多 AI 伙伴独立人设与隔离记忆（newfunc · 模块三）
- ai_bot_info：用户自建伙伴（名称/头像/性格/说话风格/自述/禁忌）
- ai_bot_memory：按 bot_id 强隔离的记忆（不同伙伴互不互通；重置只清单个伙伴）
- 回复严格贴合人设 + 强活人感（system prompt 明令禁止模板化话术）
- 只读复用旧数据：情绪日历（push_setting.diary_read_auth 授权后）用于主动陪伴
"""
import datetime as dt
import random
import re
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.modules.newfunc.models import AIBotInfo, AIBotMemory, UserDiaryMood

MAX_MEMORY_PER_BOT = 200

# 用户消息里的高价值记忆规则（轻量规则抽取，AI 不可用也能沉淀记忆）
_MEMORY_PATTERNS = [
    (re.compile(r"我(?:喜欢|热爱|超爱)([^。，,；;！!？?\s]{1,30})"), "preference", 8),
    (re.compile(r"我(?:讨厌|不喜欢|烦)([^。，,；;！!？?\s]{1,30})"), "preference", 7),
    (re.compile(r"我(?:要|准备|打算)(?:考|复习|参加)([^。，,；;！!？?\s]{1,30})"), "fact", 9),
    (re.compile(r"我(?:在|正在)(?:准备|复习|学)([^。，,；;！!？?\s]{1,30})"), "fact", 8),
    (re.compile(r"我叫([^。，,；;！!？?\s]{1,10})"), "fact", 9),
    (re.compile(r"我是([^。，,；;！!？?\s]{1,15})"), "fact", 6),
    (re.compile(r"我(?:最近)?(?:很|有点|超)?(开心|难过|焦虑|压力大|累|烦躁|emo|兴奋)"),
     "emotion", 7),
]


def _now():
    return dt.datetime.now()


# ============================================================
# 伙伴 CRUD
# ============================================================
def list_bots(db: Session, uid: int) -> List[Dict]:
    rows = db.query(AIBotInfo).filter(
        AIBotInfo.uid == uid, AIBotInfo.is_active == 1
    ).order_by(AIBotInfo.created_at.asc()).all()
    out = []
    for b in rows:
        d = b.to_dict()
        d["memory_count"] = db.query(AIBotMemory).filter(
            AIBotMemory.bot_id == b.id).count()
        out.append(d)
    return out


def create_bot(db: Session, uid: int, data: Dict) -> Dict:
    name = (data.get("name") or "").strip()[:30]
    if not name:
        return {"__error__": "伙伴名称不能为空", "__code__": 400}
    count = db.query(AIBotInfo).filter(
        AIBotInfo.uid == uid, AIBotInfo.is_active == 1).count()
    if count >= 10:
        return {"__error__": "最多创建 10 个 AI 伙伴", "__code__": 400}
    b = AIBotInfo(
        uid=uid, name=name,
        avatar=(data.get("avatar") or "🌿")[:20],
        personality=(data.get("personality") or "")[:300],
        speak_style=(data.get("speak_style") or "")[:300],
        self_intro=(data.get("self_intro") or "")[:500],
        taboo=(data.get("taboo") or "")[:300],
        allow_push=1 if data.get("allow_push", True) else 0,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    d = b.to_dict()
    d["memory_count"] = 0
    return d


def _get_bot(db: Session, uid: int, bot_id: int):
    return db.query(AIBotInfo).filter(
        AIBotInfo.id == bot_id, AIBotInfo.uid == uid, AIBotInfo.is_active == 1).first()


def update_bot(db: Session, uid: int, bot_id: int, data: Dict) -> Dict:
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    for k in ("name", "avatar", "personality", "speak_style", "self_intro",
              "taboo", "allow_push"):
        if k in data:
            v = data[k]
            if k == "allow_push":
                v = 1 if v else 0
            elif k == "name":
                v = (v or "").strip()[:30]
                if not v:
                    return {"__error__": "伙伴名称不能为空", "__code__": 400}
            else:
                v = (v or "")[:300]
            setattr(b, k, v)
    db.commit()
    return {"id": b.id}


def delete_bot(db: Session, uid: int, bot_id: int) -> Dict:
    """删除伙伴：连同该伙伴的全部记忆一并清除（只影响此 bot_id）"""
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    b.is_active = 0
    db.query(AIBotMemory).filter(AIBotMemory.bot_id == bot_id).delete(
        synchronize_session=False)
    db.commit()
    return {"id": bot_id}


# ============================================================
# 隔离记忆
# ============================================================
def recall_memories(db: Session, bot_id: int, limit: int = 10) -> List[str]:
    """按 重要度+新近 排序召回该伙伴的记忆（严格限定 bot_id）"""
    rows = db.query(AIBotMemory).filter(
        AIBotMemory.bot_id == bot_id
    ).order_by(AIBotMemory.importance.desc(), AIBotMemory.id.desc()
               ).limit(limit).all()
    return [r.content for r in rows]


def add_memories(db: Session, bot_id: int, uid: int,
                 items: List[Tuple[str, str, int]]) -> int:
    """写入记忆（去重 + 容量上限，超出淘汰最旧低重要度）"""
    added = 0
    for content, mtype, imp in items:
        content = (content or "").strip()[:500]
        if not content:
            continue
        dup = db.query(AIBotMemory).filter(
            AIBotMemory.bot_id == bot_id, AIBotMemory.content == content).first()
        if dup:
            continue
        db.add(AIBotMemory(bot_id=bot_id, uid=uid, mem_type=mtype,
                           content=content, importance=max(1, min(10, imp))))
        added += 1
    if added:
        total = db.query(AIBotMemory).filter(AIBotMemory.bot_id == bot_id).count()
        if total > MAX_MEMORY_PER_BOT:
            old = db.query(AIBotMemory).filter(
                AIBotMemory.bot_id == bot_id
            ).order_by(AIBotMemory.importance.asc(), AIBotMemory.id.asc()
                       ).limit(total - MAX_MEMORY_PER_BOT).all()
            for m in old:
                db.delete(m)
    db.commit()
    return added


def extract_memories_from_text(text: str) -> List[Tuple[str, str, int]]:
    out = []
    for pat, mtype, imp in _MEMORY_PATTERNS:
        m = pat.search(text)
        if m:
            frag = m.group(0) if mtype == "emotion" else m.group(0)
            out.append((frag, mtype, imp))
    return out[:5]


def list_memories(db: Session, uid: int, bot_id: int,
                  mem_type: str = "", page: int = 1, size: int = 30) -> Dict:
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    q = db.query(AIBotMemory).filter(AIBotMemory.bot_id == bot_id)
    if mem_type:
        q = q.filter(AIBotMemory.mem_type == mem_type)
    total = q.count()
    rows = q.order_by(AIBotMemory.id.desc()).offset(
        (max(1, page) - 1) * size).limit(size).all()
    return {"total": total, "list": [r.to_dict() for r in rows],
            "bot": b.to_dict()}


def delete_memory(db: Session, uid: int, bot_id: int, memory_id: int) -> Dict:
    m = db.query(AIBotMemory).filter(
        AIBotMemory.id == memory_id, AIBotMemory.bot_id == bot_id,
        AIBotMemory.uid == uid).first()
    if not m:
        return {"__error__": "记忆不存在", "__code__": 404}
    db.delete(m)
    db.commit()
    return {"id": memory_id}


def reset_memory(db: Session, uid: int, bot_id: int) -> Dict:
    """重置单个伙伴记忆：只清该 bot_id，不影响其他伙伴"""
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    n = db.query(AIBotMemory).filter(AIBotMemory.bot_id == bot_id).delete(
        synchronize_session=False)
    db.commit()
    return {"bot_id": bot_id, "cleared": n}


ALLOWED_MEM_TYPES = {"fact", "preference", "emotion", "dialogue"}


def create_memory(db: Session, uid: int, bot_id: int, content: str,
                  mem_type: str = "fact", importance: int = 5) -> Dict:
    """用户手动写入一条记忆（复用去重 + 容量上限逻辑）"""
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    content = (content or "").strip()[:500]
    if not content:
        return {"__error__": "记忆内容不能为空", "__code__": 400}
    if mem_type not in ALLOWED_MEM_TYPES:
        mem_type = "fact"
    importance = max(1, min(10, int(importance or 5)))

    existing = db.query(AIBotMemory).filter(
        AIBotMemory.bot_id == bot_id, AIBotMemory.content == content).first()
    if existing:
        return {"memory": existing.to_dict(), "created": False}

    add_memories(db, bot_id, uid, [(content, mem_type, importance)])
    row = db.query(AIBotMemory).filter(
        AIBotMemory.bot_id == bot_id, AIBotMemory.content == content
    ).order_by(AIBotMemory.id.desc()).first()
    return {"memory": row.to_dict() if row else None, "created": True}


# ============================================================
# 人设 System Prompt（强活人感 + 严格贴合 + 记忆注入）
# ============================================================
def build_persona_prompt(b: AIBotInfo, memories: List[str],
                         today_context: str = "") -> str:
    lines = [
        f"你是「{b.name}」，用户亲手创造的 AI 伙伴，不是客服，不是助手，是一个活生生的朋友。",
    ]
    if b.self_intro:
        lines.append(f"你的背景与自述：{b.self_intro}")
    if b.personality:
        lines.append(f"你的性格：{b.personality}")
    if b.speak_style:
        lines.append(f"你的说话风格：{b.speak_style}")
    if b.taboo:
        lines.append(f"你的禁忌（绝对不可违反）：{b.taboo}")
    lines += [
        "表达要求：",
        "1. 完全以第一人称活在人设里，回复必须带有你性格中真实的情绪起伏与主观想法；",
        "2. 严禁模板化、客服腔、鸡汤腔（禁止出现『作为AI』『希望这能帮到你』『如果你还有问题』等句式）；",
        "3. 回复贴合用户当下说的话，可以追问、吐槽、开玩笑、表达担心，像真人发消息一样自然，长度通常不超过 3 句；",
        "4. 记忆是你和用户共同经历的过去，可自然引用，但不要一次性罗列。",
    ]
    if memories:
        lines.append("你记得的关于用户的事（仅限本伙伴的记忆）：\n- " + "\n- ".join(memories))
    if today_context:
        lines.append(f"用户今日状态（仅供你自然关心，不要原文复述）：{today_context}")
    return "\n".join(lines)


# ============================================================
# 对话
# ============================================================
async def bot_chat(db: Session, uid: int, bot_id: int, text: str,
                   history: List[Dict] = None) -> Dict:
    b = _get_bot(db, uid, bot_id)
    if not b:
        return {"__error__": "伙伴不存在", "__code__": 404}
    text = (text or "").strip()[:2000]
    if not text:
        return {"__error__": "消息不能为空", "__code__": 400}

    memories = recall_memories(db, bot_id, limit=10)
    system = build_persona_prompt(b, memories)
    # ↓↓↓ 新增（2026-11-15）：情绪低落时允许顺口建议去做点具体的事 ↓↓↓
    # 复用已有情绪识别；识别失败或用户拒绝建议时保持原 prompt 不变
    try:
        from app.services.emotion_service import EmotionService
        if (EmotionService.analyze_emotion(text).get("valence") == "negative"
                and not EmotionService.is_rejecting_comfort(text)):
            system += ("\n如果自然合适，可以在回复最后顺口邀请用户去做一件具体的事"
                       "（正念呼吸、写情绪树洞、一起专注），一句话带过，不要列清单、不要说教。")
    except Exception:
        pass
    # ↑↑↑ 新增结束 ↑↑↑
    msgs = [{"role": "system", "content": system}]
    for h in (history or [])[-8:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            msgs.append({"role": h["role"], "content": str(h["content"])[:1000]})
    msgs.append({"role": "user", "content": text})

    from app.services.ai_service import AIService
    reply = (await AIService.chat_non_stream(msgs)).strip()
    if not reply:
        reply = _fallback_reply(b, text, memories)

    added = add_memories(db, bot_id, uid, extract_memories_from_text(text))
    b.last_chat_at = _now()
    db.commit()
    return {"reply": reply, "bot_id": bot_id, "bot_name": b.name,
            "memories_added": added}


def _fallback_reply(b: AIBotInfo, text: str, memories: List[str]) -> str:
    """AI 不可用时的人设化兜底（从用户话语/记忆里取材，避免完全模板腔）"""
    openers = {
        "gentle": "嗯，我在听。",
        "default": "",
    }
    mem = f"对了，还记得你{memories[0][2:]}……改天再聊这个。" if memories else ""
    tail = f"（{b.name}记下了）" if len(text) > 10 else ""
    return f"{openers.get('gentle', '')}你说「{text[:20]}」，{b.name}在这里陪着你。{mem}{tail}"


# ============================================================
# 主动陪伴消息（供定时任务与手动触发）
# ============================================================
def _today_context(db: Session, uid: int, diary_auth: bool) -> str:
    """只读汇总当日状态（打卡/待办/情绪/日记），供伙伴自然关心"""
    from app.models.habit import Checkin
    from app.models.schedule import Schedule
    from app.models.emotion import EmotionRecord
    today = _now().date()
    parts = []
    ck = db.query(Checkin).filter(
        Checkin.user_id == uid, Checkin.checkin_date == today,
        Checkin.status == 1).first()
    if ck:
        parts.append(f"今日打卡完成率{float(ck.completion_rate or 0):.0f}%")
    else:
        parts.append("今天还没打卡")
    scs = db.query(Schedule).filter(
        Schedule.schedule_date == today, Schedule.status == 1).all()
    if scs:
        done = sum(1 for x in scs if x.is_done)
        parts.append(f"待办 {done}/{len(scs)} 完成")
    emos = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == uid, EmotionRecord.record_date == today).all()
    if emos:
        parts.append("情绪记录：" + "、".join(e.emotion for e in emos[-3:]))
    if diary_auth:
        d = db.query(UserDiaryMood).filter(
            UserDiaryMood.uid == uid, UserDiaryMood.diary_date == today).first()
        if d:
            if d.mood_tags:
                parts.append("日记心情标签：" + "、".join(d.mood_tags))
            if d.diary_text:
                parts.append("日记片段：" + d.diary_text[:60])
    return "；".join(parts)


async def build_proactive_message(db: Session, uid: int, mood: str = "",
                                  diary_auth: bool = False,
                                  bot_ids: List[int] = None) -> Tuple[str, int]:
    """为用户生成一条贴合人设的主动陪伴消息；返回 (内容, bot_id)，无可用伙伴返回 ('', 0)"""
    q = db.query(AIBotInfo).filter(
        AIBotInfo.uid == uid, AIBotInfo.is_active == 1, AIBotInfo.allow_push == 1)
    if bot_ids:
        q = q.filter(AIBotInfo.id.in_(bot_ids))
    bots = q.all()
    if not bots:
        return "", 0
    b = random.choice(bots)
    memories = recall_memories(db, b.id, limit=6)
    ctx = _today_context(db, uid, diary_auth)
    system = build_persona_prompt(b, memories, ctx) + (
        "\n当前任务：主动给用户发一条关心消息。要求：结合上面的今日状态与你对用户的记忆，"
        "只发一条，像忽然想起 TA 一样自然，25 字以内，不要提问超过一个，不要出现『检查到』『系统』等机器词。")
    from app.services.ai_service import AIService
    try:
        msg = (await AIService.chat_non_stream(
            [{"role": "system", "content": system}])).strip().split("\n")[0][:120]
    except Exception:
        msg = ""
    if not msg:
        # 人设化兜底：取一条记忆或今日状态自然组装
        if memories:
            msg = f"忽然想起你{memories[0]}，怎么样啦？"
        elif ctx:
            msg = f"看到你{ctx.split('；')[0]}，想跟你说句悄悄话：辛苦啦。"
        else:
            msg = f"我是{b.name}，路过想你了，今天过得还好吗？"
    return msg, b.id
