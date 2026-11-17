# -*- coding: utf-8 -*-
"""
【newfunc 增量-语音包】多语种/方言 TTS 数据模型 —— 5 张独立新表
（见 migrations/005_newfunc_voice.sql）
tts_voice_pack / tts_voice_timbre / tts_cache / tts_user_setting / tts_bot_voice
不修改任何旧表，bot_id / uid 仅逻辑关联、无外键。
"""
from sqlalchemy import BigInteger, INT, Column
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class TTSVoicePack(Base):
    """语音包（语种/方言维度）"""
    __tablename__ = "tts_voice_pack"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pack_code = Column(VARCHAR(32), nullable=False, unique=True,
                       comment="语音包编码 ko-kr/ja-jp/zh-hk/zh-liaoning/zh-shaanxi/zh-default")
    name = Column(VARCHAR(50), nullable=False, comment="显示名")
    lang_code = Column(VARCHAR(16), nullable=False, comment="BCP-47 语种")
    region = Column(VARCHAR(20), nullable=False, default="", comment="地区")
    sample_text = Column(VARCHAR(200), nullable=False, default="", comment="试听示例文本")
    provider = Column(VARCHAR(20), nullable=False, default="edge",
                      comment="TTS 供应商 edge/azure/local")
    is_enabled = Column(TINYINT, nullable=False, default=1)
    sort = Column(INT, nullable=False, default=0)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class TTSVoiceTimbre(Base):
    """语音包音色明细"""
    __tablename__ = "tts_voice_timbre"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pack_code = Column(VARCHAR(32), nullable=False, comment="所属语音包编码")
    voice_id = Column(VARCHAR(64), nullable=False, unique=True, comment="音色ID")
    name = Column(VARCHAR(50), nullable=False, comment="音色显示名")
    gender = Column(VARCHAR(10), nullable=False, default="female")
    is_default = Column(TINYINT, nullable=False, default=0, comment="该包默认音色")
    is_enabled = Column(TINYINT, nullable=False, default=1)
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class TTSCache(Base):
    """TTS 音频缓存（命中直接回音频，减少重复请求）"""
    __tablename__ = "tts_cache"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cache_key = Column(VARCHAR(40), nullable=False, unique=True,
                       comment="md5(voice_id|text)")
    voice_id = Column(VARCHAR(64), nullable=False)
    text = Column(VARCHAR(2000), nullable=False, comment="合成原文")
    audio_path = Column(VARCHAR(300), nullable=False, comment="音频文件相对路径")
    audio_format = Column(VARCHAR(10), nullable=False, default="mp3")
    size_bytes = Column(INT, nullable=False, default=0)
    hits = Column(INT, nullable=False, default=0, comment="命中次数")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    last_hit_at = Column(DATETIME, nullable=True)


class TTSUserSetting(Base):
    """用户 TTS 默认语音设置（每用户一行）"""
    __tablename__ = "tts_user_setting"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="用户ID")
    voice_id = Column(VARCHAR(64), nullable=False, default="zh-CN-XiaoyiNeural",
                      comment="默认音色（原有普通话音色）")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())


class TTSBotVoice(Base):
    """AI 伙伴专属语音绑定（不同人设伙伴搭配不同语种/方言音色）"""
    __tablename__ = "tts_bot_voice"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False)
    bot_id = Column(BigInteger, nullable=False,
                    comment="AI 伙伴ID（逻辑关联 ai_bot_info.id，无外键）")
    voice_id = Column(VARCHAR(64), nullable=False, comment="绑定音色ID")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
