# -*- coding: utf-8 -*-
"""
【newfunc 增量-语音包】多语种/方言 TTS 服务
- 语音包/音色注册与自动种子（韩语、日语、粤语、四川话 + 原有普通话）
- 后端 TTS 合成（edge-tts 供应商，可扩展 azure/gtts/本地引擎）
- md5 文本级音频缓存（命中不重复请求供应商）
- 三级音色解析与异常兜底：显式指定 > AI伙伴绑定 > 用户默认 > 全局默认；
  语种不支持 / 供应商异常时自动回退默认语音
不引用、不修改任何原有语音代码（app/services/voice_service.py 仅做 ASR 识别，互不相干）。
"""
import asyncio
import hashlib
import os

from sqlalchemy.orm import Session

from app.modules.newfunc.models import AIBotInfo
from app.modules.newfunc.voice.voice_models import (
    TTSBotVoice, TTSCache, TTSVoicePack, TTSVoiceTimbre, TTSUserSetting,
)

# 服务端音频缓存目录（server/tts_cache_audio/）
SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
AUDIO_DIR = os.path.join(SERVER_ROOT, "tts_cache_audio")

# 全局默认音色 = 原有普通话语音（回退链终点）
# 注意：edge 供应商偶尔会下架/屏蔽个别音色（表现为 NoAudioReceived），
# 晓晓(zh-CN-XiaoxiaoNeural) 在某些网络下已无法合成，故默认改用晓伊。
DEFAULT_VOICE = "zh-CN-XiaoyiNeural"

# 供应商异常时的兜底音色顺序（去重后依次尝试，全部失败才报错）
FALLBACK_VOICES = [
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunjianNeural",
    "zh-TW-HsiaoChenNeural",
]

