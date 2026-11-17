# -*- coding: utf-8 -*-
"""
ORM 模型导出 - 统一入口
导入所有模型以便 Alembic 迁移和 FastAPI 自动文档生成
"""
from app.models.user import User, Admin
from app.models.habit import TaskTemplate, Habit, Checkin, CheckinItem, DifficultyLog
from app.models.chat import AIRole, AIRoleAsset, ChatSession, ChatMessage, AIUserMemory, HabitAchievement
from app.models.achievement import Badge, UserBadge
from app.models.emotion import EmotionRecord
from app.models.mindfulness import MindfulnessSession, MindfulnessPlan, AudioResource
from app.models.archive import EmotionReport, GrowthArchive, CheckinDiary, CrisisInterventionLog
from app.models.system import (
    PushTask, PushRecord, DailyReport, SmsCode,
    OperationLog, AppConfig, FileUpload
)
from app.models.voice_diary import VoiceDiary, VoiceDiaryCategory
from app.models.crisis import CrisisContact, EmotionMonitorLog, CrisisResource, UserPrivacySetting
from app.models.companion import CompanionRecord
from app.models.moment import Moment, MomentLike, MomentComment
# === 性格测评(云端) ===
from app.models.personality import UserPersonalityResult
# === 虚拟经济(云端) ===
from app.models.economy import UserEconomy
# === 陪伴感增强 v3（记忆分层/角色人设/扭蛋角色/主动互动） ===
from app.models.persona_ext import GachaCharacterPool, AIProactiveLog
# === 习惯-伙伴融合（生命周期感知 / 习惯话题总开关） ===
from app.models.habit_companion import UserCompanionSetting
# === 四大新增模块模型 ===
from app.models.schedule import Schedule
from app.models.gacha import (
    GachaTemplate, UserGachaWallet, UserGachaRecord, UserGachaFavorite
)
from app.models.world import (
    World, WorldRole, WorldNote, WorldNoteComment,
    WorldPlot, WorldPlotUnlock, WorldRelation
)
# === 小想法 · 共鸣匹配（独立模块，additive：只新增导入，不动既有模型） ===
from app.modules.idea.models import (
    Idea, IdeaResonance, IdeaLike, IdeaSetting,
    IdeaBlock, IdeaConversation, IdeaMessage, IdeaNotification,
)
# === 专注 · AI陪伴监督（独立模块，additive：只新增导入，不动既有模型） ===
from app.modules.focus.models import (
    FocusTask, FocusStep, FocusSession, FocusRecord,
    FocusDynamic, FocusDynamicComment, FocusDynamicLike,
    FocusRemind, FocusFollow, FocusSetting,
)
# === 纯本地玩法上云（独立模块，additive：只新增导入，不动既有模型） ===
from app.modules.play.models import UserPlayState, UserCapsule, ShopOrder

__all__ = [
    # 用户
    "User", "Admin",
    # 习惯
    "TaskTemplate", "Habit", "Checkin", "CheckinItem", "DifficultyLog",
    # AI对话
    "AIRole", "AIRoleAsset", "ChatSession", "ChatMessage",
    "AIUserMemory", "HabitAchievement",
    # 成就
    "Badge", "UserBadge",
    # 情绪
    "EmotionRecord",
    # 正念
    "MindfulnessSession", "MindfulnessPlan", "AudioResource",
    # 档案
    "EmotionReport", "GrowthArchive", "CheckinDiary", "CrisisInterventionLog",
    # 系统
    "PushTask", "PushRecord", "DailyReport", "SmsCode",
    "OperationLog", "AppConfig", "FileUpload",
    # 语音日记
    "VoiceDiary", "VoiceDiaryCategory",
    # 危机干预
    "CrisisContact", "EmotionMonitorLog", "CrisisResource", "UserPrivacySetting",
    # 陪伴模式
    "CompanionRecord",
    # 朋友圈
    "Moment", "MomentLike", "MomentComment",
    # 日程提醒
    "Schedule",
    # 互动扭蛋
    "GachaTemplate", "UserGachaWallet", "UserGachaRecord", "UserGachaFavorite",
    # 世界世界观 + AI笔记
    "World", "WorldRole", "WorldNote", "WorldNoteComment",
    "WorldPlot", "WorldPlotUnlock", "WorldRelation",
    # 性格测评(云端)
    "UserPersonalityResult",
    # 虚拟经济(云端)
    "UserEconomy",
    # 陪伴感增强 v3
    "GachaCharacterPool", "AIProactiveLog",
    # 习惯-伙伴融合
    "UserCompanionSetting",
    # 小想法 · 共鸣匹配
    "Idea", "IdeaResonance", "IdeaLike", "IdeaSetting",
    "IdeaBlock", "IdeaConversation", "IdeaMessage", "IdeaNotification",
    "FocusTask", "FocusStep", "FocusSession", "FocusRecord",
    "FocusDynamic", "FocusDynamicComment", "FocusDynamicLike",
    "FocusRemind", "FocusFollow", "FocusSetting",
    # 纯本地玩法上云
    "UserPlayState", "UserCapsule", "ShopOrder",
]
