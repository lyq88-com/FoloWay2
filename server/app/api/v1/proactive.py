# -*- coding: utf-8 -*-
"""
主动陪伴 API —— 陪伴感增强 v3
用户在打开会话时调用 /next，拿到一条「TA 主动说的话」。
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.services.proactive_service import ProactiveService

router = APIRouter(prefix="/proactive", tags=["主动陪伴"])


@router.get("/next")
async def next_proactive(role_key: str = Query(default="", description="角色标识"),
                         session_id: Optional[int] = Query(default=None),
                         fast: bool = Query(default=False, description="true=只用模板，不等大模型"),
                         user_id: int = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """取一条主动消息（没有值得主动说的就返回 data=null，前端不展示气泡）"""
    data = await ProactiveService.next_proactive(
        db, user_id, role_key, session_id, use_ai=not fast)
    return ResponseBase.success(data=data)


@router.get("/history")
def proactive_history(role_key: str = Query(default=""),
                      limit: int = Query(default=20, ge=1, le=100),
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """主动互动历史"""
    return ResponseBase.success(data=ProactiveService.history(db, user_id, role_key, limit))


@router.post("/{log_id}/read")
def mark_read(log_id: int, user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """标记已读"""
    from app.models.persona_ext import AIProactiveLog
    row = db.query(AIProactiveLog).filter(
        AIProactiveLog.id == log_id, AIProactiveLog.user_id == user_id
    ).first()
    if not row:
        return ResponseBase.error(message="记录不存在", code=404)
    row.is_read = 1
    db.commit()
    return ResponseBase.success(message="ok")
