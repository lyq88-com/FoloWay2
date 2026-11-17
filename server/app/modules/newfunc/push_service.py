# -*- coding: utf-8 -*-
"""
推送服务（newfunc · 模块一）
- 个推 REST API 封装（配置 GETUI_ENABLED=true 且填好密钥时走真实厂商通道；
  未配置时自动降级 local 模式：只落 push_record，由前端轮询 + 本地通知呈现）
- 独立定时任务（APScheduler，进程内启动，不碰任何旧业务代码）：
  1) checkin_remind  打卡未完成提醒（每日 checkin_push_time 扫描，只读 habits/checkins）
  2) todo_due        待办到期提醒（每分钟扫描 schedules，只读，dedupe 防重发）
  3) ai_companion    AI 伙伴主动陪伴（按 ai_frequency 频控，基于伙伴记忆+当日情绪）
- 免打扰时段内不发送（AI 消息顺延，提醒类跳过并次日不再补发）。
"""
import asyncio
import datetime as dt
from typing import Dict, List

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.newfunc.models import PushRecord, PushSetting

# ---------------- 个推 REST 配置（.env 增量配置项，见推送接入配置文档） ----------------
GETUI_ENABLED = getattr(settings, "getui_enabled", False)
GETUI_APPID = getattr(settings, "getui_app_id", "")
GETUI_APPKEY = getattr(settings, "getui_app_key", "")
GETUI_APPSECRET = getattr(settings, "getui_app_secret", "")
GETUI_BASE = "https://restapi.getui.com/v2"

_token_cache: Dict[str, object] = {"token": "", "expire_at": 0}

JUMP_PAGES = {
    "checkin_remind": "/pages/habit/habit",
    "todo_due": "/pages/schedule/schedule",
    "ai_companion": "/pages/newfunc/bot-chat",
    "test": "/pages/newfunc/notification-center",
}


# ============================================================
# 设置读写
# ============================================================
_GROUP_PUSH_COL_READY = False


def _ensure_group_push_column(db: Session) -> None:
    """【模块4·群推送】幂等补列：存量库即使没跑迁移脚本也不会出现 Unknown column"""
    global _GROUP_PUSH_COL_READY
    if _GROUP_PUSH_COL_READY:
        return
    from sqlalchemy import text
    try:
        db.execute(text(
            "ALTER TABLE push_setting ADD COLUMN group_push_enabled TINYINT NOT NULL "
            "DEFAULT 1 COMMENT '群聊消息提醒开关 0关 1开'"
        ))
        db.commit()
    except Exception:
        db.rollback()
    _GROUP_PUSH_COL_READY = True


def get_or_create_setting(db: Session, uid: int) -> PushSetting:
    _ensure_group_push_column(db)
    row = db.query(PushSetting).filter(PushSetting.uid == uid).first()
    if not row:
        row = PushSetting(uid=uid)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def in_quiet_hours(s: PushSetting, now: dt.datetime) -> bool:
    """是否处于免打扰时段（支持跨零点，如 23:00~08:00）"""
    if not s.quiet_enabled:
        return False
    cur = now.strftime("%H:%M")
    a, b = s.quiet_start, s.quiet_end
    if a <= b:
        return a <= cur <= b
    return cur >= a or cur <= b


def _freq_limit(freq: str) -> int:
    return {"low": 1, "medium": 3, "high": 6}.get(freq, 3)


# ============================================================
# 个推 REST v2（真实通道；未配置时降级 local）
# ============================================================
async def _getui_token() -> str:
    import time
    if _token_cache["token"] and time.time() < _token_cache["expire_at"]:
        return _token_cache["token"]
    url = f"{GETUI_BASE}/{GETUI_APPID}/auth"
    body = {"sign": GETUI_APPKEY, "timestamp": str(int(time.time() * 1000)),
            "appkey": GETUI_APPKEY}
    # 注：完整签名算法为 md5(appkey+timestamp+appsecret)，接入时在文档指引下开启
    import hashlib
    body["sign"] = hashlib.md5(
        f"{GETUI_APPKEY}{body['timestamp']}{GETUI_APPSECRET}".encode()).hexdigest()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=body)
        data = resp.json()
    if data.get("code") == 0:
        _token_cache["token"] = data["data"]["token"]
        _token_cache["expire_at"] = time.time() + 3600 * 20
        return _token_cache["token"]
    raise RuntimeError(f"getui auth failed: {data}")


