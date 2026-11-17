# -*- coding: utf-8 -*-
"""
newfunc 路由 —— 全部接口挂在 /api/newfunc/ 前缀下（main.py 末尾追加挂载）
与旧接口（/api/v1/**）完全隔离，不改动任何旧路由。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.modules.newfunc import bot_service, diary_service, push_service
from app.modules.newfunc.models import PushRecord
from app.modules.newfunc.schemas import (
    AuthorizeRequest, BindCidRequest, BotChatRequest, BotCreateRequest,
    BotMemoryCreateRequest, BotProactiveRequest, BotUpdateRequest,
    DiaryDateRequest, DiarySaveRequest, DiarySummaryRequest,
    PushSettingUpdate,
)

router = APIRouter(tags=["newfunc增量功能"])


def _err(result):
    code = result.get("__code__", 400)
    return ResponseBase.error(message=result["__error__"], code=code)


# ============================================================
# 模块一：消息推送
# ============================================================
@router.get("/push/setting")
def get_push_setting(user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    s = push_service.get_or_create_setting(db, user_id)
    return ResponseBase.success(s.to_dict())


@router.post("/push/setting")
def update_push_setting(payload: PushSettingUpdate,
                        user_id: int = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    s = push_service.get_or_create_setting(db, user_id)
    for k, v in payload.dict(exclude_none=True).items():
        if k in ("push_enabled", "checkin_push_enabled", "todo_push_enabled",
                 "ai_push_enabled", "quiet_enabled", "group_push_enabled"):
            setattr(s, k, 1 if v else 0)
        elif k == "ai_frequency":
            setattr(s, k, v if v in ("low", "medium", "high") else "medium")
        elif k in ("checkin_push_time", "quiet_start", "quiet_end"):
            setattr(s, k, str(v)[:5])
    db.commit()
    return ResponseBase.success(s.to_dict())


@router.post("/push/bind-cid")
def bind_cid(payload: BindCidRequest,
             user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """App 端上报个推 CID；未配置个推时留空走 local 通道"""
    s = push_service.get_or_create_setting(db, user_id)
    s.client_id = (payload.client_id or "")[:100]
    db.commit()
    return ResponseBase.success({"client_id": s.client_id})


@router.get("/push/records")
def push_records(type: str = Query(default=""),
                 only_unread: bool = Query(default=False),
                 page: int = Query(default=1, ge=1),
                 size: int = Query(default=20, ge=1, le=50),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """消息通知中心：推送记录列表（保存每一次推送）"""
    q = db.query(PushRecord).filter(
        PushRecord.uid == user_id, PushRecord.status == 1)
    if type:
        q = q.filter(PushRecord.push_type == type)
    if only_unread:
        q = q.filter(PushRecord.is_read == 0)
    total = q.count()
    rows = q.order_by(PushRecord.id.desc()).offset(
        (page - 1) * size).limit(size).all()
    return ResponseBase.success({
        "total": total, "list": [r.to_dict() for r in rows],
        "unread": db.query(PushRecord).filter(
            PushRecord.uid == user_id, PushRecord.is_read == 0,
            PushRecord.status == 1).count(),
    })


@router.post("/push/{record_id}/read")
def push_read(record_id: int, user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    rec = db.query(PushRecord).filter(
        PushRecord.id == record_id, PushRecord.uid == user_id).first()
    if not rec:
        return ResponseBase.error(message="记录不存在", code=404)
    rec.is_read = 1
    db.commit()
    return ResponseBase.success(message="ok")


@router.post("/push/read-all")
def push_read_all(user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    n = db.query(PushRecord).filter(
        PushRecord.uid == user_id, PushRecord.is_read == 0).update(
        {"is_read": 1}, synchronize_session=False)
    db.commit()
    return ResponseBase.success({"updated": n})


@router.post("/push/test")
async def push_test(user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """发送一条测试推送（验证开关/免打扰/通道链路）"""
    result = await push_service.dispatch_push(
        db, user_id, "test", "测试推送",
        "这是一条测试通知，如果你看到它，说明推送链路通了 ✅")
    return ResponseBase.success(result["record"])


# ============================================================
# 模块二：情绪日记日历
# ============================================================
@router.get("/diary/day")
def diary_day(date: str = Query(default=""),
              user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    return ResponseBase.success(diary_service.day_detail(db, user_id, date))


@router.post("/diary/save")
def diary_save(payload: DiarySaveRequest,
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    return ResponseBase.success(diary_service.save_day(
        db, user_id, payload.date, payload.mood_tags, payload.mood_score,
        payload.diary_text))


@router.post("/diary/summary")
def diary_summary(payload: DiarySummaryRequest,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return ResponseBase.success(diary_service.save_summary(
        db, user_id, payload.date, payload.summary))


@router.post("/diary/ai-summary")
async def diary_ai_summary(payload: DiaryDateRequest,
                           user_id: int = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """AI 依据当日打卡/待办/情绪/日记自动生成总结（只读旧数据）"""
    return ResponseBase.success(
        await diary_service.generate_ai_summary(db, user_id, payload.date))


@router.get("/diary/month")
def diary_month(month: str = Query(default=""),
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return ResponseBase.success(diary_service.month_marks(db, user_id, month))


@router.post("/diary/authorize")
def diary_authorize(payload: AuthorizeRequest,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """单独授权 AI 伙伴读取全局情绪日历数据"""
    return ResponseBase.success(
        diary_service.set_authorize(db, user_id, payload.enabled))


# ============================================================
# 模块三：多 AI 伙伴 + 隔离记忆
# ============================================================
@router.get("/bots")
def bots_list(user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    return ResponseBase.success({"list": bot_service.list_bots(db, user_id)})


@router.post("/bots")
def bots_create(payload: BotCreateRequest,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    result = bot_service.create_bot(db, user_id, payload.dict())
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.put("/bots/{bot_id}")
def bots_update(bot_id: int, payload: BotUpdateRequest,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    result = bot_service.update_bot(db, user_id, bot_id, payload.dict(exclude_none=True))
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.delete("/bots/{bot_id}")
def bots_delete(bot_id: int, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    result = bot_service.delete_bot(db, user_id, bot_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/bots/{bot_id}/chat")
async def bots_chat(bot_id: int, payload: BotChatRequest,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """与指定伙伴对话：人设贴合 + 记忆召回 + 对话后沉淀记忆"""
    result = await bot_service.bot_chat(
        db, user_id, bot_id, payload.text, payload.history)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.get("/bots/{bot_id}/memories")
def bot_memories(bot_id: int, mem_type: str = Query(default=""),
                 page: int = Query(default=1, ge=1),
                 size: int = Query(default=30, ge=1, le=100),
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    result = bot_service.list_memories(db, user_id, bot_id, mem_type, page, size)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/bots/{bot_id}/memories")
def bot_memory_create(bot_id: int, payload: BotMemoryCreateRequest,
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """用户手动写入一条记忆（事实/偏好/情绪/对话）"""
    result = bot_service.create_memory(
        db, user_id, bot_id, payload.content,
        payload.mem_type, payload.importance)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.delete("/bots/{bot_id}/memories/{memory_id}")
def bot_memory_delete(bot_id: int, memory_id: int,
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    result = bot_service.delete_memory(db, user_id, bot_id, memory_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/bots/{bot_id}/memory/reset")
def bot_memory_reset(bot_id: int, user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """重置单个伙伴记忆（只清该伙伴，其他伙伴记忆不受影响）"""
    result = bot_service.reset_memory(db, user_id, bot_id)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@router.post("/bots/{bot_id}/proactive")
async def bot_proactive(bot_id: int,
                        payload: BotProactiveRequest = BotProactiveRequest(),
                        user_id: int = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """手动触发一次该伙伴的主动陪伴消息（定时任务同源逻辑）"""
    s = push_service.get_or_create_setting(db, user_id)
    msg, bid = await bot_service.build_proactive_message(
        db, user_id, diary_auth=s.diary_read_auth, bot_ids=[bot_id])
    if not msg:
        return ResponseBase.error(message="伙伴不存在或未开启主动陪伴", code=404)
    if payload.save_record:
        await push_service.dispatch_push(db, user_id, "ai_companion",
                                         "来自 AI 伙伴", msg, ref_id=bid)
    return ResponseBase.success({"bot_id": bid, "message": msg})


# ============================================================
# 【newfunc 增量-语音包】挂载多语种/方言 TTS 子路由（/api/newfunc/tts/**）
# 纯追加挂载，不改上方任何既有接口；与 /api/v1 原有语音接口完全隔离
# ============================================================
from app.modules.newfunc.voice.tts_router import tts_router  # noqa: E402
router.include_router(tts_router)
