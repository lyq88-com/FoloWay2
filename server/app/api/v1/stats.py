# -*- coding: utf-8 -*-
"""
统计分析 API - 情绪趋势 + 习惯关联 + 报告导出 + 周/月/习惯聚合
"""
import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.companion import CompanionRecord
from app.models.emotion import EmotionRecord
from app.models.habit import Habit, Checkin, CheckinItem
from app.models.mindfulness import MindfulnessSession
from app.schemas.common import ResponseBase
from app.services.emotion_service import EmotionService
from app.middleware.auth import get_current_user
# 【习惯-伙伴融合】陪伴向复盘（禁止打分 / 完成率 / 排名）
from app.services.habit_companion_service import HabitCompanionService as HCS

router = APIRouter(prefix="/stats", tags=["统计分析"])


def _as_date(v):
    """把 MySQL DATE() 的返回值统一成 date（兼容驱动返回 str 的情况）"""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _streak_from_dates(checkin_dates_desc):
    """连续打卡天数（基于 Checkin.checkin_date，补卡场景 created_at 会错）"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    if not checkin_dates_desc:
        return 0
    cursor = today if checkin_dates_desc[0] == today else yesterday
    streak = 0
    for d in checkin_dates_desc:
        if d == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif d < cursor:
            break
    return streak


@router.get("/summary")
def get_summary(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """统计概览"""
    today = date.today()
    total_emotions = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).count()

    today_checkin = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.checkin_date == today
    ).first()

    total_mindfulness = db.query(MindfulnessSession).filter(
        MindfulnessSession.user_id == user_id
    ).count()

    # 累计打卡次数（所有历史 Checkin 的完成数之和）
    total_checkins = db.query(Checkin).filter(
        Checkin.user_id == user_id
    ).with_entities(Checkin.completed_count).all()
    total_checkins = sum((r[0] or 0) for r in total_checkins)

    # 连续打卡天数（复用与周/月统计一致的日期算法）
    # 【修复】只统计真正完成过打卡的日期，避免历史空记录（completed_count=0）
    # 把连续天数虚增
    checkin_dates = [r[0] for r in db.query(Checkin.checkin_date).filter(
        Checkin.user_id == user_id, Checkin.completed_count > 0
    ).order_by(Checkin.checkin_date.desc()).all()]
    streak_days = _streak_from_dates(checkin_dates)

    # 连续陪伴天数（方案 A）：以 companion_records.start_time 的「日期」去重，
    # 只统计真正开启过陪伴的日期，不再借用打卡连续天数
    companion_rows = db.query(
        func.date(CompanionRecord.start_time)
    ).filter(
        CompanionRecord.user_id == user_id
    ).distinct().order_by(func.date(CompanionRecord.start_time).desc()).all()
    companion_dates = [d for d in (_as_date(r[0]) for r in companion_rows) if d]
    companion_days = _streak_from_dates(companion_dates)

    # 当前生效习惯总数
    total_habits = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    ).count()

    today_completed = today_checkin.completed_count if today_checkin else 0
    # 【修复】分母改用「当前生效习惯数」的实时值：
    # 1) 今天还没打卡时回落到总习惯数，避免首页一直显示 0/0
    # 2) 打卡后又新增习惯时分母同步变大，不会卡在打卡当时的旧快照
    # 3) 分子不超过分母，删除习惯后也不会出现 3/2 的越界完成率
    today_total = max(total_habits, today_completed)
    today_completed = min(today_completed, today_total)
    today_rate = round(today_completed * 100.0 / today_total, 1) if today_total else 0

    return ResponseBase.success({
        # 下划线字段：保留给已有调用方，不做破坏性改动
        "total_emotions": total_emotions,
        "today_completed": today_completed,
        "today_total": today_total,
        "today_rate": today_rate,
        "total_mindfulness": total_mindfulness,
        # 驼峰字段：首页 / 统计页读取的字段（此前缺失导致全部显示 0）
        "todayCompleted": today_completed,
        "todayTotal": today_total,
        "completionRate": today_rate,
        "streakDays": streak_days,
        "totalCheckins": total_checkins,
        "totalHabits": total_habits,
        # 新增（只加不改）：真实陪伴连续天数，首页「连续陪伴·天」改读此字段
        "companionDays": companion_days,
    })


@router.get("/emotion/trend")
def get_emotion_trend(period: str = Query("7d"),
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """情绪趋势"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)

    start_date = date.today() - timedelta(days=days - 1)
    records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start_date,
    ).order_by(EmotionRecord.record_date).all()

    record_list = [{
        "record_date": str(r.record_date), "emotion": r.emotion,
        "intensity": r.intensity, "tags": json.loads(r.tags) if r.tags else [],
    } for r in records]

    trend = EmotionService.get_emotion_trend(record_list, days)
    return ResponseBase.success(trend)


