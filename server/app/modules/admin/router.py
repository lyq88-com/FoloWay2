# -*- coding: utf-8 -*-
"""
管理后台接口（/api/v1/admin/*）

对齐 frontend/admin/src/api/*.js 的 22 条接口；鉴权使用独立的管理员 JWT（type=admin），
普通用户 token 无法访问。所有写操作都会落一条 admin_logs 记录。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.user import Admin, User
from app.models.habit import Habit, TaskTemplate
from app.models.chat import AIRole, AIRoleAsset, ChatMessage, ChatSession
from app.models.achievement import Badge, UserBadge
from app.models.archive import CheckinDiary
from app.modules.admin.models import AdminLog, AdminReview
from app.modules.admin import service as admin_service
from app.schemas.common import ResponseBase
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["管理后台"])


# ---------------- 请求体 ----------------
class AdminLoginIn(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=64)


class UserStatusIn(BaseModel):
    status: int = Field(..., description="1正常 0禁用")


class ReviewIn(BaseModel):
    status: str = Field(..., description="approved / rejected")
    remark: str = Field("", max_length=255)


class RoleIn(BaseModel):
    roleType: str = Field("", max_length=20)
    name: str = Field("", max_length=50)
    personality: str = Field("", max_length=255)
    description: str = Field("", max_length=255)
    avatar: str = Field("", max_length=32)
    systemPrompt: str = ""
    status: int = 1
    sortOrder: int = 0


class RoleAssetIn(BaseModel):
    assetUrl: str = Field("", max_length=500)
    bubbleText: str = Field("", max_length=100)
    animationType: str = Field("none", max_length=20)
    status: int = 1


class TemplateIn(BaseModel):
    type: str = Field(..., max_length=20)
    name: str = Field(..., max_length=50)
    icon: str = Field("", max_length=20)
    description: str = Field("", max_length=255)
    defaultTarget: str = Field("", max_length=100)
    sortOrder: int = 0
    status: int = 1


def _ip(request: Request) -> str:
    return (request.client.host if request.client else "") or ""


# ---------------- 认证 ----------------
@router.post("/login")
def admin_login(req: AdminLoginIn, request: Request, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == req.username.strip()).first()
    if admin is None or not AuthService.verify_password(req.password, admin.password_hash):
        return ResponseBase.error("用户名或密码错误", 401)
    if int(admin.status or 0) != 1:
        return ResponseBase.error("账号已被禁用", 403)

    admin.last_login_time = datetime.now()
    admin.last_login_ip = _ip(request)
    admin_service.add_log(db, {"id": admin.id, "username": admin.username, "nickname": admin.nickname},
                          "登录", "auth", admin.id, "管理员登录", _ip(request))
    db.commit()
    db.refresh(admin)

    return ResponseBase.success({
        "token": AuthService.create_admin_token(admin.id, admin.role or "admin"),
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "nickname": admin.nickname or admin.username,
            "avatar": admin.avatar or "",
            "role": admin.role or "admin",
            "roleName": {"super_admin": "超级管理员", "admin": "管理员", "operator": "运营"}.get(
                admin.role or "admin", "管理员"),
            "lastLoginTime": admin_service.fmt(admin.last_login_time),
            "lastLoginIp": admin.last_login_ip or "",
        },
    })


@router.get("/info")
def admin_info(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(Admin).filter(Admin.id == admin["id"]).first()
    if row is None:
        return ResponseBase.error("管理员不存在", 404)
    return ResponseBase.success({
        "id": row.id,
        "username": row.username,
        "nickname": row.nickname or row.username,
        "avatar": row.avatar or "",
        "role": row.role or "admin",
        "roleName": {"super_admin": "超级管理员", "admin": "管理员", "operator": "运营"}.get(
            row.role or "admin", "管理员"),
        "lastLoginTime": admin_service.fmt(row.last_login_time),
        "lastLoginIp": row.last_login_ip or "",
    })


@router.post("/logout")
def admin_logout(request: Request, admin: dict = Depends(get_current_admin),
                 db: Session = Depends(get_db)):
    admin_service.add_log(db, admin, "退出登录", "auth", admin["id"], "管理员退出", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


# ---------------- 看板 ----------------
@router.get("/dashboard/stats")
def dashboard(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ResponseBase.success(admin_service.dashboard_stats(db))


# ---------------- 用户管理 ----------------
@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    keyword: str = Query("", max_length=50),
    status: str = Query(""),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if keyword:
        like = f"%{keyword.strip()}%"
        q = q.filter((User.nickname.like(like)) | (User.phone.like(like)) | (User.username.like(like)))
    if status in ("0", "1"):
        q = q.filter(User.status == int(status))

    total = q.count()
    rows = q.order_by(User.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    aggs = admin_service.user_aggregates(db, [u.id for u in rows])
    return ResponseBase.success({
        "list": [admin_service.user_to_dict(u, aggs.get(u.id)) for u in rows],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    })


@router.get("/users/{user_id}")
def user_detail(user_id: int, admin: dict = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return ResponseBase.error("用户不存在", 404)
    return ResponseBase.success(admin_service.user_detail(db, user))


@router.put("/users/{user_id}/status")
def update_user_status(user_id: int, req: UserStatusIn, request: Request,
                       admin: dict = Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return ResponseBase.error("用户不存在", 404)
    user.status = 1 if int(req.status) == 1 else 0
    admin_service.add_log(db, admin, "更新用户状态", "user", user_id,
                          f"{'启用' if user.status == 1 else '禁用'}用户 {user.nickname}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


# ---------------- AI 角色管理 ----------------
def _role_dict(r: AIRole):
    return {
        "id": r.id,
        "roleType": r.role_type,
        "name": r.name,
        "personality": r.personality or "",
        "description": r.description or "",
        "avatar": r.avatar or "",
        "systemPrompt": r.system_prompt or "",
        "status": int(r.status or 0),
        "sortOrder": int(r.sort_order or 0),
        "createdAt": admin_service.fmt(r.created_at),
    }


@router.get("/roles")
def list_roles(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(AIRole).order_by(AIRole.sort_order.asc(), AIRole.id.asc()).all()
    return ResponseBase.success({"list": [_role_dict(r) for r in rows], "total": len(rows)})


@router.post("/roles")
def create_role(req: RoleIn, request: Request, admin: dict = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    role_type = (req.roleType or "").strip()
    name = (req.name or "").strip()
    if not role_type or not name:
        return ResponseBase.error("角色标识与名称不能为空", 422)
    if db.query(AIRole).filter(AIRole.role_type == role_type).first():
        return ResponseBase.error("角色标识已存在", 409)
    row = AIRole(
        role_type=role_type,
        name=name,
        personality=req.personality,
        description=req.description,
        avatar=req.avatar,
        system_prompt=req.systemPrompt,
        status=1 if req.status == 1 else 0,
        sort_order=req.sortOrder,
    )
    db.add(row)
    db.flush()
    admin_service.add_log(db, admin, "创建AI角色", "role", row.id, f"创建角色 {name}", _ip(request))
    db.commit()
    db.refresh(row)
    return ResponseBase.success(_role_dict(row))


@router.put("/roles/{role_id}")
def update_role(role_id: int, req: RoleIn, request: Request,
                admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(AIRole).filter(AIRole.id == role_id).first()
    if row is None:
        return ResponseBase.error("角色不存在", 404)
    if req.roleType and req.roleType != row.role_type:
        if db.query(AIRole).filter(AIRole.role_type == req.roleType).first():
            return ResponseBase.error("角色标识已存在", 409)
        row.role_type = req.roleType
    if req.name:
        row.name = req.name
    row.personality = req.personality if req.personality else row.personality
    row.description = req.description if req.description else row.description
    if req.avatar:
        row.avatar = req.avatar
    if req.systemPrompt:
        row.system_prompt = req.systemPrompt
    if req.status in (0, 1):
        row.status = req.status
    row.sort_order = req.sortOrder
    admin_service.add_log(db, admin, "更新AI角色", "role", role_id, f"更新角色 {row.name}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, request: Request, admin: dict = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    row = db.query(AIRole).filter(AIRole.id == role_id).first()
    if row is None:
        return ResponseBase.error("角色不存在", 404)
    name = row.name
    db.query(AIRoleAsset).filter(AIRoleAsset.role_id == role_id).delete(synchronize_session=False)
    db.delete(row)
    admin_service.add_log(db, admin, "删除AI角色", "role", role_id, f"删除角色 {name}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


@router.get("/roles/{role_id}/assets")
def role_assets(role_id: int, admin: dict = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    rows = db.query(AIRoleAsset).filter(AIRoleAsset.role_id == role_id).all()
    return ResponseBase.success({
        "roleId": role_id,
        "list": [{
            "id": a.id,
            "roleId": a.role_id,
            "emotionStatus": a.emotion_status,
            "assetUrl": a.asset_url or "",
            "bubbleText": a.bubble_text or "",
            "animationType": a.animation_type or "none",
            "status": int(a.status or 0),
        } for a in rows],
    })


@router.put("/roles/{role_id}/assets/{asset_id}")
def update_role_asset(role_id: int, asset_id: int, req: RoleAssetIn, request: Request,
                      admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = (db.query(AIRoleAsset)
           .filter(AIRoleAsset.id == asset_id, AIRoleAsset.role_id == role_id).first())
    if row is None:
        return ResponseBase.error("素材不存在", 404)
    if req.assetUrl:
        row.asset_url = req.assetUrl
    if req.bubbleText:
        row.bubble_text = req.bubbleText
    if req.animationType:
        row.animation_type = req.animationType
    row.status = 1 if req.status == 1 else 0
    admin_service.add_log(db, admin, "更新角色素材", "role", role_id,
                          f"更新素材 {asset_id}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


# ---------------- 任务模板 ----------------
def _template_dict(t: TaskTemplate):
    return {
        "id": t.id,
        "type": t.type,
        "name": t.name,
        "icon": t.icon or "",
        "description": t.description or "",
        "defaultTarget": t.default_target or "",
        "sortOrder": int(t.sort_order or 0),
        "status": int(t.status or 0),
        "createdAt": admin_service.fmt(t.created_at),
    }


@router.get("/templates")
def list_templates(status: str = Query(""), admin: dict = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    q = db.query(TaskTemplate)
    if status in ("0", "1"):
        q = q.filter(TaskTemplate.status == int(status))
    rows = q.order_by(TaskTemplate.sort_order.asc(), TaskTemplate.id.asc()).all()
    return ResponseBase.success({"list": [_template_dict(t) for t in rows], "total": len(rows)})


@router.post("/templates")
def create_template(req: TemplateIn, request: Request, admin: dict = Depends(get_current_admin),
                    db: Session = Depends(get_db)):
    row = TaskTemplate(
        type=req.type.strip(),
        name=req.name.strip(),
        icon=req.icon,
        description=req.description,
        default_target=req.defaultTarget,
        sort_order=req.sortOrder,
        status=1 if req.status == 1 else 0,
    )
    db.add(row)
    db.flush()
    admin_service.add_log(db, admin, "创建模板", "template", row.id,
                          f"创建模板 {row.name}", _ip(request))
    db.commit()
    db.refresh(row)
    return ResponseBase.success(_template_dict(row))


@router.put("/templates/{template_id}")
def update_template(template_id: int, req: TemplateIn, request: Request,
                    admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if row is None:
        return ResponseBase.error("模板不存在", 404)
    row.type = req.type
    row.name = req.name
    row.icon = req.icon
    row.description = req.description
    row.default_target = req.defaultTarget
    row.sort_order = req.sortOrder
    row.status = 1 if req.status == 1 else 0
    admin_service.add_log(db, admin, "更新模板", "template", template_id,
                          f"更新模板 {row.name}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, request: Request, admin: dict = Depends(get_current_admin),
                    db: Session = Depends(get_db)):
    row = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if row is None:
        return ResponseBase.error("模板不存在", 404)
    name = row.name
    db.delete(row)
    admin_service.add_log(db, admin, "删除模板", "template", template_id,
                          f"删除模板 {name}", _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


# ---------------- 内容审核 ----------------
@router.get("/content/chats")
def list_chat_contents(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: str = Query(""),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(ChatMessage)
    if status == "pending":
        reviewed = db.query(AdminReview.target_id).filter(AdminReview.target_type == "chat")
        q = q.filter(~ChatMessage.id.in_(reviewed))
    elif status in ("approved", "rejected"):
        ids = db.query(AdminReview.target_id).filter(
            AdminReview.target_type == "chat", AdminReview.status == status)
        q = q.filter(ChatMessage.id.in_(ids))

    total = q.count()
    rows = q.order_by(ChatMessage.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    users = {u.id: u for u in db.query(User).filter(
        User.id.in_({r.user_id for r in rows})).all()} if rows else {}
    status_map = admin_service.review_map(db, "chat", [r.id for r in rows])
    return ResponseBase.success({
        "list": [admin_service.chat_content_dict(r, users.get(r.user_id), status_map.get(r.id))
                 for r in rows],
        "total": total, "page": page, "pageSize": pageSize,
    })


@router.get("/content/checkins")
def list_checkin_contents(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: str = Query(""),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(CheckinDiary)
    if status == "pending":
        reviewed = db.query(AdminReview.target_id).filter(AdminReview.target_type == "checkin")
        q = q.filter(~CheckinDiary.id.in_(reviewed))
    elif status in ("approved", "rejected"):
        ids = db.query(AdminReview.target_id).filter(
            AdminReview.target_type == "checkin", AdminReview.status == status)
        q = q.filter(CheckinDiary.id.in_(ids))

    total = q.count()
    rows = q.order_by(CheckinDiary.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    users = {u.id: u for u in db.query(User).filter(
        User.id.in_({r.user_id for r in rows})).all()} if rows else {}
    habits = {h.id: h for h in db.query(Habit).filter(
        Habit.id.in_({r.habit_id for r in rows})).all()} if rows else {}
    status_map = admin_service.review_map(db, "checkin", [r.id for r in rows])
    result = []
    for r in rows:
        item = admin_service.checkin_content_dict(r, users.get(r.user_id), habits.get(r.habit_id))
        item["reviewStatus"] = status_map.get(r.id, "pending")
        result.append(item)
    return ResponseBase.success({"list": result, "total": total, "page": page, "pageSize": pageSize})


@router.put("/content/{content_id}/review")
def review_content(content_id: int, req: ReviewIn, request: Request,
                   admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    if req.status not in ("approved", "rejected"):
        return ResponseBase.error("审核结果只能是 approved / rejected", 422)

    target_type = None
    if db.query(ChatMessage.id).filter(ChatMessage.id == content_id).first():
        target_type = "chat"
    elif db.query(CheckinDiary.id).filter(CheckinDiary.id == content_id).first():
        target_type = "checkin"
    if target_type is None:
        return ResponseBase.error("内容不存在", 404)

    admin_service.upsert_review(db, target_type, content_id, req.status,
                                admin["id"], req.remark)
    admin_service.add_log(db, admin, "审核内容", "content", content_id,
                          f"{'通过' if req.status == 'approved' else '驳回'} {target_type} #{content_id}",
                          _ip(request))
    db.commit()
    return ResponseBase.success({"success": True})


@router.get("/badges")
def list_badges(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    counts = dict(
        db.query(UserBadge.badge_id, func.count(UserBadge.id))
        .group_by(UserBadge.badge_id).all()
    )
    rows = db.query(Badge).order_by(Badge.id.asc()).all()
    return ResponseBase.success({
        "list": [{
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "description": b.description or "",
            "icon": b.icon or "",
            "conditionType": b.condition_type,
            "conditionValue": int(b.condition_value or 0),
            "status": int(b.status or 0),
            "earnedCount": int(counts.get(b.id, 0)),
        } for b in rows],
        "total": len(rows),
    })


@router.get("/logs")
def list_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AdminLog)
    total = q.count()
    rows = q.order_by(AdminLog.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ResponseBase.success({
        "list": [r.to_dict() for r in rows],
        "total": total, "page": page, "pageSize": pageSize,
    })
