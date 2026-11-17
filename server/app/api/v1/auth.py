# -*- coding: utf-8 -*-
"""
认证 API - 登录/注册/游客登录
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core import rate_limit
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    GuestLoginRequest,
    UsernameLoginRequest,
    UsernameRegisterRequest,
    SmsSendRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import AuthService
from app.services.sms_service import SmsService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _client_ip(request: Request) -> str:
    """取客户端 IP

    默认只认 TCP 对端地址；只有显式开启 TRUST_PROXY_HEADERS（部署在可信代理后）
    才读取 X-Forwarded-For，避免客户端伪造请求头绕过登录限流。
    """
    if request is None:
        return "unknown"
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for") or ""
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """手机号密码登录"""
    # 登录失败限流（同账号 + 同 IP）
    ip = _client_ip(request)
    blocked, wait_minutes = rate_limit.login_blocked(req.phone, ip)
    if blocked:
        return ResponseBase.error(f"尝试次数过多，请 {wait_minutes} 分钟后再试", 429)

    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        rate_limit.record_login_failure(req.phone, ip)
        return ResponseBase.error("用户不存在", 404)
    if user.status != 1:
        return ResponseBase.error("账号已被禁用", 403)
    if not AuthService.verify_password(req.password, user.password_hash):
        rate_limit.record_login_failure(req.phone, ip)
        return ResponseBase.error("密码错误", 401)

    rate_limit.clear_login_failures(req.phone, ip)
    # 更新登录信息
    user.last_login_time = datetime.now(timezone.utc)
    user.last_login_ip = ip[:45]
    db.commit()

    token = AuthService.create_access_token(user.id, {"phone": user.phone})
    return ResponseBase.success({
        "token": token,
        "token_type": "Bearer",
        "expires_in": 604800,
        "user_info": {
            "id": user.id,
            "phone": user.phone,
            "username": user.username or "",
            "nickname": user.nickname,
            "avatar": user.avatar,
            "gender": user.gender,
            "register_time": str(user.register_time),
        }
    })


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        return ResponseBase.error("手机号已注册", 409)

    now = datetime.now(timezone.utc)
    user = User(
        phone=req.phone,
        password_hash=AuthService.hash_password(req.password),
        nickname=req.nickname or f"用户{req.phone[-4:]}",
        register_time=now,
        last_login_time=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthService.create_access_token(user.id, {"phone": user.phone})
    return ResponseBase.success({
        "token": token,
        "token_type": "Bearer",
        "user_info": {
            "id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
        }
    })


@router.post("/guest")
def guest_login(req: GuestLoginRequest):
    """游客登录"""
    # 游客不创建数据库记录，只生成临时token
    token = AuthService.create_access_token(0, {"guest": True, "nickname": req.nickname})
    return ResponseBase.success({
        "token": token,
        "token_type": "Bearer",
        "user_info": {
            "id": 0,
            "nickname": req.nickname,
            "is_guest": True,
        }
    })


@router.post("/login-username")
def login_username(req: UsernameLoginRequest, request: Request, db: Session = Depends(get_db)):
    """统一账号登录：用户名或手机号二选一

    历史上这里只认 username，手机号注册的账号在登录页永远登不上，
    实际上形成了「用户名账号 / 手机号账号」两套入口。现在两种标识都能登录，
    返回体同时带 username 与 phone，前端按 username 优先做本地存储键。
    """
    account = (req.username or "").strip()
    # 登录失败限流（同账号 + 同 IP）
    ip = _client_ip(request)
    blocked, wait_minutes = rate_limit.login_blocked(account, ip)
    if blocked:
        return ResponseBase.error(f"尝试次数过多，请 {wait_minutes} 分钟后再试", 429)

    user = (
        db.query(User)
        .filter((User.username == account) | (User.phone == account))
        .first()
    )
    if not user or not AuthService.verify_password(req.password, user.password_hash):
        rate_limit.record_login_failure(account, ip)
        return ResponseBase.error("账号或密码错误", 401)
    if user.status != 1:
        return ResponseBase.error("账号已被禁用", 403)

    rate_limit.clear_login_failures(account, ip)
    user.last_login_time = datetime.now(timezone.utc)
    user.last_login_ip = ip[:45]
    db.commit()

    token = AuthService.create_access_token(user.id)
    return ResponseBase.success({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username or "",
            "phone": user.phone or "",
            "email": user.email or "",
            "nickname": user.nickname or "",
        }
    })


@router.post("/register-username")
def register_username(req: UsernameRegisterRequest, db: Session = Depends(get_db)):
    """统一账号注册：用户名必填，手机号选填

    注册前同时校验用户名 / 手机号 / 邮箱唯一，避免同一个人用不同入口
    注册出多个互不相通的账号。
    """
    username = (req.username or "").strip()
    phone = (req.phone or "").strip()
    email = (req.email or "").strip()
    if not username:
        return ResponseBase.error("用户名不能为空", 422)
    if db.query(User).filter(User.username == username).first():
        return ResponseBase.error("用户名已存在", 409)
    if phone and db.query(User).filter(User.phone == phone).first():
        return ResponseBase.error("该手机号已注册，请直接登录", 409)
    if email and db.query(User).filter(User.email == email).first():
        return ResponseBase.error("该邮箱已注册", 409)

    now = datetime.now(timezone.utc)
    user = User(
        username=username,
        phone=phone or None,
        email=email or None,
        password_hash=AuthService.hash_password(req.password),
        nickname=username,
        register_time=now,
        last_login_time=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthService.create_access_token(user.id)
    return ResponseBase.success({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "phone": user.phone or "",
            "email": user.email or "",
            "nickname": user.nickname,
        }
    })


@router.post("/sms/send")
def send_sms_code(req: SmsSendRequest):
    """发送短信验证码（当前用于找回密码）

    开发渠道（SMS_PROVIDER=mock）在 development 环境会把 demoCode 一起返回，
    方便本地联调；生产环境不会返回验证码。
    """
    try:
        data = SmsService.send_code(req.phone, req.scene)
    except ValueError as exc:
        return ResponseBase.error(str(exc), 400)
    except RuntimeError as exc:
        return ResponseBase.error(str(exc), 503)
    return ResponseBase.success(data, "验证码已发送")


@router.post("/password/reset")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """用短信验证码重置密码（验证码一次性使用）"""
    if not SmsService.verify_code(req.phone, req.code, "reset"):
        return ResponseBase.error("验证码不正确或已过期", 400)

    user = db.query(User).filter(User.phone == (req.phone or "").strip()).first()
    if not user:
        return ResponseBase.error("该手机号未注册，请先注册", 404)
    if user.status != 1:
        return ResponseBase.error("账号已被禁用", 403)

    user.password_hash = AuthService.hash_password(req.new_password)
    db.commit()
    return ResponseBase.success(None, "密码已重置，请用新密码登录")


@router.get("/info")
def get_info(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    if user_id == 0:
        return ResponseBase.success({"id": 0, "nickname": "游客", "is_guest": True})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ResponseBase.error("用户不存在", 404)
    return ResponseBase.success({
        "id": user.id,
        "username": user.username or "",
        "email": user.email or "",
        "phone": user.phone or "",
        "nickname": user.nickname,
        "avatar": user.avatar,
        "gender": user.gender,
        "register_time": str(user.register_time) if user.register_time else "",
    })