# 语音包注册表：后续新增语种/方言只需在此追加一条并重启（详见配置文档）
VOICE_PACK_REGISTRY = [
    {
        "pack_code": "zh-default", "name": "原有语音（普通话）",
        "lang_code": "zh", "region": "CN", "sort": 1,
        "sample_text": "你好，我是循途的AI伙伴，欢迎使用循途。",
        "timbres": [
            {"voice_id": "zh-CN-XiaoxiaoNeural", "name": "晓晓（温柔女声）", "gender": "female", "is_default": 0},
            {"voice_id": "zh-CN-XiaoyiNeural", "name": "晓伊（活力少女）", "gender": "female", "is_default": 1},
            {"voice_id": "zh-CN-YunxiNeural", "name": "云希（清朗男声）", "gender": "male", "is_default": 0},
            {"voice_id": "zh-CN-YunjianNeural", "name": "云健（阳光男声）", "gender": "male", "is_default": 0},
            {"voice_id": "zh-CN-YunyangNeural", "name": "云扬（沉稳男声）", "gender": "male", "is_default": 0},
        ],
    },
    {
        "pack_code": "ko-kr", "name": "韩语语音包",
        "lang_code": "ko", "region": "KR", "sort": 2,
        "sample_text": "안녕하세요, 저는 순도의 AI 파트너예요. 만나서 반가워요!",
        "timbres": [
            {"voice_id": "ko-KR-SunHiNeural", "name": "선희（女声）", "gender": "female", "is_default": 1},
            {"voice_id": "ko-KR-InJoonNeural", "name": "인준（男声）", "gender": "male", "is_default": 0},
        ],
    },
    {
        "pack_code": "ja-jp", "name": "日语语音包",
        "lang_code": "ja", "region": "JP", "sort": 3,
        "sample_text": "こんにちは、私は循途のAIパートナーです。よろしくね！",
        "timbres": [
            {"voice_id": "ja-JP-NanamiNeural", "name": "七海（女声）", "gender": "female", "is_default": 1},
            {"voice_id": "ja-JP-KeitaNeural", "name": "圭太（男声）", "gender": "male", "is_default": 0},
        ],
    },
    {
        "pack_code": "zh-hk", "name": "粤语语音包",
        "lang_code": "yue", "region": "HK", "sort": 4,
        "sample_text": "你好呀，我係循途嘅AI夥伴，好開心識到你！",
        "timbres": [
            {"voice_id": "zh-HK-HiuMaanNeural", "name": "曉曼（女声）", "gender": "female", "is_default": 1},
            {"voice_id": "zh-HK-HiuGaaiNeural", "name": "曉佳（温柔女声）", "gender": "female", "is_default": 0},
            {"voice_id": "zh-HK-WanLungNeural", "name": "雲龍（男声）", "gender": "male", "is_default": 0},
        ],
    },
    {
        "pack_code": "zh-liaoning", "name": "东北话语音包",
        "lang_code": "zh", "region": "CN-Liaoning", "sort": 5,
        "sample_text": "哎呀妈呀，我是循途的AI伙伴，老好使了！",
        "timbres": [
            {"voice_id": "zh-CN-liaoning-XiaobeiNeural", "name": "小北（女声）", "gender": "female", "is_default": 1},
        ],
    },
    {
        "pack_code": "zh-shaanxi", "name": "陕西话语音包",
        "lang_code": "zh", "region": "CN-Shaanxi", "sort": 6,
        "sample_text": "额是循途的AI伙伴，嘹咋咧！",
        "timbres": [
            {"voice_id": "zh-CN-shaanxi-XiaoniNeural", "name": "小妮（女声）", "gender": "female", "is_default": 1},
        ],
    },
    {
        "pack_code": "zh-tw", "name": "台湾腔语音包",
        "lang_code": "zh", "region": "TW", "sort": 7,
        "sample_text": "嗨，我是循途的AI伙伴，很開心認識你！",
        "timbres": [
            {"voice_id": "zh-TW-HsiaoChenNeural", "name": "曉臻（温柔女声）", "gender": "female", "is_default": 1},
            {"voice_id": "zh-TW-HsiaoYuNeural", "name": "曉雨（甜美女声）", "gender": "female", "is_default": 0},
            {"voice_id": "zh-TW-YunJheNeural", "name": "雲哲（男声）", "gender": "male", "is_default": 0},
        ],
    },
    {
        "pack_code": "en-us", "name": "英语语音包",
        "lang_code": "en", "region": "US", "sort": 8,
        "sample_text": "Hi, I'm your AI companion from Xuntu. It's so nice to meet you!",
        "timbres": [
            {"voice_id": "en-US-AvaNeural", "name": "Ava（温柔女声）", "gender": "female", "is_default": 1},
            {"voice_id": "en-US-EmmaNeural", "name": "Emma（知性女声）", "gender": "female", "is_default": 0},
            {"voice_id": "en-US-AndrewNeural", "name": "Andrew（磁性男声）", "gender": "male", "is_default": 0},
            {"voice_id": "en-US-AnaNeural", "name": "Ana（童声）", "gender": "female", "is_default": 0},
        ],
    },
    # 注：四川话等其他方言当前 edge 供应商暂无音色，接入方法见
    # 《多语种语音包接入配置文档》第六节（可换 Azure 定制神经语音等供应商扩展）
]


