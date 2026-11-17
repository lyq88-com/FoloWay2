# -*- coding: utf-8 -*-
"""
性格测评 API - 云端版(替换纯 localStorage 的本地方案)

接口:
  GET    /personality/result           取当前生效的测评结果(未测返回 completed=false)
  POST   /personality/result           保存/重测(写入新记录, 旧记录自动转历史)
  GET    /personality/history          测评历史(最近 N 条)
  DELETE /personality/result           重置(当前生效记录转历史)

约定:
  - 请求/响应都用前端同款 camelCase 字段名(emotionalResilience / companionStyle / rawScores)
    同时兼容 snake_case(别名), 便于后台/脚本调用
  - 单生效位: 保存前先将该用户 is_active=1 的行全部置 0, 再插入新的 is_active=1
"""
import json
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.personality import UserPersonalityResult
from app.schemas.common import ResponseBase
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/personality", tags=["性格测评"])

# 合法枚举值(仅做兜底校验, 前端题库改动时需同步)
ALLOWED = {
    "personality": {"anxious", "perfect", "procrastinator", "buddha"},
    "emotionalResilience": {"low", "medium", "high"},
    "procrastination": {"low", "medium", "high"},
    "companionStyle": {"warm", "smart", "energetic", "creative"},
}


class PersonalitySaveReq(BaseModel):
    """保存测评结果(兼容 camelCase 与 snake_case)"""
    model_config = ConfigDict(populate_by_name=True)

    personality: str = Field("", max_length=20)
    emotional_resilience: str = Field("", alias="emotionalResilience", max_length=20)
    procrastination: str = Field("", max_length=20)
    companion_style: str = Field("", alias="companionStyle", max_length=20)
    raw_scores: Optional[Dict[str, Any]] = Field(None, alias="rawScores")
    answers: Optional[List[Any]] = Field(None)
    quiz_version: str = Field("v1", alias="quizVersion", max_length=20)
    source: str = Field("app", max_length=20)


def _dump(value) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return None


def _load(text, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _to_dict(row: UserPersonalityResult) -> dict:
    """ORM 行 -> 前端同款结构"""
    return {
        "id": row.id,
        "personality": row.personality,
        "emotionalResilience": row.emotional_resilience,
        "procrastination": row.procrastination,
        "companionStyle": row.companion_style,
        "rawScores": _load(row.raw_scores, None),
        "answers": _load(row.answers, None),
        "quizVersion": row.quiz_version,
        "source": row.source,
        "isActive": row.is_active,
        "updatedAt": str(row.updated_at) if row.updated_at else "",
        "createdAt": str(row.created_at) if row.created_at else "",
    }


def _validate(req: PersonalitySaveReq) -> Optional[str]:
    pairs = [
        ("personality", req.personality),
        ("emotionalResilience", req.emotional_resilience),
        ("procrastination", req.procrastination),
        ("companionStyle", req.companion_style),
    ]
    for key, val in pairs:
        if val and val not in ALLOWED[key]:
            return f"字段 {key} 取值非法: {val}"
    return None


@router.get("/result")
def get_result(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前生效的测评结果"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端测评结果", 403)
    row = (
        db.query(UserPersonalityResult)
        .filter(UserPersonalityResult.user_id == user_id,
                UserPersonalityResult.is_active == 1)
        .order_by(UserPersonalityResult.id.desc())
        .first()
    )
    if not row:
        return ResponseBase.success({"completed": False, "result": None})
    return ResponseBase.success({
        "completed": True,
        "result": _to_dict(row),
    })


@router.post("/result")
def save_result(req: PersonalitySaveReq, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """保存/重测: 旧结果自动转历史, 新结果置为生效"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端保存", 403)

    err = _validate(req)
    if err:
        return ResponseBase.error(err, 400)
    if not req.personality:
        return ResponseBase.error("personality 不能为空", 400)

    # 1. 旧结果转历史(单生效位)
    db.query(UserPersonalityResult).filter(
        UserPersonalityResult.user_id == user_id,
        UserPersonalityResult.is_active == 1,
    ).update({UserPersonalityResult.is_active: 0}, synchronize_session=False)

    # 2. 写入新结果
    row = UserPersonalityResult(
        user_id=user_id,
        personality=req.personality,
        emotional_resilience=req.emotional_resilience,
        procrastination=req.procrastination,
        companion_style=req.companion_style,
        raw_scores=_dump(req.raw_scores),
        answers=_dump(req.answers),
        quiz_version=req.quiz_version or "v1",
        source=req.source or "app",
        is_active=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseBase.success(_to_dict(row), "已保存到云端")


@router.get("/history")
def get_history(limit: int = Query(20, ge=1, le=100),
                user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """测评历史(按时间倒序)"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端测评结果", 403)
    rows = (
        db.query(UserPersonalityResult)
        .filter(UserPersonalityResult.user_id == user_id)
        .order_by(UserPersonalityResult.id.desc())
        .limit(limit)
        .all()
    )
    return ResponseBase.success({
        "total": len(rows),
        "list": [_to_dict(r) for r in rows],
    })


@router.delete("/result")
def reset_result(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """重置测评: 当前生效记录转历史(不物理删除, 保留审计轨迹)"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端重置", 403)
    n = db.query(UserPersonalityResult).filter(
        UserPersonalityResult.user_id == user_id,
        UserPersonalityResult.is_active == 1,
    ).update({UserPersonalityResult.is_active: 0}, synchronize_session=False)
    db.commit()
    return ResponseBase.success({"removed": n}, "已重置云端测评结果")
