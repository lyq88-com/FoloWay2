# -*- coding: utf-8 -*-
"""
newfunc 模块数据模型 —— 5 张独立新表（见 migrations/004_newfunc_modules.sql）
push_record / push_setting / user_diary_mood / ai_bot_info / ai_bot_memory
只读引用旧表（habits/checkins/schedules/emotion_records），不建立外键、不修改旧表。
"""
from sqlalchemy import Column, BigInteger, JSON, TEXT
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATE, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class PushRecord(Base):
    """推送记录（消息通知中心数据源）"""
    __tablename__ = "push_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    push_type = Column(VARCHAR(20), nullable=False, default="ai_companion",
                       comment="推送类型 checkin_remind/todo_due/ai_companion/test")
    title = Column(VARCHAR(100), nullable=False, default="", comment="通知标题")
    content = Column(VARCHAR(500), nullable=False, default="", comment="通知内容")
    ref_id = Column(BigInteger, nullable=False, default=0, comment="关联业务ID")
    jump_page = Column(VARCHAR(200), nullable=False, default="", comment="点击跳转页面")
    channel = Column(VARCHAR(20), nullable=False, default="local",
                     comment="发送通道 getui/local")
    is_read = Column(TINYINT, nullable=False, default=0, comment="是否已读 0否 1是")
    status = Column(TINYINT, nullable=False, default=1, comment="1正常 0删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id, "uid": self.uid, "push_type": self.push_type,
            "title": self.title, "content": self.content, "ref_id": self.ref_id,
            "jump_page": self.jump_page, "channel": self.channel,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class PushSetting(Base):
    """推送设置（每用户一行）"""
    __tablename__ = "push_setting"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="用户ID")
    push_enabled = Column(TINYINT, nullable=False, default=1, comment="总开关")
    checkin_push_enabled = Column(TINYINT, nullable=False, default=1, comment="打卡提醒开关")
    checkin_push_time = Column(VARCHAR(5), nullable=False, default="21:30", comment="打卡提醒时间")
    todo_push_enabled = Column(TINYINT, nullable=False, default=1, comment="待办提醒开关")
    ai_push_enabled = Column(TINYINT, nullable=False, default=1, comment="AI陪伴开关")
    ai_frequency = Column(VARCHAR(10), nullable=False, default="medium",
                          comment="AI消息频率 low/medium/high")
    quiet_enabled = Column(TINYINT, nullable=False, default=0, comment="免打扰开关")
    quiet_start = Column(VARCHAR(5), nullable=False, default="23:00", comment="免打扰开始")
    quiet_end = Column(VARCHAR(5), nullable=False, default="08:00", comment="免打扰结束")
    diary_read_auth = Column(TINYINT, nullable=False, default=0,
                             comment="授权AI读取全局情绪日历 0否 1是")
    # 【模块4·群推送】独立群聊消息提醒开关（新增列，不影响原有字段与索引）
    group_push_enabled = Column(TINYINT, nullable=False, default=1,
                                comment="群聊消息提醒开关 0关 1开")
    client_id = Column(VARCHAR(100), nullable=False, default="", comment="个推CID")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    def to_dict(self):
        return {
            "push_enabled": bool(self.push_enabled),
            "checkin_push_enabled": bool(self.checkin_push_enabled),
            "checkin_push_time": self.checkin_push_time,
            "todo_push_enabled": bool(self.todo_push_enabled),
            "ai_push_enabled": bool(self.ai_push_enabled),
            "ai_frequency": self.ai_frequency,
            "quiet_enabled": bool(self.quiet_enabled),
            "quiet_start": self.quiet_start,
            "quiet_end": self.quiet_end,
            "diary_read_auth": bool(self.diary_read_auth),
            # 【模块4·群推送】群聊消息提醒开关
            "group_push_enabled": bool(self.group_push_enabled),
            "client_id": self.client_id,
        }


class UserDiaryMood(Base):
    """情绪日记日历（按日期聚合；情绪明细只读旧表 emotion_records）"""
    __tablename__ = "user_diary_mood"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="用户ID")
    diary_date = Column(DATE, nullable=False, comment="归属日期")
    mood_tags = Column(JSON, nullable=True, comment='情绪标签数组 ["calm","tired"]')
    mood_score = Column(TINYINT, nullable=False, default=5, comment="当日心情分 0-10")
    diary_text = Column(TEXT, nullable=True, comment="日记正文")
    summary = Column(VARCHAR(1000), nullable=False, default="", comment="当日总结")
    summary_source = Column(VARCHAR(10), nullable=False, default="",
                            comment="总结来源 manual/ai")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id, "diary_date": self.diary_date.strftime("%Y-%m-%d"),
            "mood_tags": self.mood_tags or [], "mood_score": self.mood_score,
            "diary_text": self.diary_text or "", "summary": self.summary,
            "summary_source": self.summary_source,
        }


class AIBotInfo(Base):
    """AI 伙伴人设（用户自建）"""
    __tablename__ = "ai_bot_info"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    name = Column(VARCHAR(30), nullable=False, comment="伙伴名称")
    avatar = Column(VARCHAR(20), nullable=False, default="🌿", comment="头像emoji")
    personality = Column(VARCHAR(300), nullable=False, default="", comment="性格描述")
    speak_style = Column(VARCHAR(300), nullable=False, default="", comment="说话风格")
    self_intro = Column(VARCHAR(500), nullable=False, default="", comment="自述/背景设定")
    taboo = Column(VARCHAR(300), nullable=False, default="", comment="禁忌")
    allow_push = Column(TINYINT, nullable=False, default=1, comment="允许主动陪伴 0否 1是")
    is_active = Column(TINYINT, nullable=False, default=1, comment="1正常 0已删除")
    last_chat_at = Column(DATETIME, nullable=True, comment="最近对话时间")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "avatar": self.avatar,
            "personality": self.personality, "speak_style": self.speak_style,
            "self_intro": self.self_intro, "taboo": self.taboo,
            "allow_push": bool(self.allow_push),
            "last_chat_at": self.last_chat_at.strftime("%Y-%m-%d %H:%M:%S") if self.last_chat_at else "",
            "memory_count": 0,
        }


class AIBotMemory(Base):
    """AI 伙伴隔离记忆（bot_id 为隔离边界，互不互通）"""
    __tablename__ = "ai_bot_memory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, nullable=False, comment="伙伴ID(隔离边界)")
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    mem_type = Column(VARCHAR(20), nullable=False, default="fact",
                      comment="记忆类型 fact/preference/emotion/dialogue")
    content = Column(VARCHAR(500), nullable=False, comment="记忆内容")
    importance = Column(TINYINT, nullable=False, default=5, comment="重要度 1-10")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id, "bot_id": self.bot_id, "mem_type": self.mem_type,
            "content": self.content, "importance": self.importance,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }
