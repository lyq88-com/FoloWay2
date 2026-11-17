# -*- coding: utf-8 -*-
"""
「专注」模块 HTTP 路由
======================

挂载前缀：/api/v1/focus（由 app/main.py 追加注册）。
所有接口前置校验登录态（Depends(get_current_user)），发布类接口做审核与限流。

路由清单（对齐需求 focusAssistant 云对象 8 方法 + 页面所需补充）：
  POST /focus/plan/generate        备考计划生成并落任务+提醒（= generatePlan）
  POST /focus/task/split           大任务拆解为极小单步（= splitBigTask）
  POST /focus/task                 手动创建任务
  GET  /focus/tasks                今日待办看板（进度 + 子步骤）
  PUT  /focus/task/{id}/status     勾选完成 / 状态调整
  DELETE /focus/task/{id}          删除任务（级联清步骤/提醒/会话）
  POST /focus/step/finish          完成步骤推进（= finishStep，返回 AI 鼓励）
  POST /focus/session/start        开启专注会话（= startFocusSession）
  POST /focus/session/interrupt    跳出/拦截回报（= interruptCheck）
  POST /focus/session/finish       结束专注（生成记录摘要）
  GET  /focus/stat                 统计报表（= getFocusStat）
  POST /focus/remind               创建提醒
  GET  /focus/reminds              待触发提醒列表（前端调度本地通知）
  POST /focus/remind/{id}/trigger  客户端触发回报
  DELETE /focus/remind/{id}        删除提醒
  POST /focus/record               保存引导进度（引导记录）
  GET  /focus/records              引导记录列表（可搜索）
  GET  /focus/record/{id}          回放详情（含导出文本）
  DELETE /focus/record/{id}        删除记录
  POST /focus/dynamic              发布专注动态（= publishFocusDynamic）
  GET  /focus/dynamics             动态流（仅自己+互关好友，无公开广场）
  POST /focus/dynamic/{id}/react   点赞/取消（= reactDynamic）
  DELETE /focus/dynamic/{id}       删除动态
  POST /focus/follow/{uid}         关注（互关好友）
  DELETE /focus/follow/{uid}       取关
  GET  /focus/follows              我的互关好友
  POST /focus/companion-chat       监督陪伴聊天（含 createRemindFromChat 指令解析）
  POST /focus/upload               动态配图上传
  POST /focus/upload-audio         语音转文字（复用现有 ASR 通道）
  GET/POST /focus/setting          动态发布/提醒 开关
  GET  /focus/roles                角色列表（沿用现有角色体系）
  GET  /focus/recommend            空态小任务推荐
"""
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase

from . import service
from .persona import ROLE_IDS, ROLE_META
from .focus_ai import recommend_small_tasks
# 审核与限流工具复用「小想法」模块（独立 import，不改其任何代码）
from app.modules.idea.content_safety import limiter
from .schemas import (
    FocusPlanRequest, FocusTaskCreateRequest, FocusTaskStatusRequest,
    FocusSplitRequest, FocusStepFinishRequest, FocusSessionStartRequest,
    FocusSessionInterruptRequest, FocusSessionFinishRequest,
    FocusRemindRequest, FocusGuideSaveRequest, FocusDynamicRequest,
    FocusChatRequest,
)

router = APIRouter(prefix="/focus", tags=["专注"])


def _err(result: dict):
    return ResponseBase.error(result["__error__"], result.get("__code__", 400))


