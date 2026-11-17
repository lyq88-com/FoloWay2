# -*- coding: utf-8 -*-
"""
正念练习 API - 练习记录 + 计划 + 音频资源
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.mindfulness import MindfulnessSession, MindfulnessPlan, AudioResource
from app.schemas.common import ResponseBase
from app.schemas.mindfulness import MindfulnessSessionCreate, MindfulnessPlanCreate
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/mindfulness", tags=["正念练习"])


@router.get("/audio/list")
def get_audio_list(audio_type: str = Query(""), db: Session = Depends(get_db)):
    """获取音频资源列表"""
    query = db.query(AudioResource).filter(AudioResource.status == 1)
    if audio_type:
        query = query.filter(AudioResource.audio_type == audio_type)
    audios = query.order_by(AudioResource.sort_order).all()

    return ResponseBase.success([{
        "id": a.id, "title": a.title, "audio_type": a.audio_type,
        "duration_min": a.duration_min, "audio_url": a.audio_url,
        "cover_url": a.cover_url, "description": a.description or "",
        "narrator": a.narrator,
    } for a in audios])


@router.post("/session/create")
def create_session(req: MindfulnessSessionCreate,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """记录正念练习"""
    session = MindfulnessSession(
        user_id=user_id,
        session_type=req.session_type,
        duration_min=req.duration_min,
        audio_id=req.audio_id,
        emotion_before=req.emotion_before,
        emotion_after=req.emotion_after,
        intensity_before=req.intensity_before,
        intensity_after=req.intensity_after,
        completed=req.completed,
        session_date=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # ↓↓↓ 模块2 新增：正念结束后同步写 emotion_records（复用项目已有表，不建新表） ↓↓↓
    # 只有练习后选了情绪才写；原始音频不上传，只存情绪标签
    try:
        import pymysql, json
        from app.core.config import settings
        if req.emotion_after and req.emotion_after != req.emotion_before:
            _conn = pymysql.connect(
                host=settings.db_host, port=settings.db_port,
                user=settings.db_user, password=settings.db_password,
                database=settings.db_name, charset='utf8mb4'
            )
            _cur = _conn.cursor()
            _tags = json.dumps(["mindfulness", req.session_type or "meditation"], ensure_ascii=False)
            _desc = f"正念练习({req.duration_min}min)后情绪变化：{req.emotion_before} → {req.emotion_after}"
            _cur.execute(
                "INSERT INTO emotion_records (user_id, emotion, intensity, tags, description, record_date, habit_id) "
                "VALUES (%s, %s, %s, %s, %s, CURDATE(), 0)",
                (user_id, req.emotion_after or "calm",
                 req.intensity_after or 5, _tags, _desc[:200])
            )
            _conn.commit()
            _cur.close(); _conn.close()
    except Exception:
        # 情绪记录写入失败不影响正念练习记录，静默降级
        pass
    # ↑↑↑ 模块2 新增结束 ↑↑↑

    return ResponseBase.success({
        "id": session.id, "session_type": session.session_type,
        "duration_min": session.duration_min, "completed": session.completed,
        # ↓↓↓ 模块2 新增：把呼吸采集结果回传给前端（用于调试/展示） ↓↓↓
        "breath_rate": req.breath_rate,
        "breath_anomalies": req.breath_anomalies,
        # ↑↑↑ 模块2 新增结束 ↑↑↑
    })


@router.get("/session/list")
def get_sessions(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取练习记录列表"""
    query = db.query(MindfulnessSession).filter(MindfulnessSession.user_id == user_id)
    total = query.count()
    records = query.order_by(desc(MindfulnessSession.session_date)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ResponseBase.success({
        "list": [{
            "id": r.id, "session_type": r.session_type,
            "duration_min": r.duration_min, "audio_id": r.audio_id,
            "emotion_before": r.emotion_before, "emotion_after": r.emotion_after,
            "intensity_before": r.intensity_before, "intensity_after": r.intensity_after,
            "completed": r.completed, "session_date": str(r.session_date),
        } for r in records],
        "total": total, "page": page, "page_size": page_size,
    })


@router.post("/plan/create")
def create_plan(req: MindfulnessPlanCreate,
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """创建练习计划"""
    plan = MindfulnessPlan(
        user_id=user_id,
        plan_type=req.plan_type,
        session_type=req.session_type,
        reminder_time=req.reminder_time,
        week_days=req.week_days,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return ResponseBase.success({"id": plan.id, "plan_type": plan.plan_type})


@router.get("/plan/list")
def get_plans(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取练习计划列表"""
    plans = db.query(MindfulnessPlan).filter(
        MindfulnessPlan.user_id == user_id, MindfulnessPlan.active == 1
    ).all()

    return ResponseBase.success([{
        "id": p.id, "plan_type": p.plan_type, "session_type": p.session_type,
        "reminder_time": p.reminder_time, "week_days": p.week_days, "active": p.active,
    } for p in plans])


@router.put("/plan/toggle/{plan_id}")
def toggle_plan(plan_id: int, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """启用/停用计划"""
    plan = db.query(MindfulnessPlan).filter(
        MindfulnessPlan.id == plan_id, MindfulnessPlan.user_id == user_id
    ).first()
    if not plan:
        return ResponseBase.error("计划不存在", 404)
    plan.active = 0 if plan.active == 1 else 1
    db.commit()
    return ResponseBase.success({"id": plan.id, "active": plan.active})


@router.get("/audio/{audio_id}")
def get_audio_detail(audio_id: int, db: Session = Depends(get_db)):
    """获取音频详情（前端 getAudio 调用，stub）"""
    audio = db.query(AudioResource).filter(AudioResource.id == audio_id, AudioResource.status == 1).first()
    if not audio:
        return ResponseBase.error("音频不存在", 404)
    return ResponseBase.success({
        "id": audio.id, "title": audio.title, "audio_type": audio.audio_type,
        "duration_min": audio.duration_min, "audio_url": audio.audio_url,
        "cover_url": audio.cover_url, "description": audio.description or "",
        "narrator": audio.narrator,
    })


@router.get("/stats")
def get_stats(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """练习统计（前端 getStats 调用，stub）"""
    sessions = db.query(MindfulnessSession).filter(MindfulnessSession.user_id == user_id).all()
    total_min = sum(s.duration_min or 0 for s in sessions)
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.completed == 1)
    avg_duration = round(total_min / max(total_sessions, 1), 2)
    return ResponseBase.success({
        "total_minutes": total_min,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "streak_days": 0,
        "avg_duration": avg_duration,
        "category_stats": {},
    })


@router.get("/knowledge")
def get_knowledge(user_id: int = Depends(get_current_user)):
    """正念知识库（前端 getKnowledge 调用，stub）"""
    return ResponseBase.success([
        {"id": 1, "title": "什么是正念？", "summary": "正念是带着觉知活在当下", "content": ""},
        {"id": 2, "title": "呼吸的力量", "summary": "呼吸是连接身心的桥梁", "content": ""},
        {"id": 3, "title": "身体扫描", "summary": "从头顶到脚趾感受身体每一处", "content": ""},
    ])


@router.post("/guide")
def get_guide(data: dict = Body(...), user_id: int = Depends(get_current_user)):
    """AI 引导语（前端 getGuide 调用，stub）"""
    phase = data.get("phase", "start")
    guides = {
        "start": "深呼吸，慢慢放松身体，准备开始这段练习",
        "middle": "保持觉知，温柔地观察自己的呼吸",
        "end": "慢慢回到现实，给自己一个微笑",
    }
    next_phase = {"start": "middle", "middle": "end", "end": "done"}
    return ResponseBase.success({
        "guide_text": guides.get(phase, "保持呼吸的节奏"),
        "next_phase": next_phase.get(phase, "done"),
    })
