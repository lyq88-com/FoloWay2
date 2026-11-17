# -*- coding: utf-8 -*-
"""
情绪日记日历联动（newfunc · 模块二）
- user_diary_mood：按日期聚合的情绪标签 / 日记 / 当日总结（新表，只写本表）
- 只读复用旧数据：emotion_records（情绪明细）、checkins（打卡）、schedules（待办）
- 支持手动总结与 AI 依据当日打卡+待办+情绪+日记自动生成总结
- 全局情绪日历读取授权（push_setting.diary_read_auth）供 AI 伙伴参考
"""
import datetime as dt
from typing import Dict

from sqlalchemy.orm import Session

from app.modules.newfunc.models import UserDiaryMood, PushSetting

MOOD_EMOJI = {
    "happy": "😄", "excited": "🤩", "calm": "😌",
    "sad": "😢", "angry": "😠", "tired": "😪",
}


def _parse_date(s: str) -> dt.date:
    return dt.datetime.strptime((s or "")[:10], "%Y-%m-%d").date()


def get_or_create_setting(db: Session, uid: int):
    row = db.query(PushSetting).filter(PushSetting.uid == uid).first()
    if not row:
        row = PushSetting(uid=uid)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _upsert_day(db: Session, uid: int, d: dt.date) -> UserDiaryMood:
    row = db.query(UserDiaryMood).filter(
        UserDiaryMood.uid == uid, UserDiaryMood.diary_date == d).first()
    if not row:
        row = UserDiaryMood(uid=uid, diary_date=d)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


# ============================================================
# 当日聚合（读：emotion_records 只读 + user_diary_mood 本表）
# ============================================================
def day_detail(db: Session, uid: int, date_str: str) -> Dict:
    from app.models.emotion import EmotionRecord
    d = _parse_date(date_str)
    emos = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == uid, EmotionRecord.record_date == d
    ).order_by(EmotionRecord.id.asc()).all()
    row = db.query(UserDiaryMood).filter(
        UserDiaryMood.uid == uid, UserDiaryMood.diary_date == d).first()
    return {
        "date": d.strftime("%Y-%m-%d"),
        "emotions": [{"id": e.id, "emotion": e.emotion,
                      "emoji": MOOD_EMOJI.get(e.emotion, "🙂"),
                      "intensity": e.intensity, "description": e.description,
                      "tags": e.tags or []} for e in emos],
        "diary": row.to_dict() if row else {
            "id": 0, "diary_date": d.strftime("%Y-%m-%d"), "mood_tags": [],
            "mood_score": 5, "diary_text": "", "summary": "",
            "summary_source": ""},
    }


def save_day(db: Session, uid: int, date_str: str, mood_tags=None,
             mood_score: int = None, diary_text: str = None) -> Dict:
    """保存情绪标签/心情分/日记（同一日期一条，重复保存即更新）"""
    d = _parse_date(date_str)
    row = _upsert_day(db, uid, d)
    if mood_tags is not None:
        row.mood_tags = [str(t)[:20] for t in mood_tags][:8]
    if mood_score is not None:
        row.mood_score = max(0, min(10, int(mood_score)))
    if diary_text is not None:
        row.diary_text = str(diary_text)[:5000]
    db.commit()
    return row.to_dict()


def save_summary(db: Session, uid: int, date_str: str, summary: str) -> Dict:
    d = _parse_date(date_str)
    row = _upsert_day(db, uid, d)
    row.summary = (summary or "").strip()[:1000]
    row.summary_source = "manual"
    db.commit()
    return row.to_dict()