@router.get("/emotion/distribution")
def get_emotion_distribution(period: str = Query("30d"),
                             user_id: int = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    """情绪分布"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)

    start_date = date.today() - timedelta(days=days - 1)
    records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start_date,
    ).all()

    distribution = {}
    for r in records:
        distribution[r.emotion] = distribution.get(r.emotion, 0) + 1

    total = len(records)
    result = [{
        "emotion": emo,
        "label": EmotionService.EMOTION_LABELS.get(emo, emo),
        "count": count,
        "ratio": round(count / max(total, 1) * 100, 1),
    } for emo, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)]

    return ResponseBase.success({"distribution": result, "total": total})


@router.get("/emotion/triggers")
def get_triggers(period: str = Query("30d"),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """触发因素分析"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)

    start_date = date.today() - timedelta(days=days - 1)
    records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start_date,
    ).all()

    record_list = [{
        "emotion": r.emotion, "intensity": r.intensity,
        "tags": json.loads(r.tags) if r.tags else [],
    } for r in records]

    analysis = EmotionService.get_trigger_analysis(record_list)
    return ResponseBase.success(analysis)


@router.get("/emotion/habit-correlation")
def get_habit_correlation(period: str = Query("30d"),
                          user_id: int = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """习惯打卡与情绪关联"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)

    start_date = date.today() - timedelta(days=days - 1)

    emotion_records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start_date,
    ).all()

    checkin_records = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id,
        CheckinItem.created_at >= start_date,
    ).all()

    habit_map = {
        h.id: h for h in db.query(Habit).filter(
            Habit.user_id == user_id,
        ).all()
    }

    emotion_list = [{
        "record_date": str(r.record_date), "emotion": r.emotion,
        "intensity": r.intensity,
    } for r in emotion_records]

    # ↓↓↓ 修复 ↓↓↓ 原来只返回一个 {success_top, fail_top, ...} 摘要对象，
    # 前端 habit-emotion-heatmap 要的是「每个习惯一行」的数组，拿到对象 → 永远「暂无数据」。
    # 这里改用 EmotionService.get_habit_emotion_correlations（新增，原函数保留未动）。
    checkin_list = []
    for c in checkin_records:
        habit = habit_map.get(c.habit_id)
        # 补卡场景下 created_at 会错，优先取主表的 checkin_date
        if c.checkin and c.checkin.checkin_date:
            d = str(c.checkin.checkin_date)
        elif c.created_at:
            d = str(c.created_at.date())
        else:
            d = ""
        checkin_list.append({
            "habit_id": c.habit_id,
            "habit_name": habit.name if habit else "习惯",
            "habit_icon": habit.icon if habit else "checkmark",
            "checkin_date": d,
            "completed": c.completed,
        })

    correlations = EmotionService.get_habit_emotion_correlations(emotion_list, checkin_list)
    return ResponseBase.success(correlations)


@router.get("/habit/trend")
def get_habit_trend(period: str = Query("7d"),
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """习惯打卡趋势"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)

    labels = []
    completed = []
    rates = []

    today = date.today()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%Y-%m-%d"))
        checkin = db.query(Checkin).filter(
            Checkin.user_id == user_id, Checkin.checkin_date == d
        ).first()
        if checkin:
            completed.append(checkin.completed_count)
            rates.append(float(checkin.completion_rate))
        else:
            completed.append(0)
            rates.append(0)

    return ResponseBase.success({
        "labels": labels, "completed": completed, "rates": rates,
    })


@router.get("/week")
def stats_week(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """返回本周每日打卡数组 [{date, completed, rate}]"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    result = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        checkin = db.query(Checkin).filter(
            Checkin.user_id == user_id, Checkin.checkin_date == d
        ).first()
        completed = checkin.completed_count if checkin else 0
        total = checkin.total_habits if checkin else 0
        rate = round(completed / total * 100, 2) if total else 0.0
        result.append({"date": str(d), "completed": completed, "rate": rate})
    return ResponseBase.success(result)


@router.get("/month")
def stats_month(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """返回本月每日打卡数组 [{date, completed, rate}]"""
    today = date.today()
    month_start = today - timedelta(days=29)
    result = []
    for i in range(30):
        d = month_start + timedelta(days=i)
        checkin = db.query(Checkin).filter(
            Checkin.user_id == user_id, Checkin.checkin_date == d
        ).first()
        completed = checkin.completed_count if checkin else 0
        total = checkin.total_habits if checkin else 0
        rate = round(completed / total * 100, 2) if total else 0.0
        result.append({"date": str(d), "completed": completed, "rate": rate})
    return ResponseBase.success(result)


@router.get("/year")
def stats_year(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """返回今年 1 月至今的月度打卡数组 [{date:'YYYY-MM', completed, total, rate}]"""
    today = date.today()
    result = []
    for m in range(1, 13):
        start = date(today.year, m, 1)
        if m == 12:
            end = date(today.year, 12, 31)
        else:
            end = date(today.year, m + 1, 1) - timedelta(days=1)
        if start > today:
            # 未来月份补 0，保证图表 12 根柱子稳定
            result.append({"date": f"{today.year}-{m:02d}", "completed": 0, "total": 0, "rate": 0.0})
            continue
        rows = db.query(Checkin).filter(
            Checkin.user_id == user_id,
            Checkin.checkin_date >= start,
            Checkin.checkin_date <= end,
        ).all()
        completed = sum((r.completed_count or 0) for r in rows)
        total = sum((r.total_habits or 0) for r in rows)
        rate = round(completed / total * 100, 2) if total else 0.0
        result.append({
            "date": f"{today.year}-{m:02d}",
            "completed": completed,
            "total": total,
            "rate": rate,
        })
    return ResponseBase.success(result)


@router.get("/habits")
def stats_habits(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """返回各习惯统计数组 [{id, name, icon, color, streak, rate, totalCheckins}]"""
    habits = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == 1).all()
    today = date.today()
    month_ago = today - timedelta(days=29)

    result = []
    for h in habits:
        items = db.query(CheckinItem).filter(
            CheckinItem.user_id == user_id, CheckinItem.habit_id == h.id,
            CheckinItem.completed == 1
        ).join(Checkin, Checkin.id == CheckinItem.checkin_id).all()
        checkin_dates = sorted({item.checkin.checkin_date for item in items}, reverse=True)
        streak = _streak_from_dates(checkin_dates)
        total_checkins = len(items)
        # 近 30 天完成率
        recent_count = sum(1 for d in checkin_dates if d >= month_ago)
        rate = round(recent_count / 30 * 100, 2)
        result.append({
            "id": h.id, "name": h.name, "icon": h.icon, "color": h.color,
            "streak": streak, "rate": rate, "totalCheckins": total_checkins,
            # ↓↓↓ 习惯-伙伴融合 ↓↓↓
            "is_paused": bool(h.is_paused),
            "resume_count": int(h.resume_count or 0),
        })
    return ResponseBase.success(result)


@router.get("/companion-review")
def companion_review(days: int = Query(30, description="回看天数 7/30/90"),
                     user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    AI 伙伴视角的复盘文本（P1-4）

    只输出陪伴向解读：讲一起走过的事、讲你停下来又捡起来的那些次。
    禁止：打分、完成率、排名、和别人比较。
    """
    days = max(1, min(days, 365))
    return ResponseBase.success(HCS.build_companion_review(db, user_id, days=days))
