# -*- coding: utf-8 -*-
"""
AI对话模型 - 角色/素材/会话/消息
"""
from sqlalchemy import Column, BigInteger, ForeignKey, JSON
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATE, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class AIRole(Base):
    """AI角色定义"""
    __tablename__ = "ai_roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_type = Column(VARCHAR(20), nullable=False, unique=True, comment="角色类型 cute/gentle/serious/energetic")
    name = Column(VARCHAR(50), nullable=False, comment="角色名称")
    personality = Column(VARCHAR(255), nullable=False, default="", comment="人格描述")
    description = Column(VARCHAR(255), nullable=False, default="", comment="选择页描述")
    # ↓↓↓ 新增（BUG-001：陪伴对象选择页头像空白） ↓↓↓
    avatar = Column(VARCHAR(32), nullable=False, default="", comment="角色头像emoji")
    # ↑↑↑ 新增结束 ↑↑↑
    system_prompt = Column(TEXT, nullable=True, comment="系统提示词模板")
    # ↓↓↓ 新增（陪伴感增强 v3：完整人设 + 心情状态 + 自捏高级设定 + 音色） ↓↓↓
    backstory = Column(TEXT, nullable=True, comment="人物背景故事线")
    speech_style = Column(VARCHAR(255), nullable=False, default="", comment="专属说话风格")
    quirks = Column(TEXT, nullable=True, comment="小癖好/口头禅")
    mood = Column(VARCHAR(32), nullable=False, default="normal", comment="当前心情 normal/happy/tired/sad/angry/quiet")
    mood_note = Column(VARCHAR(255), nullable=False, default="", comment="状态说明(展示给用户)")
    mood_updated_at = Column(DATETIME, nullable=True, comment="心情更新时间")
    taboos = Column(TEXT, nullable=True, comment="雷区/说话禁忌")
    expression_habits = Column(TEXT, nullable=True, comment="表达习惯(句式/称呼/语气词)")
    angry_style = Column(TEXT, nullable=True, comment="生气时是什么样子")
    happy_style = Column(TEXT, nullable=True, comment="开心时是什么样子")
    voice_tone = Column(VARCHAR(64), nullable=False, default="", comment="音色标识 soft/bright/warm/cool/husky")
    nickname = Column(VARCHAR(64), nullable=False, default="", comment="角色对用户的专属称呼")
    origin = Column(VARCHAR(20), nullable=False, default="official", comment="来源 official/custom/gacha")
    creator_id = Column(BigInteger, nullable=False, default=0, comment="创建者 0=官方")
    # ↑↑↑ 新增结束 ↑↑↑
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    sort_order = Column(INTEGER, nullable=False, default=0, comment="排序值")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class AIRoleAsset(Base):
    """AI角色素材(每角色x6情绪状态)"""
    __tablename__ = "ai_role_assets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("ai_roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID")
    emotion_status = Column(VARCHAR(20), nullable=False, comment="情绪状态 normal/happy/sad/gentle/encourage/chat")
    asset_type = Column(VARCHAR(20), nullable=False, default="image", comment="素材类型 image/animation")
    asset_url = Column(VARCHAR(500), nullable=False, default="", comment="素材URL")
    bubble_text = Column(VARCHAR(100), nullable=False, default="", comment="气泡文字")
    animation_type = Column(VARCHAR(20), nullable=False, default="none", comment="动画类型 bounce/shake/pulse/float/none")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class ChatSession(Base):
    """对话会话"""
    __tablename__ = "chat_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    role_type = Column(VARCHAR(20), nullable=False, default="cute", comment="当前AI角色类型")
    title = Column(VARCHAR(100), nullable=False, default="", comment="会话标题")
    message_count = Column(INTEGER, nullable=False, default=0, comment="消息总数")
    last_message_time = Column(DATETIME, nullable=True, comment="最后消息时间")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1活跃 0归档")
    # === 阶段J扩展字段 (习惯-AI全链路融合) ===
    habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯ID(0=纯聊天会话)")
    emotion_id = Column(BigInteger, nullable=False, default=0, comment="关联情绪记录ID(0=无关联)")
    session_type = Column(VARCHAR(20), nullable=False, default="chat", comment="会话类型 chat/checkin_trigger/emotion_guide/mindfulness")
    dialogue_style = Column(VARCHAR(20), nullable=False, default="gentle", comment="当前对话风格 gentle/analytical/humorous/calm")
    context_summary = Column(TEXT, nullable=True, comment="超过30轮后的早期对话压缩摘要")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class ChatMessage(Base):
    """对话消息(支持上下文记忆)"""
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False, comment="会话ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    role = Column(VARCHAR(20), nullable=False, comment="消息角色 user/assistant/system")
    content = Column(TEXT, nullable=False, comment="消息内容")
    emotion = Column(VARCHAR(20), nullable=False, default="neutral", comment="用户情绪 positive/negative/neutral")
    ai_status = Column(VARCHAR(20), nullable=False, default="chat", comment="AI状态")
    comfort_text = Column(VARCHAR(255), nullable=False, default="", comment="安抚话术(负面情绪时)")
    tokens = Column(INTEGER, nullable=False, default=0, comment="token消耗")
    # === 阶段J扩展字段 (习惯-AI全链路融合) ===
    habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯ID(打卡联动消息时)")
    emotion_id = Column(BigInteger, nullable=False, default=0, comment="关联情绪记录ID")
    message_type = Column(VARCHAR(20), nullable=False, default="normal", comment="消息类型 normal/checkin_link/emotion_guide/achievement/crisis")
    emotion_intensity = Column(TINYINT, nullable=False, default=0, comment="情绪强度分数 0-10")
    is_key_memory = Column(TINYINT, nullable=False, default=0, comment="是否为关键记忆 0否 1是(不会被30轮截断删除)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class AIUserMemory(Base):
    """AI用户长期记忆库 - 存储所有打卡/情绪/对话关键信息供AI上下文调用"""
    __tablename__ = "ai_user_memories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯ID")
    emotion_id = Column(BigInteger, nullable=False, default=0, comment="关联情绪记录ID")
    memory_type = Column(VARCHAR(20), nullable=False, comment="记忆类型 checkin/emotion/chat/achievement/crisis/plan")
    # ↓↓↓ 新增（陪伴感增强 v3：记忆分层 + 角色绑定 + 可删除） ↓↓↓
    memory_layer = Column(VARCHAR(20), nullable=False, default="event",
                          comment="记忆分层 profile长期固定/event对话事件/preference偏好")
    role_key = Column(VARCHAR(64), nullable=False, default="", comment="归属角色标识(空=共享记忆)")
    role_id = Column(BigInteger, nullable=False, default=0, comment="归属角色 ai_roles.id")
    # ↑↑↑ 新增结束 ↑↑↑
    memory_content = Column(TEXT, nullable=False, comment="记忆内容摘要")
    title = Column(VARCHAR(64), nullable=False, default="", comment="记忆标题(列表展示用短标签)")
    salience = Column(TINYINT, nullable=False, default=5, comment="重要度 1-10，越高越优先召回")
    source = Column(VARCHAR(20), nullable=False, default="auto", comment="来源 auto/manual/rule")
    emotion_score = Column(TINYINT, nullable=False, default=5, comment="情绪分数 0-10")
    habit_status = Column(VARCHAR(20), nullable=False, default="", comment="完成状态 completed/failed/partial")
    context_data = Column(JSON, nullable=True, comment="附加上下文数据 {habit_name, difficulty, duration, tags, ...}")
    is_long_term = Column(TINYINT, nullable=False, default=0, comment="是否长期保留 0否 1是(成就/危机/核心诉求)")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除 0正常 1已删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=True, comment="更新时间")


class HabitAchievement(Base):
    """习惯连续打卡成就记录"""
    __tablename__ = "habit_achievements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, comment="习惯ID")
    milestone = Column(INTEGER, nullable=False, comment="成就阈值 7/15/30/60/100")
    character_id = Column(VARCHAR(50), nullable=False, default="linxi", comment="触发时的AI角色ID")
    dialogue_style = Column(VARCHAR(20), nullable=False, default="gentle", comment="对话风格")
    ai_dialogue = Column(TEXT, nullable=True, comment="AI专属剧情台词")
    comic_image_url = Column(VARCHAR(500), nullable=False, default="", comment="AI漫画日记图片URL")
    diary_content = Column(TEXT, nullable=True, comment="AI生成的日记内容")
    is_unlocked = Column(TINYINT, nullable=False, default=0, comment="是否已解锁 0否 1是")
    unlocked_at = Column(DATETIME, nullable=True, comment="解锁时间")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
