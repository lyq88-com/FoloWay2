# -*- coding: utf-8 -*-
"""
语音服务 - ASR转写(mock+真实双模式) + 翻译 + 日记CRUD + 统计分析
"""
import os
import json
import uuid
from datetime import date, timedelta, datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.voice_diary import VoiceDiary, VoiceDiaryCategory
from app.services.emotion_service import EmotionService


class ASRError(Exception):
    """
    语音识别业务异常。
    【2026-11-15】真实渠道未配置 / 调用失败时抛出，由路由转成明确错误码；
    绝不再「失败就返回假文本」，避免用户以为录音被正确识别。
    """

    def __init__(self, message: str, code: int = 502):
        super().__init__(message)
        self.message = message
        self.code = code


class ASRService:
    """语音识别服务(ASR) - mock / OpenAI Whisper 兼容双模式"""

    # mock 模式预置转写文本(循环使用, 模拟真实转写)
    MOCK_TRANSCRIPTS = [
        "今天心情很不错，早上去公园跑了五公里，空气特别清新。",
        "工作上遇到了一点小挑战，不过我相信慢慢来总能解决的。",
        "晚上和朋友吃了一顿火锅，聊了很久，感觉整个人都放松下来了。",
        "今天读完了那本一直想看的书，有一些感触想记录下来。",
        "最近在坚持早睡早起，感觉白天的精力比以前好多了。",
        "今天有点累，但完成了一直拖延的任务，还是很有成就感的。",
    ]

    @staticmethod
    def provider_name() -> str:
        """当前渠道名(小写)；mock=本地模拟，其余走 OpenAI Whisper 兼容接口"""
        return (settings.asr_provider or "mock").strip().lower()

    @staticmethod
    def is_configured() -> bool:
        """真实渠道是否具备调用条件(mock 视为已配置)"""
        if ASRService.provider_name() == "mock":
            return True
        return bool(settings.asr_api_key.strip() and settings.asr_api_base.strip())

    @staticmethod
    def status() -> Dict:
        """渠道状态(前端据此提示「语音识别未配置/不可用」)"""
        provider = ASRService.provider_name()
        configured = ASRService.is_configured()
        return {
            "provider": provider,
            "model": settings.asr_model if provider != "mock" else "",
            "configured": configured,
            "mock": provider == "mock",
            "reason": "" if configured else "未配置 ASR_API_KEY（或 ASR_API_BASE 为空）",
        }

    @staticmethod
    def preflight():
        """SSE 等无法回改状态码的场景，在开流前先校验渠道是否可用"""
        if not ASRService.is_configured():
            raise ASRError("语音识别未配置，请联系管理员配置 ASR_API_KEY", 503)

    @staticmethod
    def transcribe(audio_path: str, language: str = "zh") -> str:
        """
        语音转文字(一次性完整转写)
        mock: 返回预置文本; 真实: 调用 OpenAI Whisper 兼容接口
        真实渠道失败时抛 ASRError(不再静默降级成假文本)
        """
        if ASRService.provider_name() == "mock":
            idx = abs(hash(audio_path)) % len(ASRService.MOCK_TRANSCRIPTS)
            return ASRService.MOCK_TRANSCRIPTS[idx]

        if not ASRService.is_configured():
            raise ASRError("语音识别未配置，请联系管理员配置 ASR_API_KEY", 503)
        if not audio_path or not os.path.exists(audio_path):
            raise ASRError("音频文件不存在，请重新录制", 404)

        # 真实模式: OpenAI Whisper 兼容接口
        try:
            import httpx
            with open(audio_path, "rb") as f:
                resp = httpx.post(
                    f"{settings.asr_api_base}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.asr_api_key}"},
                    files={"file": f},
                    data={"model": settings.asr_model, "language": language},
                    timeout=60,
                )
                resp.raise_for_status()
                text = (resp.json().get("text") or "").strip()
        except ASRError:
            raise
        except Exception as e:
            print(f"[ASRService] 真实转写失败: {e}")
            raise ASRError("语音识别服务暂时不可用，请稍后再试", 502)

        if not text:
            raise ASRError("没有识别到有效语音内容，请再说一次", 422)
        return text

    @staticmethod
    def split_phrases(text: str) -> List[str]:
        """按标点把整段转写切成短语片段（SSE 逐段推送 / 模拟实时节奏）"""
        segments = []
        buf = ""
        for ch in text or "":
            buf += ch
            if ch in "，。！？；、,.!?;":
                if len(buf.strip()) >= 2:
                    segments.append(buf.strip())
                buf = ""
        if buf.strip():
            segments.append(buf.strip())
        return segments

    @staticmethod
    def result_meta() -> Dict:
        """转写结果渠道标记（前端据此提示 mock / 真实渠道）"""
        provider = ASRService.provider_name()
        return {
            "provider": "mock" if provider == "mock" else "openai",
            "mock": provider == "mock",
        }