# ------------------------------------------------------------
# 种子与查询
# ------------------------------------------------------------
def seed_voice_packs(db: Session):
    """幂等种子：按注册表同步语音包/音色（新增补插，注册表已移除的包自动停用）"""
    reg_codes = {pack["pack_code"] for pack in VOICE_PACK_REGISTRY}
    # 注册表外已存在的包 → 停用（不删数据，保留可追溯）
    for row in db.query(TTSVoicePack).all():
        if row.pack_code not in reg_codes and row.is_enabled == 1:
            row.is_enabled = 0
            db.add(row)
    for pack in VOICE_PACK_REGISTRY:
        row = db.query(TTSVoicePack).filter(
            TTSVoicePack.pack_code == pack["pack_code"]).first()
        if not row:
            row = TTSVoicePack(
                pack_code=pack["pack_code"], name=pack["name"],
                lang_code=pack["lang_code"], region=pack["region"],
                sample_text=pack["sample_text"], provider="edge",
                is_enabled=1, sort=pack["sort"])
            db.add(row)
        for timbre in pack["timbres"]:
            exists = db.query(TTSVoiceTimbre).filter(
                TTSVoiceTimbre.voice_id == timbre["voice_id"]).first()
            if not exists:
                db.add(TTSVoiceTimbre(
                    pack_code=pack["pack_code"], voice_id=timbre["voice_id"],
                    name=timbre["name"], gender=timbre["gender"],
                    is_default=timbre["is_default"], is_enabled=1))
            elif exists.is_default != timbre["is_default"]:
                # 注册表是默认音色的唯一出处：默认音色变更时同步旧数据
                exists.is_default = timbre["is_default"]
                db.add(exists)
    db.commit()


def enabled_voice_ids(db: Session) -> set:
    """当前启用的全部音色ID集合（回退判定依据）"""
    return {v.voice_id for v in db.query(TTSVoiceTimbre).filter(
        TTSVoiceTimbre.is_enabled == 1).all()}


def list_voices(db: Session):
    """语音包列表（含音色明细），首次调用自动种子"""
    seed_voice_packs(db)
    packs = db.query(TTSVoicePack).filter(
        TTSVoicePack.is_enabled == 1).order_by(TTSVoicePack.sort).all()
    timbres = db.query(TTSVoiceTimbre).filter(
        TTSVoiceTimbre.is_enabled == 1).all()
    by_pack = {}
    for t in timbres:
        by_pack.setdefault(t.pack_code, []).append({
            "voice_id": t.voice_id, "name": t.name, "gender": t.gender,
            "is_default": bool(t.is_default),
        })
    result = []
    for p in packs:
        result.append({
            "pack_code": p.pack_code, "name": p.name,
            "lang_code": p.lang_code, "region": p.region,
            "sample_text": p.sample_text, "provider": p.provider,
            "timbres": by_pack.get(p.pack_code, []),
        })
    return result


# ------------------------------------------------------------
# 音色解析（回退链）与用户/伙伴设置
# ------------------------------------------------------------
def get_or_create_user_setting(db: Session, uid: int) -> TTSUserSetting:
    s = db.query(TTSUserSetting).filter(TTSUserSetting.uid == uid).first()
    if not s:
        s = TTSUserSetting(uid=uid, voice_id=DEFAULT_VOICE)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def set_user_voice(db: Session, uid: int, voice_id: str):
    """设置用户默认音色；音色不存在返回 None"""
    seed_voice_packs(db)
    exists = db.query(TTSVoiceTimbre).filter(
        TTSVoiceTimbre.voice_id == voice_id,
        TTSVoiceTimbre.is_enabled == 1).first()
    if not exists:
        return None
    s = get_or_create_user_setting(db, uid)
    s.voice_id = voice_id
    db.commit()
    return s


def resolve_voice(db: Session, uid: int, voice_id: str = None,
                  bot_id: int = None) -> dict:
    """
    三级音色解析：显式指定 > AI伙伴绑定 > 用户默认 > 全局默认
    返回 {voice_id, source, fallback, fallback_reason}
    """
    enabled = enabled_voice_ids(db)
    if voice_id:
        if voice_id in enabled:
            return {"voice_id": voice_id, "source": "explicit",
                    "fallback": False, "fallback_reason": ""}
        # 语种/音色不支持 → 兜底回退默认语音
        return {"voice_id": DEFAULT_VOICE, "source": "global_default",
                "fallback": True,
                "fallback_reason": f"语音包或音色不支持: {voice_id}，已回退默认语音"}
    if bot_id:
        bv = db.query(TTSBotVoice).filter(
            TTSBotVoice.bot_id == bot_id, TTSBotVoice.uid == uid).first()
        if bv and bv.voice_id in enabled:
            return {"voice_id": bv.voice_id, "source": "bot_binding",
                    "fallback": False, "fallback_reason": ""}
    s = get_or_create_user_setting(db, uid)
    if s.voice_id in enabled:
        return {"voice_id": s.voice_id, "source": "user_setting",
                "fallback": False, "fallback_reason": ""}
    return {"voice_id": DEFAULT_VOICE, "source": "global_default",
            "fallback": False, "fallback_reason": ""}


