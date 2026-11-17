# -*- coding: utf-8 -*-
"""
【newfunc 增量-语音包】语音包 5 张表幂等建表脚本
运行：cd server && python -m app.modules.newfunc.voice.voice_init_tables
"""
from app.core.database import engine
from app.modules.newfunc.voice.voice_models import (
    TTSBotVoice, TTSCache, TTSUserSetting, TTSVoicePack, TTSVoiceTimbre,
)

TABLES = [TTSVoicePack.__table__, TTSVoiceTimbre.__table__, TTSCache.__table__,
          TTSUserSetting.__table__, TTSBotVoice.__table__]


def init_voice_tables():
    for t in TABLES:
        t.create(bind=engine, checkfirst=True)
    print("[voice_init_tables] done:", [t.name for t in TABLES])


if __name__ == "__main__":
    init_voice_tables()
