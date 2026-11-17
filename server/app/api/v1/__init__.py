# -*- coding: utf-8 -*-
"""
API v1 路由导出
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.user import router as user_router
from app.api.v1.habit import router as habit_router
from app.api.v1.emotion import router as emotion_router
from app.api.v1.mindfulness import router as mindfulness_router
from app.api.v1.chat import router as chat_router
from app.api.v1.stats import router as stats_router
from app.api.v1.archive import router as archive_router

api_router = APIRouter(prefix="/api/v1")

# 注册所有子路由
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(habit_router)
api_router.include_router(emotion_router)
api_router.include_router(mindfulness_router)
api_router.include_router(chat_router)
api_router.include_router(stats_router)
api_router.include_router(archive_router)

__all__ = ["api_router"]
