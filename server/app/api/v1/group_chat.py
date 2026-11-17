# -*- coding: utf-8 -*-
"""
群聊 API 路由 —— 独立新建 prefix="/api/v1" 下的 /group/* 子路径
所有鉴权复用 get_current_user，所有 AI 调度复用 group_service
新文件，不碰任何原有业务代码
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.middleware.auth import get_current_user
from app.services import group_service

router = APIRouter()


# ============ Schema ============

class CreateGroupRequest(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=50)
    role_types: List[str] = Field(..., min_length=2, max_length=4,
                                  description='要加入的 AI 伙伴 role_type 列表（2~4 个）')


class AddMemberRequest(BaseModel):
    role_type: str


class RenameGroupRequest(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=50)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# ============ 路由 ============

@router.post("/group/create")
def create_group(req: CreateGroupRequest,
                 user_id: int = Depends(get_current_user)):
    """创建群聊"""
    if not req.role_types:
        raise HTTPException(400, "请至少选 2 位 AI 伙伴")
    g = group_service.create_group(user_id, req.group_name, req.role_types)
    return ResponseBase.success(g)


@router.get("/group/list")
def list_groups(user_id: int = Depends(get_current_user)):
    """我所在的群列表"""
    groups = group_service.list_my_groups(user_id)
    return ResponseBase.success(groups)


@router.get("/group/{group_id}")
def get_group(group_id: int,
              user_id: int = Depends(get_current_user)):
    """群详情（含成员列表）"""
    import pymysql
    from app.core.config import settings
    conn = pymysql.connect(host=settings.db_host, port=settings.db_port,
                           user=settings.db_user, password=settings.db_password,
                           database=settings.db_name, charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    g = group_service.get_group(cur, group_id, user_id)
    cur.close(); conn.close()
    if not g:
        raise HTTPException(404, "群不存在或你没有权限查看")
    return ResponseBase.success(g)


@router.put("/group/{group_id}")
def rename_group(group_id: int, req: RenameGroupRequest,
                 user_id: int = Depends(get_current_user)):
    """改群名（只有群主）"""
    ok = group_service.rename_group(group_id, user_id, req.group_name)
    if not ok:
        raise HTTPException(404, "群不存在或你不是群主")
    return ResponseBase.success({"ok": True})


@router.delete("/group/{group_id}")
def dissolve_group(group_id: int,
                   user_id: int = Depends(get_current_user)):
    """解散群（只有群主）"""
    ok = group_service.dissolve_group(group_id, user_id)
    if not ok:
        raise HTTPException(404, "群不存在或你不是群主")
    return ResponseBase.success({"ok": True})


@router.post("/group/{group_id}/join")
def add_ai_member(group_id: int, req: AddMemberRequest,
                  user_id: int = Depends(get_current_user)):
    """加 AI 成员到群里（【修复】只有群内成员可操作）"""
    ok = group_service.add_member(group_id, user_id, req.role_type)
    if not ok:
        raise HTTPException(403, "无权操作该群或该成员已存在")
    return ResponseBase.success({"ok": True})


@router.post("/group/{group_id}/leave")
def leave_group(group_id: int,
                user_id: int = Depends(get_current_user)):
    """人类成员退群"""
    ok = group_service.leave_group(group_id, user_id)
    if not ok:
        raise HTTPException(400, "群主不能退群，只能解散；或你不在这个群里")
    return ResponseBase.success({"ok": True})


@router.get("/group/{group_id}/messages")
def list_messages(group_id: int,
                  user_id: int = Depends(get_current_user),
                  page: int = Query(1, ge=1),
                  size: int = Query(50, ge=1, le=100)):
    """拉群消息历史（带权限校验）"""
    result = group_service.list_messages(group_id, user_id, page, size)
    return ResponseBase.success(result)


@router.post("/group/{group_id}/send")
async def send_message(group_id: int, req: SendMessageRequest,
                       user_id: int = Depends(get_current_user)):
    """
    发群消息（核心接口）：
    1. 写用户消息
    2. 智能调度 AI 回复（错开时间）
    3. 存 AI 回复
    4. 触发推送
    """
    # 【修复】越权拦截：非群成员不得发言
    if not group_service.is_member(group_id, user_id):
        raise HTTPException(403, "群不存在或你不在这个群里")
    try:
        result = await group_service.dispatch_user_message(group_id, user_id, req.content)
    except PermissionError:
        raise HTTPException(403, "群不存在或你不在这个群里")
    return ResponseBase.success(result)


@router.post("/group/{group_id}/stop")
async def stop_ai(group_id: int,
                  user_id: int = Depends(get_current_user)):
    """喊停：置位暂停标记 + 存一条系统消息（【修复】await 异步服务，原实现返回 500）"""
    try:
        result = await group_service.send_group_stop(group_id, user_id)
    except PermissionError:
        raise HTTPException(403, "群不存在或你不在这个群里")
    return ResponseBase.success(result)


@router.post("/group/{group_id}/resume")
def resume_ai(group_id: int,
              user_id: int = Depends(get_current_user)):
    """【修复新增】继续聊天：解除喊停状态，恢复群内 AI 自动回复"""
    ok = group_service.resume_group_ai(group_id, user_id)
    if not ok:
        raise HTTPException(403, "群不存在或你不在这个群里")
    return ResponseBase.success({"ok": True})


# ============ 模块4 新增：SSE 流式发群消息 endpoint ============
# 【新增独立 endpoint】绝对不修改上面已有的 /send 同步 endpoint
# 权限沿用 get_current_user + group_service 内部的 user_in_group 校验
@router.post("/group/{group_id}/send-sse")
async def send_message_sse(group_id: int, req: SendMessageRequest,
                           user_id: int = Depends(get_current_user)):
    """
    SSE 版发群消息：
    - arrival 事件：用户消息已入群
    - AI 回复事件：每个 AI 生成完完整回复后 yield（各 AI 之间 0.8~1.5s 错开）
    - done 事件：全部结束
    前端逐步展示每个 AI 的回复，打字动画体验。
    """
    # 权限前置校验：用户必须在群里
    import pymysql
    from app.core.config import settings
    conn = pymysql.connect(host=settings.db_host, port=settings.db_port,
                           user=settings.db_user, password=settings.db_password,
                           database=settings.db_name, charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) AS c FROM group_members WHERE group_id=%s AND user_id=%s AND member_type=0",
        (group_id, user_id)
    )
    in_group = cur.fetchone()['c'] > 0
    cur.close(); conn.close()
    if not in_group:
        raise HTTPException(404, "群不存在或你没有权限")

    async def event_generator():
        async for obj in group_service.dispatch_user_message_sse(group_id, user_id, req.content):
            yield f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
# ============ 模块4 SSE endpoint 结束 ============
