# -*- coding: utf-8 -*-
"""
【newfunc 增量-语音包】TTS 路由 —— 全部挂在 /api/newfunc/tts/ 前缀下
（由 newfunc/router.py 末尾 include，与 /api/v1 原有语音接口完全隔离）
"""
import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.modules.newfunc.voice import voice_service
from app.modules.newfunc.voice.voice_schemas import (
    TTSBotVoiceRequest, TTSSynthesizeRequest, TTSVoiceSettingRequest,
)

tts_router = APIRouter(prefix="/tts", tags=["newfunc语音包"])

CONTENT_TYPES = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg"}


def _err(result):
    code = result.get("__code__", 400)
    return ResponseBase.error(message=result["__error__"], code=code)


# ---------- 语音包与音色 ----------
@tts_router.get("/voices")
def list_voices(user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """语音包列表（韩语/日语/粤语/四川话/原有普通话 + 音色明细），首次自动种子"""
    return ResponseBase.success(voice_service.list_voices(db))


@tts_router.get("/setting")
def get_setting(user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    s = voice_service.get_or_create_user_setting(db, user_id)
    return ResponseBase.success({"voice_id": s.voice_id})


@tts_router.post("/setting")
def set_setting(payload: TTSVoiceSettingRequest,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """设置用户默认语音音色（前端语音包选择页）"""
    s = voice_service.set_user_voice(db, user_id, payload.voice_id)
    if s is None:
        return ResponseBase.error(message="音色不存在或未启用", code=404)
    return ResponseBase.success({"voice_id": s.voice_id})


# ---------- 文本转语音（缓存 + 兜底） ----------
@tts_router.post("/synthesize")
def synthesize(payload: TTSSynthesizeRequest,
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """文本转语音：AI对话朗读/内容朗读统一入口，命中缓存不重复请求供应商"""
    result = voice_service.synthesize(
        db, user_id, payload.text,
        voice_id=payload.voice_id or None, bot_id=payload.bot_id or None)
    if "__error__" in result:
        return _err(result)
    return ResponseBase.success(result)


@tts_router.get("/audio/{cache_key}")
def get_audio(cache_key: str,
              user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """获取缓存的音频文件流"""
    row = voice_service.get_cache_row(db, cache_key)
    if not row:
        return ResponseBase.error(message="音频不存在或已过期", code=404)
    path = os.path.join(voice_service.AUDIO_DIR, row.audio_path)
    if not os.path.isfile(path):
        return ResponseBase.error(message="音频文件缺失", code=404)
    return FileResponse(path, media_type=CONTENT_TYPES.get(
        row.audio_format, "application/octet-stream"),
        filename=f"{cache_key}.{row.audio_format}")


# ---------- AI 伙伴专属语音包绑定 ----------
@tts_router.get("/bots/{bot_id}/voice")
def get_bot_voice(bot_id: int,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return ResponseBase.success(voice_service.get_bot_voice(db, user_id, bot_id))


@tts_router.post("/bots/{bot_id}/voice")
def bind_bot_voice(bot_id: int, payload: TTSBotVoiceRequest,
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """AI 伙伴绑定专属语音包音色（不同人设搭配不同语种/方言）"""
    result = voice_service.bind_bot_voice(db, user_id, bot_id, payload.voice_id)
    if result == "no_bot":
        return ResponseBase.error(message="AI伙伴不存在", code=404)
    if result is None:
        return ResponseBase.error(message="音色不存在或未启用", code=404)
    return ResponseBase.success(voice_service.get_bot_voice(db, user_id, bot_id))


@tts_router.delete("/bots/{bot_id}/voice")
def unbind_bot_voice(bot_id: int,
                     user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """解绑伙伴语音 → 该伙伴回退到用户默认语音"""
    ok = voice_service.unbind_bot_voice(db, user_id, bot_id)
    if not ok:
        return ResponseBase.error(message="该伙伴未绑定语音", code=404)
    return ResponseBase.success({"bot_id": bot_id, "unbind": True})


# ---------- 缓存管理 ----------
@tts_router.get("/cache/stats")
def cache_stats(user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return ResponseBase.success(voice_service.cache_stats(db))


@tts_router.post("/cache/clear")
def cache_clear(user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    n = voice_service.cache_clear(db)
    return ResponseBase.success({"cleared": n})
