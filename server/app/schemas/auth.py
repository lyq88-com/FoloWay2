# -*- coding: utf-8 -*-
"""
认证Schema
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")
    code: str = Field(default="", description="短信验证码(验证码登录时)")


class RegisterRequest(BaseModel):
    """注册请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    nickname: str = Field(default="", description="昵称")
    code: str = Field(..., description="短信验证码")


class GuestLoginRequest(BaseModel):
    """游客登录"""
    nickname: str = Field(default="游客", description="昵称")


class UsernameLoginRequest(BaseModel):
    """统一账号登录（用户名或手机号）"""
    username: str = Field(..., description="登录用户名或手机号")
    password: str = Field(..., description="密码")


class UsernameRegisterRequest(BaseModel):
    """统一账号注册"""
    username: str = Field(..., description="登录用户名")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    email: str = Field(default="", description="邮箱(选填)")
    phone: str = Field(default="", description="手机号(选填，用于后续手机号登录)")


class SmsSendRequest(BaseModel):
    """短信验证码发送请求"""
    phone: str = Field(..., description="手机号")
    scene: str = Field(default="reset", description="使用场景 reset=找回密码")


class ResetPasswordRequest(BaseModel):
    """短信验证码重置密码"""
    phone: str = Field(..., description="注册手机号")
    code: str = Field(..., description="短信验证码")
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码(至少8位)")


class TokenResponse(BaseModel):
    """Token响应"""
    token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 604800
    user_info: dict = {}


class UserInfo(BaseModel):
    """用户信息"""
    id: int = 0
    phone: str = ""
    nickname: str = ""
    avatar: str = ""
    gender: int = 0
    register_time: str = ""
