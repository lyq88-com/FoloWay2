# -*- coding: utf-8 -*-
"""
Service 导出
"""
from app.services.auth_service import AuthService
from app.services.ai_service import AIService
from app.services.emotion_service import EmotionService
from app.services.crisis_service import CrisisService
from app.services.archive_service import ArchiveService
from app.services.storage_service import StorageService, LocalStorage, get_storage

__all__ = [
    "AuthService",
    "AIService",
    "EmotionService",
    "CrisisService",
    "ArchiveService",
    "StorageService",
    "LocalStorage",
    "get_storage",
]
