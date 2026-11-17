# -*- coding: utf-8 -*-
"""
活动 API - 每日签到 / 活跃任务
前端对应: frontend/pages/activity/activity.vue（原先是纯占位页）

设计要点
- 签到按「自然日」判定，同一天重复点只会返回已签到，不会重复发奖
- 连续天数断签即归 1；max_streak 只增不减
- 奖励只算「该发多少」，金币真正入账由前端 economy 模块执行（后端不碰 user_economy，
  避免与已有的经济读写逻辑打架）
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.activity import UserSignin
from app.models.habit import CheckinItem
from app.models.mindfulness import MindfulnessSession
from app.models.emotion import EmotionRecord
from app.schemas.common import ResponseBase

router = APIRouter(prefix="/activity", tags=["活动"])

# 基础奖励 + 连续里程碑
BASE_REWARD = 10
STREAK_BONUS = {3: 5, 7: 20, 14: 30, 30: 50}


def _reward_for(streak: int) -> int:
    """连续第 N 天签到能领多少金币"""
    bonus = 0
    for day, coin in STREAK_BONUS.items():
        if streak >= day:
            bonus = max(bonus, coin)
    return BASE_REWARD + bonus


def _load_or_create(db: Session, user_id: int) -> UserSignin:
    row = db.query(UserSignin).filter(UserSignin.user_id == user_id).first()
    if not row:
        row = UserSignin(user_id=user_id, streak=0, max_streak=0, total_days=0)
        db.add(row)
        db.flush()
    return row


@router.get("/signin")
def get_signin(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """签到状态（不写库，纯查询）"""
    row = db.query(UserSignin).filter(UserSignin.user_id == user_id).first()
    today = date.today()

    if not row or not row.last_date:
        return ResponseBase.success({
            "signed_today": False,
            "last_date": "",
            "streak": 0,
            "max_streak": (row.max_streak if row else 0),
            "total_days": (row.total_days if row else 0),
            "today_reward": _reward_for(1),
            "next_reward": _reward_for(1),
        })

    signed_today = (row.last_date == today)
    # 断签了：下次签到会重新从 1 开始
    effective_streak = (row.streak or 0) if (signed_today or row.last_date == today - timedelta(days=1)) else 0

    return ResponseBase.success({
        "signed_today": signed_today,
        "last_date": str(row.last_date),
        "streak": effective_streak,
        "max_streak": row.max_streak or 0,
        "total_days": row.total_days or 0,
        "today_reward": 0 if signed_today else _reward_for(effective_streak + 1),
        "next_reward": _reward_for(effective_streak + 1),
    })


@router.post("/signin")
def do_signin(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """签到：一天只会成功一次"""
    today = date.today()
    row = _load_or_create(db, user_id)

    if row.last_date == today:
        db.commit()
        return ResponseBase.success({
            "signed": False,
            "message": "今天已经签到过了，明天再来吧",
            "streak": row.streak or 0,
            "total_days": row.total_days or 0,
            "reward": 0,
        })

    # 连续判定：昨天签过就 +1，否则重新从 1 开始
    if row.last_date == today - timedelta(days=1):
        row.streak = (row.streak or 0) + 1
    else:
        row.streak = 1

    row.last_date = today
    row.total_days = (row.total_days or 0) + 1
    row.max_streak = max(row.max_streak or 0, row.streak)

    db.commit()
    db.refresh(row)

    return ResponseBase.success({
        "signed": True,
        "message": "签到成功",
        "streak": row.streak,
        "total_days": row.total_days,
        "max_streak": row.max_streak,
        "reward": _reward_for(row.streak),
    })


@router.get("/tasks")
def get_tasks(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """活跃任务进度（只读统计，不产生奖励）"""
    checkins = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id, CheckinItem.completed == 1
    ).count()
    mindfulness = db.query(MindfulnessSession).filter(
        MindfulnessSession.user_id == user_id
    ).count()
    emotions = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).count()

    def _task(tid, name, icon, cur, target, desc, reward):
        return {
            "id": tid, "name": name, "icon": icon,
            "current": cur, "target": target,
            "progress": 0 if target <= 0 else min(100, int(cur * 100 / target)),
            "done": cur >= target,
            "description": desc, "reward": reward,
        }

    tasks = [
        _task("checkin_7", "七日之约", "✅", checkins, 7, "累计完成 7 次习惯打卡", 20),
        _task("checkin_30", "月度坚持", "📅", checkins, 30, "累计完成 30 次习惯打卡", 60),
        _task("mind_5", "静心五练", "🧘", mindfulness, 5, "完成 5 次正念练习", 30),
        _task("emo_10", "情绪记录者", "📓", emotions, 10, "记录 10 次情绪", 20),
    ]

    return ResponseBase.success({
        "list": tasks,
        "total_reward": sum(t["reward"] for t in tasks if t["done"]),
    })
