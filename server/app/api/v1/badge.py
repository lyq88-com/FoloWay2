# -*- coding: utf-8 -*-
"""
徽章 API - 用户成就徽章
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.habit import CheckinItem
from app.models.mindfulness import MindfulnessSession
from app.models.emotion import EmotionRecord
from app.schemas.common import ResponseBase
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/badges", tags=["徽章"])


@router.get("/my")
def get_my_badges(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取我的徽章列表"""
    habit_checkins = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id, CheckinItem.completed == 1
    ).count()
    mindfulness_count = db.query(MindfulnessSession).filter(
        MindfulnessSession.user_id == user_id
    ).count()
    emotion_count = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).count()

    badges = [
        {"id": "habit_7", "name": "坚持一周", "icon": "🌟", "unlocked": habit_checkins >= 7,
         "description": "累计打卡7次"},
        {"id": "habit_30", "name": "坚持一月", "icon": "🏆", "unlocked": habit_checkins >= 30,
         "description": "累计打卡30次"},
        {"id": "habit_100", "name": "百日坚持", "icon": "💎", "unlocked": habit_checkins >= 100,
         "description": "累计打卡100次"},
        {"id": "mind_10", "name": "初探内心", "icon": "🧘", "unlocked": mindfulness_count >= 10,
         "description": "完成10次正念练习"},
        {"id": "mind_50", "name": "静心达人", "icon": "🌊", "unlocked": mindfulness_count >= 50,
         "description": "完成50次正念练习"},
        {"id": "emo_30", "name": "情绪观察者", "icon": "📓", "unlocked": emotion_count >= 30,
         "description": "记录30次情绪"},
    ]
    return ResponseBase.success(badges)
