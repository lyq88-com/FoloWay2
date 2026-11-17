# -*- coding: utf-8 -*-
"""
习惯-AI 联动 API - 打卡触发对话 / 成就 / 记忆 / 日记 / 自定义提醒
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.habit import Habit
from app.models.chat import AIUserMemory
from app.schemas.common import ResponseBase
from app.schemas.habit_ai import (
    CheckinTriggerRequest, CustomRemindRequest,
    DiaryGenerateRequest, MemoryWriteRequest,
)
from app.services.habit_ai_service import HabitAIService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/habit-ai", tags=["习惯AI联动"])


@router.post("/checkin-trigger")
def checkin_trigger(req: CheckinTriggerRequest,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """
    打卡成功后触发AI对话
    返回: AI对话文本 + 情绪标签 + 连续天数 + 成就(如有) + 日记
    """
    result = HabitAIService.process_checkin(
        db, user_id, req.habit_id, req.note, req.emotion, req.character_id
    )
    if "error" in result:
        return ResponseBase.error(result["error"], 404)
    return ResponseBase.success(result)


@router.get("/achievements")
def get_achievements(habit_id: int = Query(0, description="习惯ID(0=全部)"),
                     user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """获取用户成就列表"""
    achievements = HabitAIService.get_user_achievements(
        db, user_id, habit_id if habit_id else None
    )
    return ResponseBase.success(achievements)


@router.post("/memory")
def write_memory(req: MemoryWriteRequest,
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """写入AI记忆"""
    memory = HabitAIService.write_memory(
        db, user_id, req.memory_type, req.memory_content,
        habit_id=req.habit_id, emotion_id=req.emotion_id,
        emotion_score=req.emotion_score, habit_status=req.habit_status,
        is_long_term=req.is_long_term,
    )
    return ResponseBase.success({
        "id": memory.id,
        "memory_type": memory.memory_type,
        "created_at": str(memory.created_at),
    })


@router.get("/memories")
def get_memories(memory_type: str = Query("", description="记忆类型(空=全部)"),
                 limit: int = Query(20, ge=1, le=100),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """获取AI记忆列表(用于构建对话上下文)"""
    memories = HabitAIService.get_recent_memories(
        db, user_id, limit,
        memory_type if memory_type else None
    )
    return ResponseBase.success([{
        "id": m.id,
        "memory_type": m.memory_type,
        "memory_content": m.memory_content,
        "emotion_score": m.emotion_score,
        "habit_id": m.habit_id,
        "is_long_term": m.is_long_term,
        "created_at": str(m.created_at),
    } for m in memories])


@router.put("/custom-remind")
def update_custom_remind(req: CustomRemindRequest,
                         user_id: int = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """更新习惯的自定义AI提醒话术和对话风格"""
    habit = db.query(Habit).filter(
        Habit.id == req.habit_id, Habit.user_id == user_id
    ).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    habit.custom_remind_text = req.custom_remind_text
    habit.ai_style = req.ai_style
    db.commit()

    # 生成当前提醒话术预览
    preview = HabitAIService.generate_custom_reminder(habit, req.ai_style)

    return ResponseBase.success({
        "habit_id": habit.id,
        "custom_remind_text": habit.custom_remind_text,
        "ai_style": habit.ai_style,
        "preview_remind": preview,
    })


@router.post("/diary")
def generate_diary(req: DiaryGenerateRequest,
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """生成打卡日记"""
    habit = db.query(Habit).filter(
        Habit.id == req.habit_id, Habit.user_id == user_id
    ).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    target_date = None
    if req.date:
        try:
            target_date = date.fromisoformat(req.date)
        except ValueError:
            pass

    continuous_day = HabitAIService.calculate_continuous_days(
        db, user_id, req.habit_id
    )
    diary = HabitAIService.generate_checkin_diary(
        habit, continuous_day, req.emotion, req.note, target_date
    )
    return ResponseBase.success({
        "diary": diary,
        "continuous_day": continuous_day,
        "habit_name": habit.name,
    })


@router.get("/reminder")
def get_reminder(habit_id: int = Query(..., description="习惯ID"),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """获取AI提醒话术(用于定时提醒)"""
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == user_id
    ).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    reminder = HabitAIService.generate_custom_reminder(habit, habit.ai_style)
    return ResponseBase.success({
        "habit_id": habit.id,
        "habit_name": habit.name,
        "reminder_text": reminder,
        "ai_style": habit.ai_style,
        "custom_remind_text": habit.custom_remind_text,
    })
