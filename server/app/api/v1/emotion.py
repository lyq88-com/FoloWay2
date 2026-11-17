# -*- coding: utf-8 -*-
"""
情绪记录 API - CRUD + 补录 + 趋势分析
"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.emotion import EmotionRecord
from app.schemas.common import ResponseBase
from app.schemas.emotion import EmotionRecordCreate
from app.services.emotion_service import EmotionService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/emotion", tags=["情绪记录"])


@router.post("/create")
def create_emotion(req: EmotionRecordCreate, user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """创建情绪记录(支持补录)"""
    record_date = date.today()
    if req.record_date:
        try:
            record_date = date.fromisoformat(req.record_date)
            # 限制补录范围(1年内)
            if (date.today() - record_date).days > 365:
                return ResponseBase.error("只能补录一年内的记录", 400)
        except ValueError:
            return ResponseBase.error("日期格式错误", 400)

    record = EmotionRecord(
        user_id=user_id,
        habit_id=req.habit_id,
        emotion=req.emotion,
        intensity=req.intensity,
        tags=json.dumps(req.tags, ensure_ascii=False) if req.tags else None,
        description=req.description,
        record_date=record_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ResponseBase.success({
        "id": record.id, "emotion": record.emotion,
        "intensity": record.intensity, "record_date": str(record.record_date),
    })


@router.get("/list")
def get_emotions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取情绪记录列表"""
    query = db.query(EmotionRecord).filter(EmotionRecord.user_id == user_id)
    total = query.count()
    records = query.order_by(desc(EmotionRecord.record_date)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ResponseBase.success({
        "list": [{
            "id": r.id, "habit_id": r.habit_id, "emotion": r.emotion,
            "intensity": r.intensity,
            "tags": json.loads(r.tags) if r.tags else [],
            "description": r.description,
            "record_date": str(r.record_date),
            "created_at": str(r.created_at),
        } for r in records],
        "total": total, "page": page, "page_size": page_size,
    })


@router.get("/trend")
def get_trend(period: str = Query("7d"), user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """情绪趋势分析"""
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)

    start_date = date.today() - timedelta(days=days - 1)
    records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start_date,
    ).order_by(EmotionRecord.record_date).all()

    record_list = [{
        "record_date": str(r.record_date),
        "emotion": r.emotion,
        "intensity": r.intensity,
        "tags": json.loads(r.tags) if r.tags else [],
    } for r in records]

    trend = EmotionService.get_emotion_trend(record_list, days)
    return ResponseBase.success(trend)


@router.get("/distribution")
def get_distribution(period: str = Query("30d"), user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """情绪分布统计"""
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


@router.get("/triggers")
def get_triggers(period: str = Query("30d"), user_id: int = Depends(get_current_user),
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
        "emotion": r.emotion,
        "intensity": r.intensity,
        "tags": json.loads(r.tags) if r.tags else [],
    } for r in records]

    analysis = EmotionService.get_trigger_analysis(record_list)
    return ResponseBase.success(analysis)


@router.delete("/delete/{record_id}")
def delete_emotion(record_id: int, user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """删除情绪记录"""
    record = db.query(EmotionRecord).filter(
        EmotionRecord.id == record_id, EmotionRecord.user_id == user_id
    ).first()
    if not record:
        return ResponseBase.error("记录不存在", 404)
    db.delete(record)
    db.commit()
    return ResponseBase.success({"id": record_id})