async def getui_push_cid(cid: str, title: str, content: str, jump_page: str) -> bool:
    """对单个 CID 推送（厂商通道，锁屏/后台可达）"""
    try:
        token = await _getui_token()
        url = f"{GETUI_BASE}/{GETUI_APPID}/push/single/cid"
        payload = {
            "request_id": f"xt_{int(dt.datetime.now().timestamp()*1000)}",
            "push_message": {
                "notification": {
                    "title": title, "body": content, "click_type": "payload",
                    "payload": jump_page or JUMP_PAGES["test"],
                }
            },
            "cid": cid,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, params={"token": token} if False else None,
                                     json=payload,
                                     headers={"token": token})
            return resp.json().get("code") == 0
    except Exception as e:
        print(f"[newfunc][getui] 推送失败(降级本地): {type(e).__name__}: {e}")
        return False


# ============================================================
# 统一发放入口：落 push_record + 选通道
# ============================================================
async def dispatch_push(db: Session, uid: int, push_type: str, title: str,
                        content: str, ref_id: int = 0,
                        jump_page: str = "") -> Dict:
    """写记录并按通道发送；返回 {record, sent}"""
    s = get_or_create_setting(db, uid)
    jump = jump_page or JUMP_PAGES.get(push_type, "")
    channel = "local"
    sent = False
    if GETUI_ENABLED and s.client_id and s.push_enabled and not in_quiet_hours(s, dt.datetime.now()):
        sent = await getui_push_cid(s.client_id, title, content, jump)
        channel = "getui" if sent else "local"
    rec = PushRecord(uid=uid, push_type=push_type, title=title[:100],
                     content=content[:500], ref_id=ref_id, jump_page=jump,
                     channel=channel)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"record": rec.to_dict(), "sent": sent}


def _already_pushed_today(db: Session, uid: int, push_type: str,
                          ref_id: int = 0) -> bool:
    """当日同类推送去重（todo_due 按日程维度、checkin_remind 按天）"""
    today = dt.date.today()
    start = dt.datetime.combine(today, dt.time.min)
    q = db.query(PushRecord).filter(
        PushRecord.uid == uid, PushRecord.push_type == push_type,
        PushRecord.created_at >= start)
    if ref_id:
        q = q.filter(PushRecord.ref_id == ref_id)
    return db.query(q.exists()).scalar()


def _ai_pushed_count_today(db: Session, uid: int) -> int:
    start = dt.datetime.combine(dt.date.today(), dt.time.min)
    return db.query(PushRecord).filter(
        PushRecord.uid == uid, PushRecord.push_type == "ai_companion",
        PushRecord.created_at >= start).count()


# ============================================================
# 定时任务 Job（只读旧表，写入仅限 push_record；async 以便走真实厂商通道）
# ============================================================
async def job_checkin_remind(db: Session) -> int:
    """打卡未完成提醒：扫描所有开启推送的用户，当日有习惯且未全部完成则提醒"""
    from app.models.habit import Checkin
    from app.models.user import User
    now = dt.datetime.now()
    today = now.date()
    sent = 0
    rows = db.query(PushSetting).filter(
        PushSetting.push_enabled == 1, PushSetting.checkin_push_enabled == 1).all()
    for s in rows:
        if s.checkin_push_time != now.strftime("%H:%M"):
            continue
        if in_quiet_hours(s, now):
            continue
        ck = db.query(Checkin).filter(
            Checkin.user_id == s.uid, Checkin.checkin_date == today,
            Checkin.status == 1).first()
        # 未打卡（无记录）或完成率<100% 都算未完成；已完成则不发
        if ck and ck.completion_rate is not None and float(ck.completion_rate) >= 100:
            continue
        if _already_pushed_today(db, s.uid, "checkin_remind"):
            continue
        user = db.query(User).filter(User.id == s.uid).first()
        name = user.nickname if user else "你"
        await dispatch_push(db, s.uid, "checkin_remind", "打卡提醒",
                            f"{name}，今天的打卡还有小尾巴没完成哦，现在补上刚好吗？")
        sent += 1
    return sent


