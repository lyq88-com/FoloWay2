# -*- coding: utf-8 -*-
"""
用户 API - 个人信息更新
"""
import json
import re
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User, UserDataBackup
from app.schemas.common import ResponseBase
from app.services.storage_service import get_storage
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/user", tags=["用户"])

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
AVATAR_MAX_BYTES = 5 * 1024 * 1024  # 头像大小上限 5MB


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[int] = None
    # ↓↓↓ 新增 ↓↓↓ 编辑个人资料：手机号 / 个性签名（原来后端不支持，前端只能禁用输入框）
    phone: Optional[str] = None
    signature: Optional[str] = None
    # ↑↑↑ 新增 ↑↑↑


def _normalize_avatar(value: Optional[str]) -> str:
    """
    头像存库统一为相对路径（如 avatar/xxx.jpg），只认 /uploads/ 之后的片段。
    原因：后端 static_base_url 是硬编码的局域网 IP（172.20.10.3），换 WiFi/换机器后
          存进库的绝对 URL 就全废了；前端展示时再用自己的环境前缀拼回去。
    """
    if not value:
        return ""
    text = str(value).strip()
    if "/uploads/" in text:
        return text.split("/uploads/", 1)[1]
    return text


def _serialize_user(user: User) -> dict:
    """用户资料统一输出（phone/signature 的 None 一律转空串，避免前端显示 null）"""
    return {
        "id": user.id,
        "phone": user.phone or "",
        "nickname": user.nickname or "",
        "avatar": user.avatar or "",
        "signature": user.signature or "",
        "gender": user.gender or 0,
        "register_time": str(user.register_time),
    }