# ============================================================
# 计划 / 任务
# ============================================================
@router.post("/plan/generate")
def generate_plan(
    payload: FocusPlanRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI 备考计划：生成 → 自动落任务 + 批量提醒（限流防刷）"""
    if not limiter.allow(f"focus_plan:{user_id}", 5, 600):
        return ResponseBase.error("计划生成太频繁了，休息一下再试", 429)
    result = service.publish_plan(
        db, user_id, payload.exam_type, payload.exam_date,
        payload.weakness, payload.daily_minutes, payload.remind_time,
    )
    return ResponseBase.success(result)


@router.post("/task/split")
def split_task(
    payload: FocusSplitRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """大任务 → 极小单步（分步引导入口，同时落引导记录）"""
    if not limiter.allow(f"focus_split:{user_id}", 10, 600):
        return ResponseBase.error("操作太频繁了，请稍后再试", 429)
    result = service.start_guide(db, user_id, payload.prompt, payload.mode)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/task")
def create_task(
    payload: FocusTaskCreateRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动创建任务（可选每日提醒时间）"""
    t = service.create_task(
        db, user_id, payload.title, payload.description, payload.tag,
        payload.est_minutes, payload.start_date, payload.due_date,
        payload.remind_time,
    )
    return ResponseBase.success(t.to_dict())


@router.get("/tasks")
def get_tasks(
    date: str = "",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """今日待办看板（含子步骤与总进度）"""
    return ResponseBase.success(service.get_board(db, user_id, date))


@router.put("/task/{task_id}/status")
def set_task_status(
    task_id: int,
    payload: FocusTaskStatusRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.update_task_status(db, user_id, task_id, payload.status)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.delete("/task/{task_id}")
def delete_task(
    task_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.delete_task(db, user_id, task_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/step/finish")
def finish_step(
    payload: FocusStepFinishRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """「我做到了」→ 推进下一步 + 角色鼓励台词"""
    result = service.finish_step(db, user_id, payload.step_id, payload.role_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 专注会话
# ============================================================
@router.post("/session/start")
def start_session(
    payload: FocusSessionStartRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """startFocusSession：登记会话起点，返回角色台词轮播"""
    result = service.start_session(db, user_id, payload.task_id,
                                   payload.role_id, payload.mode, payload.tag)
    return ResponseBase.success(result)


@router.post("/session/interrupt")
def session_interrupt(
    payload: FocusSessionInterruptRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """interruptCheck：跳出专注 / 黑名单拦截回报（原生 App；小程序 H5 离开检测）"""
    result = service.session_interrupt(db, user_id, payload.session_id, payload.count)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/session/finish")
def finish_session(
    payload: FocusSessionFinishRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """结束专注 → 时长落库 + 生成专注摘要"""
    result = service.finish_session(db, user_id, payload.session_id,
                                    payload.duration, payload.interrupted)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.get("/stat")
def get_stat(
    period: str = "day",
    start_date: str = "",
    end_date: str = "",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """getFocusStat：日/周/月/自定义 聚合报表"""
    return ResponseBase.success(service.get_stat(db, user_id, period, start_date, end_date))


# ============================================================
# 提醒
# ============================================================
@router.post("/remind")
def create_remind(
    payload: FocusRemindRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.create_remind(db, user_id, payload.task_id,
                                   payload.remind_at, payload.text)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.get("/reminds")
def list_reminds(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """待触发提醒（前端据此调度本地通知）"""
    return ResponseBase.success({"list": service.list_reminds(db, user_id)})


@router.post("/remind/{remind_id}/trigger")
def trigger_remind(
    remind_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success(service.trigger_remind(db, user_id, remind_id))


@router.delete("/remind/{remind_id}")
def delete_remind(
    remind_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success(service.delete_remind(db, user_id, remind_id))


# ============================================================
# 引导记录
# ============================================================
@router.post("/record")
def save_record(
    payload: FocusGuideSaveRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """引导推进时回写计时；导出文本即时刷新"""
    result = service.save_guide_progress(db, user_id, payload.record_id,
                                         payload.current_index,
                                         payload.duration_seconds,
                                         payload.finished_content)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.get("/records")
def list_records(
    keyword: str = "",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success({"list": service.get_records(db, user_id, keyword)})


@router.get("/record/{record_id}")
def record_detail(
    record_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """回放详情（含 export_text，前端直接展示/复制导出）"""
    result = service.get_record_detail(db, user_id, record_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.delete("/record/{record_id}")
def delete_record(
    record_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.delete_record(db, user_id, record_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 专注动态
# ============================================================
@router.post("/dynamic")
def publish_dynamic(
    payload: FocusDynamicRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """publishFocusDynamic：仅自己 / 互关好友可见，禁止公开广场"""
    if not limiter.allow(f"focus_dyn:{user_id}", 6, 600):
        return ResponseBase.error("发布太频繁了，歇一会儿", 429)
    result = service.publish_dynamic(db, user_id, payload.content,
                                     payload.image, payload.visible_type)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.get("/dynamics")
def get_dynamics(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """动态流：自己的 + 互关好友的（follow 可见），无任何公开列表"""
    return ResponseBase.success({"list": service.get_dynamics(db, user_id)})


@router.post("/dynamic/{dynamic_id}/react")
def react_dynamic(
    dynamic_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """reactDynamic：点赞/取消（幂等）"""
    result = service.react_dynamic(db, user_id, dynamic_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.delete("/dynamic/{dynamic_id}")
def delete_dynamic(
    dynamic_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.delete_dynamic(db, user_id, dynamic_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 互关好友
# ============================================================
@router.post("/follow/{target_uid}")
def follow(target_uid: int,
           user_id: int = Depends(get_current_user),
           db: Session = Depends(get_db)):
    return ResponseBase.success(service.follow_user(db, user_id, target_uid))


@router.delete("/follow/{target_uid}")
def unfollow(target_uid: int,
             user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    return ResponseBase.success(service.unfollow_user(db, user_id, target_uid))


@router.get("/follows")
def follows(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResponseBase.success({"list": service.my_friend_ids(db, user_id)})


# ============================================================
# 陪伴聊天（监督人设 + 日程指令）
# ============================================================
@router.post("/companion-chat")
def companion_chat(
    payload: FocusChatRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """监督陪伴人设聊天；用户说「提醒我九点四十五收拾房间」自动建待办+提醒"""
    if not limiter.allow(f"focus_chat:{user_id}", 20, 600):
        return ResponseBase.error("说太快啦，歇一下", 429)
    result = service.companion_chat(db, user_id, payload.text, payload.history)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 上传：配图 / 语音
# ============================================================
@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        return ResponseBase.error("仅支持图片格式", 400)
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        return ResponseBase.error("图片不能超过 5MB", 400)
    from app.services.storage_service import get_storage
    storage = get_storage()
    rel = storage.save(data, file.filename or "focus.jpg", subdir="focus")
    return ResponseBase.success({"url": storage.get_url(rel), "path": rel})


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """语音输入：录音上传 → 转文字（复用现有 ASR 通道）"""
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        return ResponseBase.error("录音不能超过 10MB", 400)
    from app.services.voice_service import VoiceDiaryService
    saved = VoiceDiaryService.save_upload(data, file.filename or "focus.mp3")
    try:
        # 转写是同步 HTTP 调用，放线程池避免阻塞事件循环
        result = await run_in_threadpool(service.transcribe_audio, saved["file_path"])
    finally:
        # 语音输入是临时文件，转写完即删，避免 uploads 目录无限增长
        try:
            import os as _os
            _os.remove(saved["file_path"])
        except OSError:
            pass
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


# ============================================================
# 开关 / 角色 / 推荐
# ============================================================
@router.get("/setting")
def get_setting(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = service.get_or_create_setting(db, user_id)
    db.commit()
    return ResponseBase.success({
        "allow_dynamic": bool(row.allow_dynamic),
        "allow_remind": bool(row.allow_remind),
    })


from pydantic import BaseModel  # noqa: E402


class FocusSettingRequest(BaseModel):
    allow_dynamic: Optional[bool] = None
    allow_remind: Optional[bool] = None


@router.post("/setting")
def set_setting(
    payload: FocusSettingRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = service.get_or_create_setting(db, user_id)
    if payload.allow_dynamic is not None:
        row.allow_dynamic = 1 if payload.allow_dynamic else 0
    if payload.allow_remind is not None:
        row.allow_remind = 1 if payload.allow_remind else 0
    db.commit()
    return ResponseBase.success({
        "allow_dynamic": bool(row.allow_dynamic),
        "allow_remind": bool(row.allow_remind),
    })


@router.get("/roles")
def roles():
    """角色列表：沿用现有 App 角色体系（不新增角色库）"""
    return ResponseBase.success({"list": [
        {"id": rid, "name": ROLE_META[rid]["name"], "style": ROLE_META[rid]["style"]}
        for rid in ROLE_IDS
    ]})


@router.get("/recommend")
def recommend():
    """空态推荐小任务（不知道做什么时）"""
    return ResponseBase.success({"list": recommend_small_tasks()})