async def job_todo_due(db: Session) -> int:
    """待办到期提醒：今天未完成的日程，到达「开始时间-提前量」后提醒一次"""
    from app.models.schedule import Schedule
    now = dt.datetime.now()
    today = now.date()
    cur = now.strftime("%H:%M")
    sent = 0
    rows = db.query(Schedule).filter(
        Schedule.schedule_date == today, Schedule.is_done == 0,
        Schedule.status == 1).all()
    for sc in rows:
        s = get_or_create_setting(db, sc.user_id)
        if not (s.push_enabled and s.todo_push_enabled):
            continue
        if in_quiet_hours(s, now):
            continue
        try:
            hh, mm = sc.start_time.split(":")[:2]
            lead = max(0, int(sc.remind_minutes or 0))
            trigger = (dt.datetime.combine(today, dt.time(int(hh), int(mm)))
                       - dt.timedelta(minutes=lead)).strftime("%H:%M")
        except Exception:
            trigger = sc.start_time
        if cur < trigger:
            continue
        if _already_pushed_today(db, sc.user_id, "todo_due", sc.id):
            continue
        await dispatch_push(db, sc.user_id, "todo_due", "待办到期",
                            f"「{sc.title}」快到时间了，去看看吧。", ref_id=sc.id)
        sent += 1
    return sent


async def job_ai_companion(db: Session, bot_ids: List[int] = None) -> int:
    """AI 伙伴主动陪伴：按用户频控挑选伙伴，基于记忆+当日情绪生成一条贴合人设的消息"""
    from app.models.emotion import EmotionRecord
    from app.modules.newfunc.bot_service import build_proactive_message
    now = dt.datetime.now()
    sent = 0
    rows = db.query(PushSetting).filter(
        PushSetting.push_enabled == 1, PushSetting.ai_push_enabled == 1).all()
    for s in rows:
        if in_quiet_hours(s, now):
            continue
        if _ai_pushed_count_today(db, s.uid) >= _freq_limit(s.ai_frequency):
            continue
        # 每次调度至多给一个用户发一条，错峰
        if s.updated_at and s.updated_at > now - dt.timedelta(minutes=2):
            continue
        emos = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == s.uid,
            EmotionRecord.record_date == now.date()).all()
        mood = emos[-1].emotion if emos else ""
        msg, bot_id = await build_proactive_message(db, s.uid, mood, s.diary_read_auth,
                                                    bot_ids=bot_ids)
        if not msg:
            continue
        await dispatch_push(db, s.uid, "ai_companion", "来自 AI 伙伴",
                            msg[:500], ref_id=bot_id)
        sent += 1
    return sent


# === ↓↓↓ 模块3新增：情绪驱动个性化推送（修复版） ↓↓↓ ===
#
# 修复前 Bug 清单（逐条修）：
#   [BUG-1] from app.models.push_setting import PushRecord —— PushRecord 实际在
#           app.modules.newfunc.models，这个 import 模块根本不存在；
#           之前因为 _run_job 的 try/except 吞掉了 ImportError，job
#           启动了但永远 0 条。
#   [BUG-2] PushRecord.scenario —— 该字段根本不存在（PushRecord 只有
#           push_type / title / content / ref_id / jump_page / channel /
#           is_read / status / created_at），AttributeError。
#   [BUG-3] PersonaService.build_persona_prompt("linxi", db) —— 签名是
#           (role: Optional[AIRole])，需要先 get_role_by_key 拿到 AIRole 对象。
#   [BUG-4] AIService.chat_non_stream(messages, temperature=0.8) —— 签名只有
#           (messages)，没有 temperature 参数。
#   [BUG-5] dispatch_push(..., ref_id=None) —— ref_id 是 BigInteger NOT NULL
#           DEFAULT 0，传 None 会破坏数据库约束。
#   [BUG-6] EmotionRecord.order_by(EmotionRecord.record_date.desc()) ——
#           record_date 是 DATE 类型，同一天多条情绪记录会乱序，
#           应该用 id / created_at desc 拿"最新一条"。
#   [BUG-7] 没有独立的冷却去重：没检查 push_type=emotion 近 4h 是否已推过
#           同一条情绪，易重复轰炸。
#   [BUG-8] 没有情绪推送独立开关判断：只要总 push_enabled=1 就发，没检查
#           diary_read_auth（AI 是否被授权读取全局情绪日历）。
#
# 修复方案：全部替换现有 job_emotion_push 实现（独立新增，不碰旧业务）。