class TranslateService:
    """翻译服务 - mock词典 + 真实API双模式"""

    # mock 模式常用短语词典
    MOCK_DICT = {
        "en": {
            "今天": "today", "心情": "mood", "不错": "good", "很开心": "very happy",
            "工作": "work", "朋友": "friend", "读书": "reading", "跑步": "running",
            "放松": "relax", "开心": "happy", "累": "tired", "早上": "morning",
            "晚上": "evening", "公园": "park", "挑战": "challenge", "坚持": "persist",
            "早睡早起": "early to bed and early to rise", "成就感": "sense of achievement",
        },
        "ja": {"今天": "今日", "心情": "気分", "开心": "嬉しい", "朋友": "友達", "工作": "仕事"},
        "ko": {"今天": "오늘", "心情": "기분", "开心": "행복", "朋友": "친구", "工作": "일"},
        "fr": {"今天": "aujourd'hui", "心情": "humeur", "开心": "heureux", "朋友": "ami"},
        "de": {"今天": "heute", "心情": "Stimmung", "开心": "glücklich", "朋友": "Freund"},
    }

    LANG_NAMES = {"en": "英语", "ja": "日语", "ko": "韩语", "fr": "法语", "de": "德语", "zh": "中文"}

    @staticmethod
    def translate(text: str, target_lang: str = "en") -> Dict:
        """
        文本翻译
        返回: {translation, target_lang, provider}
        """
        if settings.translate_provider == "mock":
            dict_map = TranslateService.MOCK_DICT.get(target_lang, {})
            words = []
            for ch_idx in range(len(text)):
                matched = False
                for zh, tr in dict_map.items():
                    if text.startswith(zh, ch_idx):
                        words.append(tr)
                        # 跳过已匹配部分
                        matched = True
                        break
                if not matched:
                    # 逐字, 无法翻译的字符保留
                    words.append(text[ch_idx])
            # 简单去重连续空格
            translation = " ".join(w for w in words if w.strip()) if words else text
            return {
                "translation": translation,
                "target_lang": target_lang,
                "target_lang_name": TranslateService.LANG_NAMES.get(target_lang, target_lang),
                "provider": "mock",
            }

        # 真实模式: 可对接 DeepL/百度/谷歌翻译API, 此处预留 OpenAI 兼容实现
        try:
            import httpx
            resp = httpx.post(
                f"{settings.ai_api_base}/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={
                    "model": settings.ai_model_name,
                    "messages": [
                        {"role": "system", "content": f"你是翻译引擎, 将文本翻译为{TranslateService.LANG_NAMES.get(target_lang, target_lang)}, 只输出译文"},
                        {"role": "user", "content": text},
                    ],
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            resp.raise_for_status()
            translation = resp.json()["choices"][0]["message"]["content"].strip()
            return {
                "translation": translation,
                "target_lang": target_lang,
                "target_lang_name": TranslateService.LANG_NAMES.get(target_lang, target_lang),
                "provider": "openai",
            }
        except Exception as e:
            print(f"[TranslateService] 真实翻译失败: {e}")
            return {"translation": text, "target_lang": target_lang, "provider": "fallback"}


class VoiceDiaryService:
    """语音日记业务服务"""

    # 默认分类(无需创建即可使用)
    DEFAULT_CATEGORIES = [
        {"id": 0, "name": "日常生活", "key": "daily", "icon": "📖", "color": "#6B8E7B"},
        {"id": 0, "name": "工作记录", "key": "work", "icon": "💼", "color": "#4A90D9"},
        {"id": 0, "name": "学习笔记", "key": "study", "icon": "📚", "color": "#9B59B6"},
        {"id": 0, "name": "旅行游记", "key": "travel", "icon": "✈️", "color": "#E67E22"},
        {"id": 0, "name": "心情随记", "key": "mood", "icon": "💭", "color": "#E74C3C"},
        {"id": 0, "name": "其他", "key": "other", "icon": "🗂️", "color": "#95A5A6"},
    ]

    # 分类key→名称
    CATEGORY_LABELS = {c["key"]: c["name"] for c in DEFAULT_CATEGORIES}

    @staticmethod
    def sentiment_from_text(text: str) -> Dict:
        """
        日记情感分析 - 复用 EmotionService 关键词分析
        返回: {sentiment_score: -5~5, sentiment_label, emotion, confidence}
        """
        result = EmotionService.analyze_emotion(text)
        valence = result.get("valence", "neutral")
        confidence = result.get("confidence", 0)
        if valence == "positive":
            score = max(1, min(5, int(3 + confidence * 2)))
        elif valence == "negative":
            score = min(-1, max(-5, -int(3 + confidence * 2)))
        else:
            score = 0
        return {
            "sentiment_score": score,
            "sentiment_label": valence,
            "emotion": result.get("emotion", "neutral"),
            "confidence": confidence,
        }

    @staticmethod
    def create_diary(db: Session, user_id: int, req) -> VoiceDiary:
        """创建日记(含情感分析)"""
        final_text = req.content_edit if req.content_edit else req.content
        sentiment = VoiceDiaryService.sentiment_from_text(final_text)

        record_date = date.today()
        if req.record_date:
            try:
                record_date = date.fromisoformat(req.record_date)
                if (date.today() - record_date).days > 365:
                    record_date = date.today()
            except ValueError:
                record_date = date.today()

        # 标题为空时取文本前20字
        title = req.title
        if not title and final_text:
            title = final_text[:20]

        diary = VoiceDiary(
            user_id=user_id,
            title=title,
            content=req.content,
            content_edit=req.content_edit,
            audio_url=req.audio_url,
            audio_duration=req.audio_duration,
            audio_size=req.audio_size,
            sample_rate=req.sample_rate,
            language=req.language,
            category=req.category,
            mood=req.mood,
            sentiment_score=sentiment["sentiment_score"],
            sentiment_label=sentiment["sentiment_label"],
            remind_time=req.remind_time,
            record_date=record_date,
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return diary

    @staticmethod
    def list_diaries(db: Session, user_id: int, page: int = 1, page_size: int = 20,
                     category: str = "", start_date: str = "", end_date: str = "",
                     keyword: str = "") -> Dict:
        """日记列表(分页+分类筛选+时间范围+关键词搜索)"""
        query = db.query(VoiceDiary).filter(VoiceDiary.user_id == user_id)

        if category:
            query = query.filter(VoiceDiary.category == category)
        if keyword:
            like = f"%{keyword}%"
            from sqlalchemy import or_
            query = query.filter(or_(
                VoiceDiary.title.like(like),
                VoiceDiary.content.like(like),
                VoiceDiary.content_edit.like(like),
            ))
        if start_date:
            try:
                query = query.filter(VoiceDiary.record_date >= date.fromisoformat(start_date))
            except ValueError:
                pass
        if end_date:
            try:
                query = query.filter(VoiceDiary.record_date <= date.fromisoformat(end_date))
            except ValueError:
                pass

        total = query.count()
        records = query.order_by(VoiceDiary.record_date.desc(), VoiceDiary.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "list": [VoiceDiaryService.to_dict(r) for r in records],
            "total": total, "page": page, "page_size": page_size,
        }

    @staticmethod
    def to_dict(r: VoiceDiary) -> Dict:
        return {
            "id": r.id, "title": r.title,
            "content": r.content or "",
            "content_edit": r.content_edit or "",
            "final_content": r.content_edit if r.content_edit else (r.content or ""),
            "audio_url": r.audio_url, "audio_duration": r.audio_duration,
            "audio_size": r.audio_size, "sample_rate": r.sample_rate,
            "language": r.language, "translation": r.translation or "",
            "translate_lang": r.translate_lang,
            "category": r.category,
            "category_name": VoiceDiaryService.CATEGORY_LABELS.get(r.category, r.category),
            "mood": r.mood,
            "sentiment_score": r.sentiment_score,
            "sentiment_label": r.sentiment_label,
            "remind_time": r.remind_time,
            "record_date": str(r.record_date),
            "created_at": str(r.created_at),
        }

    @staticmethod
    def get_stats(db: Session, user_id: int, period: str = "30d") -> Dict:
        """
        日记统计: 总数/本周数/连续天数/总时长/情绪趋势/分类分布/情感分布
        """
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 30)
        start_date = date.today() - timedelta(days=days - 1)

        all_records = db.query(VoiceDiary).filter(
            VoiceDiary.user_id == user_id,
            VoiceDiary.record_date >= start_date,
        ).order_by(VoiceDiary.record_date).all()

        # 总览(不限周期)
        total_count = db.query(VoiceDiary).filter(VoiceDiary.user_id == user_id).count()
        total_duration = db.query(VoiceDiary).filter(VoiceDiary.user_id == user_id).with_entities(
            VoiceDiary.audio_duration
        ).all()
        total_seconds = sum(d[0] or 0 for d in total_duration)

        # 情绪趋势(按日期平均情感分)
        labels, scores = [], []
        date_score = {}
        for r in all_records:
            ds = str(r.record_date)
            date_score.setdefault(ds, []).append(r.sentiment_score)
        for i in range(days - 1, -1, -1):
            ds = str(date.today() - timedelta(days=i))
            labels.append(ds[5:])  # MM-DD
            scores.append(round(sum(date_score[ds]) / len(date_score[ds]), 1) if ds in date_score else 0)

        # 分类分布
        cat_dist = {}
        for r in all_records:
            cat_dist[r.category] = cat_dist.get(r.category, 0) + 1
        category_distribution = [{
            "category": c, "name": VoiceDiaryService.CATEGORY_LABELS.get(c, c), "count": n,
        } for c, n in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True)]

        # 情感分布
        sent_dist = {}
        for r in all_records:
            sent_dist[r.sentiment_label] = sent_dist.get(r.sentiment_label, 0) + 1

        # 连续记录天数
        streak = 0
        check = date.today()
        record_dates = set(str(r.record_date) for r in db.query(VoiceDiary).filter(
            VoiceDiary.user_id == user_id
        ).with_entities(VoiceDiary.record_date).all())
        while str(check) in record_dates:
            streak += 1
            check -= timedelta(days=1)

        return {
            "period": period,
            "total_count": total_count,
            "period_count": len(all_records),
            "continuous_days": streak,
            "total_duration_seconds": total_seconds,
            "total_duration_text": VoiceDiaryService.format_duration(total_seconds),
            "sentiment_trend": {"labels": labels, "scores": scores},
            "category_distribution": category_distribution,
            "sentiment_distribution": sent_dist,
            "positive_ratio": round(
                sent_dist.get("positive", 0) / max(len(all_records), 1) * 100, 1
            ),
        }

    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分钟"
        return f"{minutes // 60}小时{minutes % 60}分钟"

    @staticmethod
    def get_categories(db: Session, user_id: int) -> List[Dict]:
        """分类列表 = 默认分类 + 用户自定义分类"""
        customs = db.query(VoiceDiaryCategory).filter(
            VoiceDiaryCategory.user_id == user_id
        ).order_by(VoiceDiaryCategory.sort, VoiceDiaryCategory.id).all()
        result = list(VoiceDiaryService.DEFAULT_CATEGORIES)
        for c in customs:
            result.append({"id": c.id, "name": c.name, "key": f"custom_{c.id}", "icon": c.icon, "color": c.color})
        return result

    @staticmethod
    def backup_export(db: Session, user_id: int) -> Dict:
        """备份导出(全量JSON)"""
        records = db.query(VoiceDiary).filter(
            VoiceDiary.user_id == user_id
        ).order_by(VoiceDiary.record_date.desc()).all()
        categories = VoiceDiaryService.get_categories(db, user_id)
        backup_data = {
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "count": len(records),
            "categories": categories,
            "diaries": [VoiceDiaryService.to_dict(r) for r in records],
        }
        return {
            "filename": f"voice-diary-backup-{date.today().strftime('%Y%m%d')}.json",
            "data": backup_data,
        }

    @staticmethod
    def save_upload(file_bytes: bytes, original_name: str = "") -> Dict:
        """保存上传的音频文件, 返回 {file_id, url, size}"""
        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        ext = ".mp3"
        if original_name and "." in original_name:
            ext = os.path.splitext(original_name)[1][:10]
        file_id = uuid.uuid4().hex
        filename = f"voice_{file_id}{ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_bytes)
        return {
            "file_id": file_id,
            "file_path": filepath,
            "url": f"/uploads/{filename}",
            "size": len(file_bytes),
        }
