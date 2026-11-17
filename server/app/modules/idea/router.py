# -*- coding: utf-8 -*-
"""
「小想法 · 共鸣匹配」HTTP 路由
==============================

挂载前缀：/api/v1/idea（由 app/main.py 追加注册）
所有接口前置校验登录态（Depends(get_current_user)），并做参数校验与限流。

路由清单（对齐需求的 6 个云对象方法 + 私聊/通知补充）：
  POST   /idea/publish            发布想法（= publishIdea）
  GET    /idea/my-resonance       我收到的共鸣（= getMyResonance）
  POST   /idea/light              点亮（= lightIdea，含双向判定）
  POST   /idea/react              轻互动（= quickReact）
  GET    /idea/my-ideas           我发布的想法（= getMyIdeaList）
  DELETE /idea/my-ideas/{id}      删除想法（= deleteIdea，级联清理）
  ---- 支撑 ----
  GET/POST /idea/setting          「接受共鸣匹配」总开关
  POST   /idea/upload             上传单张配图
  GET    /idea/conversations      私聊会话列表
  GET    /idea/conversation/{id}  会话消息
  POST   /idea/conversation/{id}  发送消息
  POST   /idea/block/{uid}        拉黑对方（同时从会话列表隐藏）
  DELETE /idea/block/{uid}        取消拉黑
  GET    /idea/notifications      通知列表 + 未读数
  POST   /idea/notifications/read 标记已读
  GET    /idea/badge              消息小红点汇总
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.services.storage_service import get_storage

from . import service
from .content_safety import (
    audit_text, limiter,
    PUBLISH_LIMIT, PUBLISH_WINDOW,
    LIGHT_LIMIT, LIGHT_WINDOW,
    REACT_LIMIT, REACT_WINDOW,
    MSG_LIMIT, MSG_WINDOW,
)
from .schemas import (
    IdeaPublishRequest, IdeaLightRequest, IdeaQuickReactRequest,
    IdeaSettingRequest, IdeaMessageRequest, IdeaReadRequest,
)

router = APIRouter(prefix="/idea", tags=["小想法·共鸣"])


def _err(result: dict):
    """把 service 的 {'__error__','__code__'} 转成统一错误响应"""
    return ResponseBase.error(result["__error__"], result.get("__code__", 400))


# ============================================================
# 发布
# ============================================================
@router.post("/publish")
def publish_idea(
    payload: IdeaPublishRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布一条小想法，并返回本次匹配到的共鸣（3~5 条，可能更少）"""
    if not limiter.allow(f"publish:{user_id}", PUBLISH_LIMIT, PUBLISH_WINDOW):
        return ResponseBase.error("发布太频繁了，歇一会儿再发吧", 429)

    content = (payload.content or "").strip()
    ok, reason = audit_text(content)
    if not ok:
        return ResponseBase.error(reason, 400)

    idea, cards = service.publish_and_match(
        db, user_id, content, payload.image or "", bool(payload.is_anonymous)
    )
    return ResponseBase.success({
        "idea": idea.to_dict(),
        "resonance": cards,
        "resonance_count": len(cards),
    })


# ============================================================
# 我的共鸣
# ============================================================
@router.get("/my-resonance")
def get_my_resonance(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取系统推送给我的全部共鸣"""
    cards = service.get_my_resonance(db, user_id)
    return ResponseBase.success({"list": cards, "total": len(cards)})


# ============================================================
# 点亮
# ============================================================
@router.post("/light")
def light_idea(
    payload: IdeaLightRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """点亮一条共鸣；若构成双向点亮，返回 matched + conversation_id"""
    if not limiter.allow(f"light:{user_id}", LIGHT_LIMIT, LIGHT_WINDOW):
        return ResponseBase.error("操作太频繁了，请稍后再试", 429)

    result = service.light_idea(db, user_id, payload.resonance_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 轻互动
# ============================================================
@router.post("/react")
def quick_react(
    payload: IdeaQuickReactRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """轻互动：good/agree/highfive/pat"""
    if not limiter.allow(f"react:{user_id}", REACT_LIMIT, REACT_WINDOW):
        return ResponseBase.error("操作太频繁了，请稍后再试", 429)
    result = service.quick_react(db, user_id, payload.idea_id, payload.action_type)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 我的已发布想法
# ============================================================
@router.get("/my-ideas")
def get_my_ideas(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我发布的所有小想法（含本人可见的收到点亮数）"""
    return ResponseBase.success({"list": service.get_my_idea_list(db, user_id)})


@router.delete("/my-ideas/{idea_id}")
def delete_idea(
    idea_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除想法 + 级联清理共鸣与点亮记录"""
    result = service.delete_idea(db, user_id, idea_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 总开关
# ============================================================
@router.get("/setting")
def get_setting(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = service.get_or_create_setting(db, user_id)
    db.commit()
    return ResponseBase.success({"accept_resonance": bool(row.accept_resonance)})


@router.post("/setting")
def set_setting(
    payload: IdeaSettingRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = service.get_or_create_setting(db, user_id)
    row.accept_resonance = 1 if payload.accept_resonance else 0
    db.commit()
    return ResponseBase.success({"accept_resonance": bool(row.accept_resonance)})


# ============================================================
# 配图上传（单张）
# ============================================================
@router.post("/upload")
async def upload_idea_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """上传单张配图，返回 { url, path }（复用统一 storage 抽象）"""
    if not file.content_type or not file.content_type.startswith("image/"):
        return ResponseBase.error("仅支持图片格式", 400)
    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return ResponseBase.error("图片不能超过 5MB", 400)
    storage = get_storage()
    rel = storage.save(file_bytes, file.filename or "idea.jpg", subdir="idea")
    return ResponseBase.success({"url": storage.get_url(rel), "path": rel})


# ============================================================
# 私聊
# ============================================================
@router.get("/conversations")
def conversations(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success({"list": service.get_conversations(db, user_id)})


@router.get("/conversation/{conversation_id}")
def conversation_detail(
    conversation_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.get_messages(db, user_id, conversation_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/conversation/{conversation_id}")
def conversation_send(
    conversation_id: int,
    payload: IdeaMessageRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not limiter.allow(f"msg:{user_id}", MSG_LIMIT, MSG_WINDOW):
        return ResponseBase.error("发送太频繁了，请稍后再试", 429)
    result = service.send_message(db, user_id, conversation_id, payload.content)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/block/{blocked_uid}")
def block_user(
    blocked_uid: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """拉黑对方：不再匹配、会话列表隐藏、双方无法继续发消息"""
    if user_id == 0:
        return ResponseBase.error("请先登录", 403)
    if blocked_uid == user_id:
        return ResponseBase.error("不能拉黑自己", 400)
    return ResponseBase.success(service.block_user(db, user_id, blocked_uid), "已拉黑")


@router.delete("/block/{blocked_uid}")
def unblock_user(
    blocked_uid: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == 0:
        return ResponseBase.error("请先登录", 403)
    return ResponseBase.success(service.unblock_user(db, user_id, blocked_uid), "已取消拉黑")


# ============================================================
# 通知 / 小红点
# ============================================================
@router.get("/notifications")
def notifications(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success(service.get_notifications(db, user_id))


@router.post("/notifications/read")
def notifications_read(
    payload: IdeaReadRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success(service.read_notifications(db, user_id, payload.notification_id or 0))


@router.get("/badge")
def badge(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success(service.unread_badge(db, user_id))