@router.get("/info")
def get_user_info(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取用户信息"""
    if user_id == 0:
        return ResponseBase.success({"id": 0, "nickname": "游客", "is_guest": True})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    # ↓↓↓ 新增 ↓↓↓ 一并返回 signature，供编辑资料页回填
    return ResponseBase.success(_serialize_user(user))
    # ↑↑↑ 新增 ↑↑↑


@router.put("/update")
def update_user(req: UserUpdate, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """更新用户信息"""
    if user_id == 0:
        return ResponseBase.error("游客不支持修改信息", 403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar is not None:
        # ↓↓↓ 修改 ↓↓↓ 只存相对路径，避免把硬编码局域网 IP 写进库
        user.avatar = _normalize_avatar(req.avatar)
        # ↑↑↑ 修改 ↑↑↑
    if req.gender is not None:
        user.gender = req.gender

    # ↓↓↓ 新增 ↓↓↓ 手机号：格式校验 + 唯一性校验（users.phone 有 UNIQUE 索引）
    if req.phone is not None:
        phone = (req.phone or "").strip()
        if phone:
            if not PHONE_RE.match(phone):
                # 422 → 前端 request.js 会把 detail 弹成 toast
                raise HTTPException(status_code=422, detail="手机号格式不正确")
            dup = db.query(User).filter(User.phone == phone, User.id != user_id).first()
            if dup:
                raise HTTPException(status_code=409, detail="该手机号已被其他账号使用")
            user.phone = phone
        else:
            # 清空场景：必须写 NULL 而不是 ''，否则 UNIQUE 索引下第二个空串用户会撞键
            user.phone = None
    # ↑↑↑ 新增 ↑↑↑

    # ↓↓↓ 新增 ↓↓↓ 个性签名（users.signature 由 migration_user_profile.sql 补列）
    if req.signature is not None:
        user.signature = (req.signature or "")[:200]
    # ↑↑↑ 新增 ↑↑↑

    db.commit()
    # ↓↓↓ 新增 ↓↓↓ 回传完整资料，前端可直接同步 store，省一次 /user/info 请求
    return ResponseBase.success(_serialize_user(user))
    # ↑↑↑ 新增 ↑↑↑


# ============ 头像上传 ============
# ↓↓↓ 新增 ↓↓↓
@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传头像（单张图片）
    返回: { url: "http://host/uploads/avatar/xxx.jpg", path: "avatar/xxx.jpg", avatar: 同 url }
    说明: 上传即写库（头像换完立刻生效），前端拿到后同步表单即可，不受"是否点了保存"影响。
    """
    if user_id == 0:
        return ResponseBase.error("游客不支持上传头像", 403)
    if not file.content_type or not file.content_type.startswith("image/"):
        return ResponseBase.error("仅支持图片格式", 400)

    file_bytes = await file.read()
    if not file_bytes:
        return ResponseBase.error("图片内容为空", 400)
    if len(file_bytes) > AVATAR_MAX_BYTES:
        return ResponseBase.error("图片不能超过 5MB", 400)

    storage = get_storage()
    relative_path = storage.save(file_bytes, file.filename or "avatar.jpg", subdir="avatar")
    full_url = storage.get_url(relative_path)

    # 上传即生效：直接把新头像写回 users.avatar（存相对路径，只认 /uploads/ 之后的部分）
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.avatar = relative_path
        db.commit()

    return ResponseBase.success({"url": full_url, "path": relative_path, "avatar": full_url})
# ↑↑↑ 新增 ↑↑↑


# ============================================================
# ↓↓↓ 安全合规批次新增 ↓↓↓
# 偏好设置（主动消息/青少年模式）+ 数据导出 + 账号注销
# ============================================================

class UserPrefsUpdate(BaseModel):
    allow_proactive_msg: Optional[int] = None   # 1允许 0关闭
    teen_mode: Optional[int] = None             # 1开启 0关闭


def _serialize_user_full(user: User) -> dict:
    """导出/备份用：不含 password_hash 等凭证字段"""
    return {
        "id": user.id,
        "phone": user.phone or "",
        "username": user.username or "",
        "email": user.email or "",
        "nickname": user.nickname or "",
        "avatar": user.avatar or "",
        "signature": user.signature or "",
        "gender": user.gender or 0,
        "allow_proactive_msg": int(user.allow_proactive_msg if user.allow_proactive_msg is not None else 1),
        "teen_mode": int(user.teen_mode or 0),
        "register_time": str(user.register_time),
    }


def _collect_user_data(db: Session, user: User) -> dict:
    """汇总用户个人数据（导出/注销备份共用），单表限量防止快照过大"""
    LIMIT = 500

    def rows(q, fmt):
        try:
            return [fmt(r) for r in q.limit(LIMIT).all()]
        except Exception as e:
            print(f"[user][WARN] 导出数据片段失败，已跳过: {type(e).__name__}: {e}")
            return []

    from app.models.habit import Habit, Checkin, CheckinItem
    from app.models.chat import ChatSession, ChatMessage, AIUserMemory
    from app.models.emotion import EmotionRecord
    from app.models.moment import Moment
    from app.models.schedule import Schedule

    uid = user.id
    data = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile": _serialize_user_full(user),
        "habits": rows(
            db.query(Habit).filter(Habit.user_id == uid).order_by(Habit.id.desc()),
            lambda h: {"id": h.id, "name": h.name, "status": h.status,
                       "is_paused": int(h.is_paused or 0), "created_at": str(h.created_at)},
        ),
        "checkins": rows(
            db.query(Checkin).filter(Checkin.user_id == uid).order_by(Checkin.id.desc()),
            lambda c: {"id": c.id, "checkin_date": str(c.checkin_date),
                       "completed_count": c.completed_count, "total_habits": c.total_habits},
        ),
        "checkin_items": rows(
            db.query(CheckinItem).filter(CheckinItem.user_id == uid).order_by(CheckinItem.id.desc()),
            lambda i: {"id": i.id, "habit_id": i.habit_id, "completed": i.completed,
                       "note": i.note or "", "created_at": str(i.created_at)},
        ),
        "chat_sessions": rows(
            db.query(ChatSession).filter(ChatSession.user_id == uid).order_by(ChatSession.id.desc()),
            lambda s: {"id": s.id, "title": s.title, "message_count": s.message_count,
                       "created_at": str(s.created_at)},
        ),
        "chat_messages": rows(
            db.query(ChatMessage).filter(ChatMessage.user_id == uid).order_by(ChatMessage.id.desc()),
            lambda m: {"id": m.id, "session_id": m.session_id, "role": m.role,
                       "content": m.content, "created_at": str(m.created_at)},
        ),
        "ai_memories": rows(
            db.query(AIUserMemory).filter(AIUserMemory.user_id == uid).order_by(AIUserMemory.id.desc()),
            lambda m: {"id": m.id, "title": m.title, "memory_content": m.memory_content,
                       "layer": m.layer, "created_at": str(m.created_at)},
        ),
        "emotions": rows(
            db.query(EmotionRecord).filter(EmotionRecord.user_id == uid).order_by(EmotionRecord.id.desc()),
            lambda e: {"id": e.id, "emotion": e.emotion, "intensity": e.intensity,
                       "record_date": str(e.record_date)},
        ),
        "moments": rows(
            db.query(Moment).filter(Moment.user_id == uid).order_by(Moment.id.desc()),
            lambda m: {"id": m.id, "content": m.content, "created_at": str(m.created_at)},
        ),
        "schedules": rows(
            db.query(Schedule).filter(Schedule.user_id == uid).order_by(Schedule.id.desc()),
            lambda s: {"id": s.id, "title": s.title, "schedule_date": str(s.schedule_date),
                       "is_done": int(s.is_done or 0)},
        ),
    }
    return data


