# -*- coding: utf-8 -*-
"""
长效记忆 API —— 陪伴感增强 v3

- 记忆分层：profile 长期固定信息 / event 对话事件 / preference 偏好
- 记忆跟随角色：role_key 隔离，A 角色记住的内容不会串到 B 角色
- 用户可查看、单条删除、一键清空（软删除）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.schemas.memory import MemoryAddRequest, MemoryUpdateRequest, MemoryExtractRequest
from app.services.memory_service import MemoryService, to_dict, VALID_LAYERS
# 【习惯-伙伴融合】习惯生命周期事件记忆过滤
from app.services.habit_companion_service import HabitCompanionService as HCS

router = APIRouter(prefix="/memory", tags=["长效记忆"])


@router.get("/list")
def list_memories(role_key: str = Query(default="", description="角色标识，空=含共享记忆"),
                  layer: str = Query(default="", description="profile/event/preference，空=全部"),
                  page: int = Query(default=1, ge=1),
                  page_size: int = Query(default=50, ge=1, le=200),
                  # ↓↓↓ 习惯-伙伴融合（P2-2）：筛选习惯相关事件记忆 ↓↓↓
                  topic: str = Query(default="", description="主题过滤：habit=只要习惯生命周期事件；空=全部"),
                  habit_id: int = Query(default=0, description="只看某个习惯的记忆，0=不限"),
                  event: str = Query(default="", description="习惯事件过滤 habit_create/habit_checkin/habit_missed/habit_pause/habit_resume"),
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """记忆列表（分层查看 + 习惯事件过滤）"""
    if layer and layer not in VALID_LAYERS:
        return ResponseBase.error(message=f"layer 只能是 {'/'.join(VALID_LAYERS)}", code=400)

    # topic=habit → 走习惯生命周期记忆的专用过滤（支持 event / habit_id 细分）
    if topic == "habit":
        rows = HCS.list_habit_memories(
            db, user_id, habit_id=habit_id, event=event,
            role_key=role_key, limit=page_size,
        )
        total = len(rows)
        return ResponseBase.success(data={
            "list": [to_dict(m) for m in rows],
            "total": total,
            "page": 1,
            "page_size": page_size,
            "topic": topic,
            "habit_id": habit_id,
        })

    rows, total = MemoryService.list_memories(db, user_id, role_key, layer, page, page_size)
    return ResponseBase.success(data={
        "list": [to_dict(m) for m in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "topic": topic,
        "stats": MemoryService.stats(db, user_id, role_key),
    })


@router.get("/stats")
def memory_stats(role_key: str = Query(default=""),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """各层记忆数量"""
    return ResponseBase.success(data=MemoryService.stats(db, user_id, role_key))


@router.post("/add")
def add_memory(req: MemoryAddRequest, user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """手动添加一条记忆（用户在记忆管理页自己补充）"""
    mem = MemoryService.add_memory(
        db, user_id, req.content, layer=req.layer, role_key=req.role_key,
        title=req.title, salience=req.salience, source="manual",
    )
    if not mem:
        return ResponseBase.error(message="内容为空或与该角色已有记忆重复", code=409)
    return ResponseBase.success(data=to_dict(mem), message="已记住")


@router.put("/{memory_id}")
def update_memory(memory_id: int, req: MemoryUpdateRequest,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """编辑一条记忆"""
    ok = MemoryService.update_memory(
        db, user_id, memory_id, content=req.content or "", title=req.title or "",
        layer=req.layer or "", salience=req.salience,
    )
    if not ok:
        return ResponseBase.error(message="记忆不存在或已删除", code=404)
    return ResponseBase.success(message="已更新")


@router.delete("/clear")
def clear_memories(role_key: str = Query(default="", description="指定角色；为空则清空全部"),
                   all_roles: bool = Query(default=False, description="true=清空该用户所有角色的记忆"),
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """一键清空记忆"""
    key = "" if all_roles else role_key
    count = MemoryService.clear_memories(db, user_id, key)
    return ResponseBase.success(data={"deleted": count}, message=f"已清空 {count} 条记忆")


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """单条删除（软删除，用户可随时删掉不想被记住的内容）"""
    ok = MemoryService.delete_memory(db, user_id, memory_id)
    if not ok:
        return ResponseBase.error(message="记忆不存在或已删除", code=404)
    return ResponseBase.success(message="已删除这一条")


@router.post("/extract")
def extract_memory(req: MemoryExtractRequest, user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """从一段文本里按规则抽取记忆（不走大模型，供前端即时同步用）"""
    saved = MemoryService.extract_by_rules(db, user_id, req.role_key, req.text)
    return ResponseBase.success(data={"saved": saved}, message=f"新增 {saved} 条记忆")
