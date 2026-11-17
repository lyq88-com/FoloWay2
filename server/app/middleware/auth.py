# -*- coding: utf-8 -*-
"""
JWT认证中间件
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.auth_service import AuthService

security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> int:
    """从请求中获取当前用户ID"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user_id = AuthService.get_user_id_from_token(token)
        if user_id is not None:
            # ↓↓↓ 安全合规批次：已注销（禁用）账号拦截，全站接口统一返回 401 ↓↓↓
            if user_id and user_id > 0:
                try:
                    from app.core.database import SessionLocal
                    from app.models.user import User
                    db = SessionLocal()
                    try:
                        u = db.query(User).filter(User.id == user_id).first()
                        if u is not None and u.status == 0:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="账号已注销",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                    finally:
                        db.close()
                except HTTPException:
                    raise
                except Exception:
                    pass  # 状态查询失败不阻塞鉴权主流程
            # ↑↑↑ 新增结束 ↑↑↑
            return user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(request: Request) -> dict:
    """从请求中获取当前管理员（管理后台专用）

    与 C 端 token 严格区分：只接受 type=admin 的 JWT，
    因此普通用户的 token 无法访问 /admin/* 接口。
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = AuthService.decode_token(auth_header[7:])
        if payload and payload.get("type") == "admin":
            try:
                admin_id = int(payload.get("sub", 0))
            except (TypeError, ValueError):
                admin_id = 0
            if admin_id > 0:
                # 校验账号仍然存在且启用（管理员被禁用后旧 token 立即失效）
                from app.core.database import SessionLocal
                from app.models.user import Admin
                db = SessionLocal()
                try:
                    admin = db.query(Admin).filter(Admin.id == admin_id).first()
                finally:
                    db.close()
                if admin is not None and int(admin.status or 0) == 1:
                    return {
                        "id": admin.id,
                        "username": admin.username,
                        "nickname": admin.nickname,
                        "role": payload.get("role") or admin.role,
                    }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="管理员未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
