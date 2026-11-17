# -*- coding: utf-8 -*-
"""
陪伴模式 API - 开启/结束/记录列表
前端对应: frontend/api/companion.js (USE_MOCK=false 时走本模块)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.companion import CompanionRecord
from app.schemas.common import ResponseBase
from app.schemas.companion import CompanionStartRequest, CompanionEndRequest

router = APIRouter(prefix="/companion", tags=["陪伴模式"])


@router.post("/start")
def start_companion(req: CompanionStartRequest,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """开始陪伴: 同一用户同一时刻仅允许一条进行中的记录"""
    # 兜底: 若存在未结束的陪伴记录, 先按当前时间静默结束
    active = db.query(CompanionRecord).filter(
        CompanionRecord.user_id == user_id,
        CompanionRecord.status == 1,
    ).first()
    if active:
        now = datetime.now()
        active.status = 0
        active.end_time = now
        active.duration_min = max(1, int((now - active.start_time).total_seconds() // 60)) if active.start_time else 0
        db.commit()

    # ↓↓↓ 新增（BUG-001）：校验 role_id，非法或不存在的角色回退到默认角色 ↓↓↓
    # 目的：即使旧客户端传来字符串角色标识（已被 schema 归一为 0）或已下架的角色，
    #       也保证陪伴记录能正常写入，不再出现「进了陪伴页但库里没记录」。
    from app.models.chat import AIRole

    role_id = req.role_id or 0
    if role_id > 0:
        exists = db.query(AIRole.id).filter(
            AIRole.id == role_id, AIRole.status == 1
        ).first()
        if not exists:
            role_id = 0
    if role_id <= 0:
        default_role = db.query(AIRole).filter(AIRole.status == 1).order_by(
            AIRole.sort_order.asc(), AIRole.id.asc()
        ).first()
        role_id = default_role.id if default_role else 1
    # ↑↑↑ 新增结束 ↑↑↑

    # ↓↓↓ 新增（20 个具名角色）：角色标识 + 名字快照 ↓↓↓
    # 陪伴的主角由 role_key 决定；role_id 仅作兼容保留（世界模块与历史数据仍在用 ai_roles）
    role_key = (req.role_key or "").strip() or "linxi"
    role_name = (req.role_name or "").strip()
    # ↑↑↑ 新增结束 ↑↑↑

    record = CompanionRecord(
        user_id=user_id,
        role_id=role_id,
        # ↓↓↓ 新增 ↓↓↓
        role_key=role_key,
        role_name=role_name,
        # ↑↑↑ 新增结束 ↑↑↑
        scene_type=req.scene_type,
        scene_name=req.scene_name,
        bg_img=req.bg_img,
        bg_sound=req.bg_sound,
        status=1,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ResponseBase.success(record.to_dict())


@router.post("/end")
def end_companion(req: CompanionEndRequest,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """结束陪伴: 置 status=0 并计算时长(分钟)"""
    record = db.query(CompanionRecord).filter(
        CompanionRecord.id == req.record_id,
        CompanionRecord.user_id == user_id,
    ).first()
    if not record:
        return ResponseBase.error("陪伴记录不存在", code=404)
    if record.status == 1:
        now = datetime.now()
        record.status = 0
        record.end_time = now
        if record.start_time:
            record.duration_min = max(
                1, int((now - record.start_time).total_seconds() // 60)
            )
        if req.remark:
            record.remark = req.remark
        db.commit()
        db.refresh(record)

    return ResponseBase.success({
        "id": record.id,
        "duration_min": record.duration_min,
        "end_time": str(record.end_time) if record.end_time else None,
    })


@router.get("/records")
def get_companion_records(page: int = 1, page_size: int = 20,
                          user_id: int = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """陪伴记录列表(倒序, 默认前20条; 与前端 mock companionRecords 返回结构一致)"""
    page = max(1, page)
    page_size = max(1, min(50, page_size))

    query = db.query(CompanionRecord).filter(CompanionRecord.user_id == user_id)
    total = query.count()
    records = query.order_by(CompanionRecord.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ResponseBase.success({
        "list": [r.to_dict() for r in records],
        "total": total,
        "page": page,
        "page_size": page_size,
    })