# ============================================================
# AI 自动生成当日总结（只读旧数据）
# ============================================================
def _collect_day_context(db: Session, uid: int, d: dt.date) -> str:
    from app.models.habit import Checkin
    from app.models.schedule import Schedule
    from app.models.emotion import EmotionRecord
    parts = []
    ck = db.query(Checkin).filter(
        Checkin.user_id == uid, Checkin.checkin_date == d, Checkin.status == 1).first()
    if ck:
        parts.append(f"打卡：完成 {ck.completed_count}/{ck.total_habits} 个习惯，"
                     f"完成率 {float(ck.completion_rate or 0):.0f}%"
                     + (f"，用户自评：{ck.note}" if ck.note else ""))
    else:
        parts.append("打卡：今天没有打卡记录")
    scs = db.query(Schedule).filter(
        Schedule.schedule_date == d, Schedule.status == 1).all()
    if scs:
        done_titles = [x.title for x in scs if x.is_done][:5]
        todo_titles = [x.title for x in scs if not x.is_done][:5]
        parts.append(f"待办：共 {len(scs)} 项，完成 {sum(1 for x in scs if x.is_done)} 项"
                     + (f"，完成的有 {('、'.join(done_titles))}" if done_titles else "")
                     + (f"，未完成的有 {('、'.join(todo_titles))}" if todo_titles else ""))
    emos = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == uid, EmotionRecord.record_date == d).all()
    if emos:
        parts.append("情绪：" + "；".join(
            f"{e.emotion}({e.intensity}/10){('，' + e.description) if e.description else ''}"
            for e in emos[-5:]))
    row = db.query(UserDiaryMood).filter(
        UserDiaryMood.uid == uid, UserDiaryMood.diary_date == d).first()
    if row:
        if row.mood_tags:
            parts.append("日记心情标签：" + "、".join(row.mood_tags))
        if row.diary_text:
            parts.append("日记内容：" + row.diary_text[:300])
    return "\n".join(parts) if parts else "这一天没有任何记录"


async def generate_ai_summary(db: Session, uid: int, date_str: str) -> Dict:
    d = _parse_date(date_str)
    ctx = _collect_day_context(db, uid, d)
    from app.services.ai_service import AIService
    prompt = (
        "你是用户的私人成长伙伴。下面是用户某一天的真实记录，"
        "请写一段 60~100 字的当日总结：温柔、具体、不空喊口号，"
        "先肯定做到的，再温和提一句可以更好的点，结尾给一句贴合当天状态的话。"
        f"\n\n{ctx}\n\n直接输出总结正文，不要标题、不要列举序号。")
    summary = (await AIService.chat_non_stream(
        [{"role": "user", "content": prompt}])).strip()
    if not summary:
        summary = _fallback_summary(ctx)
    summary = summary[:1000]
    row = _upsert_day(db, uid, d)
    row.summary = summary
    row.summary_source = "ai"
    db.commit()
    return row.to_dict()


def _fallback_summary(ctx: str) -> str:
    """AI 不可用时的本地兜底总结"""
    if "完成率" in ctx or "完成 " in ctx:
        return ("今天你把一部分事情稳稳做完了，这已经比原地踏步好很多。"
                "没做完的别急着责怪自己，留到明天也是安排。早点休息，明天继续。")
    if "情绪" in ctx:
        return ("今天没有太多任务记录，但你认真记下了自己的情绪，这本身就是照顾自己的方式。"
                "给今天一个温柔的句号吧。")
    return "今天是安静的一天。没有记录不代表没有成长，好好休息，明天见。"


# ============================================================
# 月视图标记 + 授权
# ============================================================
def month_marks(db: Session, uid: int, month: str) -> Dict:
    """返回当月有情绪/日记/总结的日期标记，供日历圆点渲染"""
    from app.models.emotion import EmotionRecord
    y, m = month.split("-")[:2]
    first = dt.date(int(y), int(m), 1)
    last_day = (dt.date(int(y), int(m) % 12 + 1, 1) - dt.timedelta(days=1)) \
        if int(m) < 12 else dt.date(int(y), 12, 31)
    diaries = db.query(UserDiaryMood).filter(
        UserDiaryMood.uid == uid,
        UserDiaryMood.diary_date >= first,
        UserDiaryMood.diary_date <= last_day).all()
    emo_dates = [r[0] for r in db.query(EmotionRecord.record_date).filter(
        EmotionRecord.user_id == uid,
        EmotionRecord.record_date >= first,
        EmotionRecord.record_date <= last_day).distinct().all()]
    marks = {}
    for r in diaries:
        key = r.diary_date.strftime("%Y-%m-%d")
        marks.setdefault(key, {"has_emotion": 0, "has_diary": 0, "has_summary": 0})
        marks[key]["has_diary"] = 1
        if r.summary:
            marks[key]["has_summary"] = 1
    for d in emo_dates:
        key = d.strftime("%Y-%m-%d")
        marks.setdefault(key, {"has_emotion": 0, "has_diary": 0, "has_summary": 0})
        marks[key]["has_emotion"] = 1
    return {"month": month, "marks": marks}


def set_authorize(db: Session, uid: int, enabled: bool) -> Dict:
    """授权 AI 伙伴读取全局情绪日历数据（存 push_setting.diary_read_auth）"""
    s = get_or_create_setting(db, uid)
    s.diary_read_auth = 1 if enabled else 0
    db.commit()
    return {"diary_read_auth": bool(s.diary_read_auth)}
