# -*- coding: utf-8 -*-
"""
成长档案 API - 月/季/年报告 + 数据导出 + 加密
"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.archive import GrowthArchive, EmotionReport
from app.models.emotion import EmotionRecord
from app.models.habit import Checkin, CheckinItem
from app.models.mindfulness import MindfulnessSession
from app.schemas.common import ResponseBase
from app.services.archive_service import ArchiveService
from app.middleware.auth import get_current_user
# 【习惯-伙伴融合】月度陪伴向复盘（P2-1，只讲回忆，禁排名打分）
from app.services.habit_companion_service import HabitCompanionService as HCS

router = APIRouter(prefix="/archive", tags=["成长档案"])


@router.get("/report")
def get_report(period: str = Query("monthly"),
              user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """获取成长报告"""
    start, end = ArchiveService.get_period_range(period)

    # 查询数据
    emotion_records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.record_date >= start,
        EmotionRecord.record_date <= end,
    ).all()

    checkin_items = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id,
        CheckinItem.created_at >= start,
        CheckinItem.created_at <= end + timedelta(days=1),
    ).all()

    mindfulness_sessions = db.query(MindfulnessSession).filter(
        MindfulnessSession.user_id == user_id,
        MindfulnessSession.session_date >= start,
        MindfulnessSession.session_date <= end + timedelta(days=1),
    ).all()

    emotion_list = [{
        "emotion": r.emotion, "intensity": r.intensity,
        "tags": json.loads(r.tags) if r.tags else [],
    } for r in emotion_records]

    checkin_list = [{"completed": c.completed} for c in checkin_items]

    mindfulness_list = [{"duration_min": m.duration_min} for m in mindfulness_sessions]

    summary = ArchiveService.build_archive_summary(
        emotion_list, checkin_list, mindfulness_list, period
    )

    # 检查是否已有存档
    archive = db.query(GrowthArchive).filter(
        GrowthArchive.user_id == user_id,
        GrowthArchive.period_type == period,
        GrowthArchive.period_start == start,
    ).first()

    if archive:
        # 更新
        archive.summary = summary.get("summary", "")
        archive.highlights = summary.get("highlights", [])
        archive.suggestions = summary.get("suggestions", [])
        archive.emotion_trend = {
            "distribution": summary.get("emotion_distribution", {}),
            "avg_intensity": summary.get("avg_intensity", 0),
        }
        db.commit()
        db.refresh(archive)
    else:
        # 创建
        archive = GrowthArchive(
            user_id=user_id, period_type=period,
            period_start=start, period_end=end,
            summary=summary.get("summary", ""),
            highlights=summary.get("highlights", []),
            suggestions=summary.get("suggestions", []),
            emotion_trend={
                "distribution": summary.get("emotion_distribution", {}),
                "avg_intensity": summary.get("avg_intensity", 0),
            },
        )
        db.add(archive)
        db.commit()
        db.refresh(archive)

    return ResponseBase.success({
        "id": archive.id, "period": period,
        "period_start": str(archive.period_start),
        "period_end": str(archive.period_end),
        "summary": summary.get("summary", ""),
        "highlights": summary.get("highlights", []),
        "suggestions": summary.get("suggestions", []),
        "emotion_count": summary.get("emotion_count", 0),
        "emotion_distribution": summary.get("emotion_distribution", {}),
        "avg_intensity": summary.get("avg_intensity", 0),
        "checkin_count": summary.get("checkin_count", 0),
        "completed_count": summary.get("completed_count", 0),
        "completion_rate": summary.get("completion_rate", 0),
        "mindfulness_count": summary.get("mindfulness_count", 0),
        "total_meditation_min": summary.get("total_meditation_min", 0),
    })


@router.get("/export")
def export_data(format: str = Query("json"),
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """导出数据(JSON/CSV)"""
    emotions = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).all()

    checkins = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id
    ).all()

    mindfulness = db.query(MindfulnessSession).filter(
        MindfulnessSession.user_id == user_id
    ).all()

    data = {
        "emotions": [{
            "date": str(r.record_date), "emotion": r.emotion,
            "intensity": r.intensity,
            "tags": json.loads(r.tags) if r.tags else [],
            "description": r.description,
        } for r in emotions],
        "checkins": [{
            "date": str(c.created_at), "habit_id": c.habit_id,
            "completed": c.completed, "note": c.note or "",
        } for c in checkins],
        "mindfulness": [{
            "date": str(m.session_date), "type": m.session_type,
            "duration": m.duration_min, "completed": m.completed,
        } for m in mindfulness],
    }

    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "date", "field1", "field2", "field3"])
        for r in data["emotions"]:
            writer.writerow(["emotion", r["date"], r["emotion"], r["intensity"], r["description"]])
        for r in data["checkins"]:
            writer.writerow(["checkin", r["date"], r["habit_id"], r["completed"], r["note"]])
        for r in data["mindfulness"]:
            writer.writerow(["mindfulness", r["date"], r["type"], r["duration"], r["completed"]])
        return ResponseBase.success({"format": "csv", "data": output.getvalue()})
    else:
        return ResponseBase.success({"format": "json", "data": data})


@router.get("/list")
def get_archive_list(user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """获取档案列表"""
    archives = db.query(GrowthArchive).filter(
        GrowthArchive.user_id == user_id
    ).order_by(GrowthArchive.period_start.desc()).limit(20).all()

    return ResponseBase.success([{
        "id": a.id, "period_type": a.period_type,
        "period_start": str(a.period_start), "period_end": str(a.period_end),
        "summary": a.summary or "",
    } for a in archives])


@router.get("/monthly-companion")
def monthly_companion(year: int = Query(0, description="年份，0=今年"),
                      month: int = Query(0, description="月份 1-12，0=本月"),
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    月度陪伴向复盘报告（P2-1）

    只输出陪伴回忆：这个月我们一起走过的习惯、停下来的那几天、又捡起来的那次。
    禁止：排名、打分、完成率评判。
    """
    y = year or None
    m = month or None
    if m is not None and not (1 <= m <= 12):
        return ResponseBase.error("month 应在 1-12", 400)
    return ResponseBase.success(HCS.build_monthly_companion_review(db, user_id, y, m))


@router.get("/share")
def share_report(period: str = Query("monthly"),
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """生成分享文本（前端 archive.js shareReport 调用，stub）"""
    start, end = ArchiveService.get_period_range(period)
    return ResponseBase.success({
        "period": period,
        "share_text": f"我的 {period} 成长档案已生成，继续加油～",
        "period_start": str(start),
        "period_end": str(end),
    })