def bind_bot_voice(db: Session, uid: int, bot_id: int, voice_id: str):
    """给 AI 伙伴绑定专属语音包音色；伙伴不存在返回 'no_bot'，音色不存在返回 None"""
    bot = db.query(AIBotInfo).filter(
        AIBotInfo.id == bot_id, AIBotInfo.uid == uid,
        AIBotInfo.is_active == 1).first()
    if not bot:
        return "no_bot"
    seed_voice_packs(db)
    exists = db.query(TTSVoiceTimbre).filter(
        TTSVoiceTimbre.voice_id == voice_id,
        TTSVoiceTimbre.is_enabled == 1).first()
    if not exists:
        return None
    bv = db.query(TTSBotVoice).filter(TTSBotVoice.bot_id == bot_id).first()
    if bv:
        bv.voice_id = voice_id
        bv.uid = uid
    else:
        db.add(TTSBotVoice(uid=uid, bot_id=bot_id, voice_id=voice_id))
    db.commit()
    return True


def unbind_bot_voice(db: Session, uid: int, bot_id: int) -> bool:
    bv = db.query(TTSBotVoice).filter(
        TTSBotVoice.bot_id == bot_id, TTSBotVoice.uid == uid).first()
    if not bv:
        return False
    db.delete(bv)
    db.commit()
    return True


def get_bot_voice(db: Session, uid: int, bot_id: int) -> dict:
    """查询伙伴当前生效音色（含解析来源）"""
    bv = db.query(TTSBotVoice).filter(
        TTSBotVoice.bot_id == bot_id, TTSBotVoice.uid == uid).first()
    resolved = resolve_voice(db, uid, bot_id=bot_id)
    return {
        "bot_id": bot_id,
        "bound_voice_id": bv.voice_id if bv else "",
        "effective_voice_id": resolved["voice_id"],
        "source": resolved["source"],
    }


# ------------------------------------------------------------
# TTS 合成（供应商封装 + 缓存 + 兜底回退）
# ------------------------------------------------------------
def _cache_key(voice_id: str, text: str) -> str:
    return hashlib.md5(f"{voice_id}|{text}".encode("utf-8")).hexdigest()