@router.get("/prefs")
def get_user_prefs(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """读取偏好设置：允许AI主动消息 / 青少年模式"""
    if user_id == 0:
        # 游客：返回默认值（不落库）
        return ResponseBase.success({"allow_proactive_msg": 1, "teen_mode": 0})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    return ResponseBase.success({
        "allow_proactive_msg": int(user.allow_proactive_msg if user.allow_proactive_msg is not None else 1),
        "teen_mode": int(user.teen_mode or 0),
    })


@router.put("/prefs")
def update_user_prefs(req: UserPrefsUpdate, user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """更新偏好设置（allow_proactive_msg / teen_mode）"""
    if user_id == 0:
        return ResponseBase.error("游客不支持修改偏好", 403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    if req.allow_proactive_msg is not None:
        user.allow_proactive_msg = 1 if req.allow_proactive_msg else 0
    if req.teen_mode is not None:
        user.teen_mode = 1 if req.teen_mode else 0
    db.commit()
    return ResponseBase.success({
        "allow_proactive_msg": int(user.allow_proactive_msg if user.allow_proactive_msg is not None else 1),
        "teen_mode": int(user.teen_mode or 0),
    })


@router.post("/export_my_data")
def export_my_data(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    导出我的数据：汇总个人数据 JSON，同时留档到 user_data_backups（backup_type=export）。
    返回完整数据给用户下载/查看。
    """
    if user_id == 0:
        return ResponseBase.error("游客没有可导出的数据", 403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)

    data = _collect_user_data(db, user)
    try:
        db.add(UserDataBackup(
            user_id=user_id, backup_type="export",
            data_json=json.dumps(data, ensure_ascii=False, default=str),
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[user][WARN] 导出留档失败（不影响返回）: {type(e).__name__}: {e}")

    counts = {k: (len(v) if isinstance(v, list) else 1) for k, v in data.items()
              if k not in ("exported_at", "profile")}
    return ResponseBase.success({
        "exported_at": data["exported_at"],
        "summary": counts,
        "data": data,
    })


@router.post("/deactivate_account")
def deactivate_account(user_id: int = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """
    注销账号：先把个人数据打包备份到 user_data_backups（backup_type=deactivate），
    再做逻辑清除（禁用 + 匿名化）。演示项目不做物理删除，保留申诉恢复能力。
    """
    if user_id == 0:
        return ResponseBase.error("游客无需注销", 403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    if user.status == 0:
        return ResponseBase.error("该账号已注销", 400)

    # 1) 备份快照（失败则中止注销，绝不丢数据）
    data = _collect_user_data(db, user)
    backup = UserDataBackup(
        user_id=user_id, backup_type="deactivate",
        data_json=json.dumps(data, ensure_ascii=False, default=str),
    )
    db.add(backup)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[user][ERR] 注销备份失败: {type(e).__name__}: {e}")
        return ResponseBase.error("注销失败：数据备份未完成，请稍后再试", 500)

    # 2) 逻辑清除：禁用 + 匿名化（可回滚）
    anonym_suffix = str(user.id).zfill(6)
    user.status = 0
    user.phone = None
    user.email = None
    user.signature = ""
    user.avatar = ""
    user.nickname = f"已注销用户{anonym_suffix}"
    user.allow_proactive_msg = 0
    db.commit()

    return ResponseBase.success({
        "message": "账号已注销。你的数据已留档，如需恢复请联系客服申诉。",
        "backup_id": backup.id,
    })
# ↑↑↑ 安全合规批次新增结束 ↑↑↑
