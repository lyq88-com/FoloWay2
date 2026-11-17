# -*- coding: utf-8 -*-
"""
认证服务 - JWT生成/验证 + 密码哈希
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int, extra: dict = None) -> str:
        """生成 JWT Token"""
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_admin_token(admin_id: int, role: str = "admin") -> str:
        """生成管理员 Token"""
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_admin_expire_hours)
        payload = {
            "sub": str(admin_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "admin",
            "role": role,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """解码验证 Token"""
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """从 Token 获取用户ID"""
        payload = AuthService.decode_token(token)
        if payload and payload.get("type") == "access":
            try:
                return int(payload.get("sub", 0))
            except (ValueError, TypeError):
                return None
        return None