async def _edge_synthesize(text: str, voice_id: str, out_path: str) -> int:
    """edge-tts 供应商合成，返回音频字节数"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice_id)
    await asyncio.wait_for(communicate.save(out_path), timeout=30)
    return os.path.getsize(out_path)


def _synthesize_by_provider(provider: str, text: str, voice_id: str,
                            out_path: str) -> int:
    """供应商统一入口；后续新增 azure/gtts 供应商在此分支扩展"""
    if provider in ("edge", "azure"):
        return asyncio.run(_edge_synthesize(text, voice_id, out_path))
    raise ValueError(f"不支持的TTS供应商: {provider}")


def synthesize(db: Session, uid: int, text: str, voice_id: str = None,
               bot_id: int = None) -> dict:
    """
    文本转语音（带缓存与三级兜底）：
    1) 解析目标音色（显式 > 伙伴绑定 > 用户默认 > 全局默认）
    2) 语种/音色不支持 → 回退默认语音
    3) 供应商合成异常 → 回退默认语音再试
    4) 默认语音也异常 → 返回 __error__（router 层转 500）
    返回 dict（含 __error__ 时为失败）
    """
    text = (text or "").strip()[:1000]
    if not text:
        return {"__error__": "文本不能为空", "__code__": 400}

    seed_voice_packs(db)
    pack = db.query(TTSVoicePack).filter(
        TTSVoicePack.pack_code == "zh-default").first()
    provider = pack.provider if pack else "edge"

    resolved = resolve_voice(db, uid, voice_id=voice_id, bot_id=bot_id)
    target_voice = resolved["voice_id"]
    fallback = resolved["fallback"]
    fallback_reason = resolved["fallback_reason"]

    def _try(voice: str):
        key = _cache_key(voice, text)
        # 1. 缓存命中：直接回音频，不重复请求供应商
        row = db.query(TTSCache).filter(TTSCache.cache_key == key).first()
        if row:
            from datetime import datetime
            row.hits = (row.hits or 0) + 1
            row.last_hit_at = datetime.now()
            db.commit()
            return {"cached": True, "key": key, "row": row, "voice": voice}
        # 2. 缓存未命中：调供应商合成并落盘
        if not os.path.isdir(AUDIO_DIR):
            os.makedirs(AUDIO_DIR, exist_ok=True)
        out_path = os.path.join(AUDIO_DIR, f"{key}.mp3")
        last_error = ""
        # 供应商偶发 NoAudioReceived，同一音色重试一次再判定失败
        for _attempt in range(2):
            try:
                size = _synthesize_by_provider(provider, text, voice, out_path)
            except Exception as e:  # 供应商/网络异常 → 重试或交给上层回退
                last_error = str(e)
                continue
            from datetime import datetime
            row = TTSCache(cache_key=key, voice_id=voice, text=text,
                           audio_path=f"{key}.mp3", audio_format="mp3",
                           size_bytes=size, hits=0, last_hit_at=datetime.now())
            db.add(row)
            db.commit()
            return {"cached": False, "key": key, "row": row, "voice": voice}
        return {"error": last_error}

    r = _try(target_voice)
    # 供应商异常 → 按 DEFAULT_VOICE / FALLBACK_VOICES 依次兜底，全部失败才报错
    if "error" in r:
        last_error = r["error"]
        tried = {target_voice}
        for voice in [DEFAULT_VOICE] + FALLBACK_VOICES:
            if voice in tried:
                continue
            tried.add(voice)
            r = _try(voice)
            if "error" not in r:
                fallback = True
                fallback_reason = (
                    f"音色 {target_voice} 合成异常({last_error[:80]})，已回退 {voice}"
                )
                break
            last_error = r["error"]
    if "error" in r:
        return {"__error__": f"TTS合成失败: {r['error']}", "__code__": 502}

    return {
        "cache_key": r["key"],
        "audio_url": f"/api/newfunc/tts/audio/{r['key']}",
        "voice_id": r["voice"],
        "requested_voice_id": voice_id or "",
        "bot_id": bot_id or 0,
        "resolved_source": resolved["source"],
        "cached": r["cached"],
        "fallback": fallback,
        "fallback_reason": fallback_reason,
        "audio_format": r["row"].audio_format,
        "size_bytes": r["row"].size_bytes,
        "text": text,
    }


def get_cache_row(db: Session, cache_key: str):
    return db.query(TTSCache).filter(TTSCache.cache_key == cache_key).first()


def cache_stats(db: Session) -> dict:
    from sqlalchemy import func as sfunc
    total = db.query(sfunc.count(TTSCache.id),
                     sfunc.coalesce(sfunc.sum(TTSCache.size_bytes), 0),
                     sfunc.coalesce(sfunc.sum(TTSCache.hits), 0)).first()
    return {"count": int(total[0] or 0), "total_bytes": int(total[1] or 0),
            "total_hits": int(total[2] or 0), "audio_dir": AUDIO_DIR}


def cache_clear(db: Session) -> int:
    """清空缓存记录与音频文件，返回清理条数"""
    rows = db.query(TTSCache).all()
    n = 0
    for row in rows:
        path = os.path.join(AUDIO_DIR, row.audio_path)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
        db.delete(row)
        n += 1
    db.commit()
    return n
