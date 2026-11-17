# -*- coding: utf-8 -*-
"""【newfunc 增量-语音包】TTS 请求体 schema"""
from pydantic import BaseModel


class TTSVoiceSettingRequest(BaseModel):
    voice_id: str


class TTSSynthesizeRequest(BaseModel):
    text: str
    voice_id: str = ""   # 不传则走 伙伴绑定 > 用户默认 > 全局默认
    bot_id: int = 0      # 传 bot_id 且未显式指定 voice_id 时，用伙伴专属语音


class TTSBotVoiceRequest(BaseModel):
    voice_id: str