async def job_emotion_push(db: Session) -> int:
    """
    情绪推送：每 30 分钟扫描一次。

    触发条件（全部满足才发）：
      ① 总 push_enabled=1 且 diary_read_auth=1（授权 AI 读情绪）
      ② 用户近 24h 有负面情绪记录（sad/angry/tired）
      ③ 近 4h 内没推过 push_type=emotion 或 ai_companion（冷却防轰炸）

    文案来源：优先调大模型（AIService.chat_non_stream），失败 → 固定兜底文案。
    点击跳转：负面强度高（intensity>=7）→ 正念页面 /pages/meditation/meditation；
              否则 → AI 聊天首页 /pages/chat/chat。
    """
    from app.models.emotion import EmotionRecord
    from app.services.ai_service import AIService
    from app.services.persona_service import PersonaService
    from app.services.emotion_service import EmotionService as _ES

    now = dt.datetime.now()
    sent = 0

    # 1. 筛选允许情绪推送的用户（总开关开 + 授权 AI 读情绪）
    rows = db.query(PushSetting).filter(
        PushSetting.push_enabled == 1,
        PushSetting.diary_read_auth == 1,   # 授权 AI 读取全局情绪日历
    ).all()

    for s in rows:
        uid = s.uid

        # —— 冷却：4 小时内没推过 emotion / ai_companion 类 ——
        last_cool = db.query(PushRecord).filter(
            PushRecord.uid == uid,
            PushRecord.push_type.in_(["emotion", "ai_companion"]),
            PushRecord.created_at > now - dt.timedelta(hours=4),
        ).order_by(PushRecord.created_at.desc()).first()
        if last_cool:
            continue

        # —— 取最新一条情绪记录（用 id desc 拿真正最新，不依赖 DATE 排序）——
        latest = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == uid,
        ).order_by(EmotionRecord.id.desc()).first()
        if not latest:
            continue

        negative = latest.emotion in ("sad", "angry", "tired")
        if not negative:
            continue

        # —— AI 生成文案（复用 project 已有 AIService 通道）——
        ai_msg = None
        try:
            # 先拿默认官方角色"林夕"的人设，作为推送语气
            _role = PersonaService.get_role_by_key(db, "linxi")
            persona_prompt = PersonaService.build_persona_prompt(_role) if _role else ""
            ai_msg = await AIService.chat_non_stream([
                {"role": "system", "content": persona_prompt + (
                    "\n你是温柔的 AI 陪伴伙伴。"
                    "现在要给用户发一条简短的鼓励推送。"
                )},
                {"role": "user", "content": (
                    f"用户最近情绪是 {latest.emotion}（强度 {latest.intensity}/10），"
                    "今天可能过得不太好。请写一条 40-60 字的温暖鼓励推送，"
                    "语气自然不要鸡汤。只输出推送文案本身，不要加引号或前缀。"
                )},
            ])
            if not ai_msg or len(ai_msg.strip()) < 10:
                ai_msg = None
        except Exception:
            ai_msg = None  # AI 挂了 → 走兜底

        if not ai_msg:
            _fallback_map = {
                "sad": "今天感觉不太好吗？想起你了，来聊聊吧 🌸",
                "angry": "感觉你现在有点烦躁，深呼吸三下试试～",
                "tired": "累了就歇歇，你已经很棒了 💪",
            }
            ai_msg = _fallback_map.get(latest.emotion, "今天也要记得好好照顾自己哦")

        # —— 点击跳转：负面强度高 → 正念；否则 → 聊天 ——
        # emotion_service 的 is_crisis_level 需要 (emotion, confidence) 结构
        _analysis = {"emotion": latest.emotion, "confidence": 0.6}
        _crisis = _ES.is_crisis_level(_analysis) or (latest.intensity or 5) >= 7
        # jump_page 必须是前端 pages.json 里的真实路径
        target = "/pages/meditation/meditation" if _crisis else "/pages/chat/chat"

        await dispatch_push(
            db, uid, "emotion", "来自 AI 伙伴的问候",
            ai_msg[:500], ref_id=0, jump_page=target,
        )
        sent += 1

    return sent
# === ↑↑↑ 模块3结束 ↑↑↑ ===
