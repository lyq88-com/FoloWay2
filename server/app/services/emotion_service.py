# -*- coding: utf-8 -*-
"""
情绪分析服务 - 文本情绪识别 + 趋势分析 + 关联分析
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class EmotionService:
    """情绪分析服务"""

    # 情绪关键词库
    EMOTION_KEYWORDS = {
        "happy": ["开心", "高兴", "快乐", "幸福", "棒", "好开心", "哈哈", "笑", "满足", "愉快"],
        "excited": ["兴奋", "激动", "期待", "太棒了", "万岁", "终于", "成功", "达成", "突破"],
        "calm": ["平静", "安心", "放松", "舒适", "宁静", "还好", "一般", "普通", "平常"],
        "sad": ["难过", "伤心", "哭", "悲伤", "不开心", "郁闷", "失落", "孤独", "想哭", "委屈"],
        "angry": ["生气", "愤怒", "气死", "烦", "讨厌", "烦死", "可恶", "不爽", "恼火", "抓狂"],
        "tired": ["累", "疲惫", "困", "没劲", "疲惫不堪", "力不从心", "撑不住", "精疲力尽", "好困"],
    }

    # 情绪中文名
    EMOTION_LABELS = {
        "happy": "开心",
        "excited": "兴奋",
        "calm": "平静",
        "sad": "难过",
        "angry": "生气",
        "tired": "疲惫",
    }

    # 情绪效价(正面/负面)
    EMOTION_VALENCE = {
        "happy": "positive",
        "excited": "positive",
        "calm": "neutral",
        "sad": "negative",
        "angry": "negative",
        "tired": "negative",
    }

    @staticmethod
    def analyze_emotion(text: str) -> Dict:
        """
        文本情绪分析 - 关键词匹配法
        返回: {emotion, confidence, valence}
        """
        if not text:
            return {"emotion": "neutral", "confidence": 0.0, "valence": "neutral"}

        text_lower = text.lower()
        scores = {}

        for emotion, keywords in EmotionService.EMOTION_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    score += len(kw)  # 长关键词权重更高
            if score > 0:
                scores[emotion] = score

        if not scores:
            return {"emotion": "neutral", "confidence": 0.0, "valence": "neutral"}

        # 取分数最高的情绪
        best_emotion = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = min(scores[best_emotion] / max(total, 1), 1.0)

        return {
            "emotion": best_emotion,
            "confidence": round(confidence, 2),
            "valence": EmotionService.EMOTION_VALENCE.get(best_emotion, "neutral"),
        }

    @staticmethod
    def get_emotion_trend(records: List[Dict], days: int = 7) -> Dict:
        """
        情绪趋势分析
        records: [{record_date, emotion, intensity, ...}]
        返回: {labels, intensities, emotions, distribution}
        """
        today = datetime.now().date()
        labels = []
        avg_intensities = []
        daily_emotions = []

        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            labels.append(date_str)

            day_records = [r for r in records if r.get("record_date") == date_str]
            if day_records:
                avg_intensity = sum(r.get("intensity", 5) for r in day_records) / len(day_records)
                avg_intensities.append(round(avg_intensity, 1))
                # 取出现最多的情绪
                emotions = [r.get("emotion") for r in day_records]
                most_common = max(set(emotions), key=emotions.count) if emotions else "neutral"
                daily_emotions.append(most_common)
            else:
                avg_intensities.append(0)
                daily_emotions.append("")

        # 情绪分布
        distribution = {}
        for r in records:
            emo = r.get("emotion", "neutral")
            distribution[emo] = distribution.get(emo, 0) + 1

        return {
            "labels": labels,
            "intensities": avg_intensities,
            "emotions": daily_emotions,
            "distribution": distribution,
        }

    @staticmethod
    def get_trigger_analysis(records: List[Dict]) -> List[Dict]:
        """
        情绪触发因素分析
        统计哪些标签容易引发情绪波动
        """
        tag_stats = {}
        for r in records:
            tags = r.get("tags", [])
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except (json.JSONDecodeError, TypeError):
                    tags = []
            intensity = r.get("intensity", 5)
            emotion = r.get("emotion", "")
            valence = EmotionService.EMOTION_VALENCE.get(emotion, "neutral")

            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"count": 0, "total_intensity": 0, "negative_count": 0}
                tag_stats[tag]["count"] += 1
                tag_stats[tag]["total_intensity"] += intensity
                if valence == "negative":
                    tag_stats[tag]["negative_count"] += 1

        result = []
        for tag, stats in tag_stats.items():
            result.append({
                "tag": tag,
                "count": stats["count"],
                "avg_intensity": round(stats["total_intensity"] / max(stats["count"], 1), 1),
                "negative_ratio": round(stats["negative_count"] / max(stats["count"], 1) * 100, 1),
            })

        result.sort(key=lambda x: x["count"], reverse=True)
        return result

    @staticmethod
    def get_habit_correlation(emotion_records: List[Dict],
                               checkin_records: List[Dict]) -> Dict:
        """
        习惯打卡与情绪关联分析
        """
        # 按日期分组
        emotion_by_date = {}
        for r in emotion_records:
            date = r.get("record_date", "")
            if date not in emotion_by_date:
                emotion_by_date[date] = []
            emotion_by_date[date].append(r)

        checkin_by_date = {}
        for r in checkin_records:
            date = r.get("checkin_date", "")
            if date not in checkin_by_date:
                checkin_by_date[date] = []
            checkin_by_date[date].append(r)

        # 分析打卡成功/失败日的情绪差异
        success_emotions = []
        fail_emotions = []

        for date, emotions in emotion_by_date.items():
            checkins = checkin_by_date.get(date, [])
            if not checkins:
                continue

            completed = sum(1 for c in checkins if c.get("completed"))
            total = len(checkins)
            rate = completed / total if total > 0 else 0

            for emo in emotions:
                if rate >= 0.5:
                    success_emotions.append(emo.get("emotion"))
                else:
                    fail_emotions.append(emo.get("emotion"))

        return {
            "success_top": EmotionService._top_emotions(success_emotions),
            "fail_top": EmotionService._top_emotions(fail_emotions),
            "success_avg_intensity": EmotionService._avg_intensity(success_emotions, emotion_by_date, success=True),
            "fail_avg_intensity": EmotionService._avg_intensity(fail_emotions, emotion_by_date, success=False),
        }

    # === ↓↓↓ 新增：真实逐习惯关联分析（供 /stats/emotion/habit-correlation 使用） ↓↓↓ ===

    @staticmethod
    def _wellbeing(emotion: str, intensity) -> float:
        """
        把「情绪 + 强度」折算成 0~10 的心理状态分：
        正面情绪强度越高越好(5.5~10)，负面情绪强度越高越差(0.5~5)，中性恒为 5。
        """
        try:
            i = float(intensity)
        except (TypeError, ValueError):
            i = 5.0
        i = max(1.0, min(10.0, i))
        valence = EmotionService.EMOTION_VALENCE.get(emotion, "neutral")
        if valence == "positive":
            return 5.0 + i / 2.0
        if valence == "negative":
            return 5.5 - i / 2.0
        return 5.0

    @staticmethod
    def _dominant_emotion(emotions: List[str], fallback: str = "") -> str:
        if not emotions:
            return fallback
        freq = {}
        for e in emotions:
            if e:
                freq[e] = freq.get(e, 0) + 1
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[0][0]

    @staticmethod
    def get_habit_emotion_correlations(emotion_records: List[Dict],
                                       checkin_records: List[Dict]) -> List[Dict]:
        """
        逐习惯计算「打卡 vs 情绪」关联。

        emotion_records: [{"record_date": "YYYY-MM-DD", "emotion": str, "intensity": int}]
        checkin_records: [{"habit_id": int, "habit_name": str, "habit_icon": str,
                           "checkin_date": "YYYY-MM-DD", "completed": bool}]

        返回（按关联度降序），字段与前端 habit-emotion-heatmap 组件一致：
        [{habit_id, habit_name, habit_icon, correlation(0~1), improvement(百分点),
          checkin_count, avg_intensity_after, emotion_before, emotion_after, sample_days}]
        """
        # 1) 按日期聚合当天心理状态分与原始强度
        mood_by_date = {}
        intensity_by_date = {}
        emo_by_date = {}
        for r in emotion_records:
            d = r.get("record_date", "")
            if not d:
                continue
            wb = EmotionService._wellbeing(r.get("emotion", ""), r.get("intensity", 5))
            mood_by_date.setdefault(d, []).append(wb)
            intensity_by_date.setdefault(d, []).append(float(r.get("intensity", 5) or 5))
            emo_by_date.setdefault(d, []).append(r.get("emotion", ""))

        mood_of_date = {d: sum(v) / len(v) for d, v in mood_by_date.items() if v}
        intensity_of_date = {d: sum(v) / len(v) for d, v in intensity_by_date.items() if v}

        # 2) 按习惯聚合「完成日 / 未完成日」
        habits = {}
        for c in checkin_records:
            hid = c.get("habit_id")
            if hid is None:
                continue
            h = habits.setdefault(hid, {
                "habit_id": hid,
                "habit_name": c.get("habit_name") or "习惯",
                "habit_icon": c.get("habit_icon") or "checkmark",
                "done": [],
                "miss": [],
                "done_count": 0,
            })
            d = c.get("checkin_date", "")
            ok = bool(c.get("completed"))
            if ok:
                h["done_count"] += 1
            if d:
                (h["done"] if ok else h["miss"]).append(d)

        # 3) 逐习惯算点二列相关 + 改善幅度
        result = []
        for hid, h in habits.items():
            done_dates = [d for d in set(h["done"]) if d in mood_of_date]
            miss_dates = [d for d in set(h["miss"]) if d in mood_of_date]
            if not done_dates and not miss_dates:
                continue

            c_moods = [mood_of_date[d] for d in done_dates]
            m_moods = [mood_of_date[d] for d in miss_dates]
            all_moods = c_moods + m_moods
            n = len(all_moods)
            mean_all = sum(all_moods) / n

            # 点二列相关 r = (M1 - M0) / s * sqrt(p * q)
            r = 0.0
            if c_moods and m_moods and n >= 2:
                m1 = sum(c_moods) / len(c_moods)
                m0 = sum(m_moods) / len(m_moods)
                ss = sum((y - mean_all) ** 2 for y in all_moods)
                if ss > 0:
                    s = (ss / n) ** 0.5
                    p = len(c_moods) / n
                    q = 1 - p
                    r = (m1 - m0) / s * ((p * q) ** 0.5)
                r = max(-1.0, min(1.0, r))
            # r 线性映射到 0~1：0.5 = 无关联，>0.7 = 明显正向
            correlation = max(0.0, min(1.0, 0.5 + r))

            mean_done = sum(c_moods) / len(c_moods) if c_moods else mean_all
            mean_miss = sum(m_moods) / len(m_moods) if m_moods else mean_all
            improvement = round((mean_done - mean_miss) * 10, 1)

            after_ints = [intensity_of_date[d] for d in done_dates if d in intensity_of_date]
            before_ints = [intensity_of_date[d] for d in miss_dates if d in intensity_of_date]
            avg_intensity_after = round(sum(after_ints) / len(after_ints), 1) if after_ints else (
                round(sum(before_ints) / len(before_ints), 1) if before_ints else 0.0)

            all_emos = []
            for d in done_dates + miss_dates:
                all_emos.extend(emo_by_date.get(d, []))
            emotion_after = EmotionService._dominant_emotion(
                [e for d in done_dates for e in emo_by_date.get(d, [])],
                EmotionService._dominant_emotion(all_emos))
            emotion_before = EmotionService._dominant_emotion(
                [e for d in miss_dates for e in emo_by_date.get(d, [])],
                EmotionService._dominant_emotion(all_emos))

            result.append({
                "habit_id": hid,
                "habit_name": h["habit_name"],
                "habit_icon": h["habit_icon"],
                "correlation": round(correlation, 3),
                "improvement": improvement,
                "checkin_count": h["done_count"],
                "avg_intensity_after": avg_intensity_after,
                "emotion_before": emotion_before,
                "emotion_after": emotion_after,
                "sample_days": n,
                "r": round(r, 3),
            })

        result.sort(key=lambda x: x["correlation"], reverse=True)
        return result

    # === ↑↑↑ 新增结束 ↑↑↑ ===

    @staticmethod
    def _top_emotions(emotions: List[str]) -> List[Dict]:
        """统计情绪频次"""
        freq = {}
        for e in emotions:
            freq[e] = freq.get(e, 0) + 1
        return [{"emotion": k, "count": v} for k, v in
                sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

    @staticmethod
    def _avg_intensity(emotions: List[str], by_date: Dict, success: bool) -> float:
        """计算平均强度(简化版)"""
        if not emotions:
            return 0.0
        return round(5.0, 1)  # 简化:默认5.0

    # === ↓↓↓ 模块1新增：宣泄倾听 + 情绪陪伴判定 ↓↓↓ ===

    # 宣泄/吐槽关键词组（识别用户"想骂人/发泄"）
    VENT_KEYWORDS = [
        "妈的", "操", "气死我", "烦死了", "想骂人", "好想骂", "忍不了",
        "受不了", "崩溃", "疯了", "砸了", "摔", "不想活", "撑不下去",
        "该死", "狗屁", "混蛋", "废物", "垃圾", "人渣",
    ]

    # 用户明确说"不要安慰"的关键词
    REJECT_COMFORT_KEYWORDS = [
        "别安慰", "不用说教", "我只是吐槽", "别劝我", "不用安慰",
        "不用管我", "我没事", "别担心", "不用陪", "让我静静",
    ]

    # 强烈负面情绪（需要跳转正念/日记的 crisis 级别）
    CRISIS_EMOTIONS = {"sad", "angry", "tired"}
    CRISIS_CONFIDENCE_THRESHOLD = 0.55  # 匹配度 > 55% 算 crisis

    @staticmethod
    def is_venting(text: str) -> bool:
        """用户是不是在吐槽/想骂人"""
        if not text:
            return False
        return any(kw in text.lower() for kw in EmotionService.VENT_KEYWORDS)

    @staticmethod
    def is_rejecting_comfort(text: str) -> bool:
        """用户是不是明确说不要安慰"""
        if not text:
            return False
        return any(kw in text.lower() for kw in EmotionService.REJECT_COMFORT_KEYWORDS)

    @staticmethod
    def should_trigger_comfort(emotion_result: Dict, text: str = "") -> bool:
        """
        是否触发情绪陪伴分支：
        - valence == "negative" 且 confidence > 0.3 → 轻度负面
        - 或者 is_venting(text) → 宣泄倾听
        """
        if emotion_result.get("valence") != "negative":
            return False
        confidence = emotion_result.get("confidence", 0.0)
        if confidence > 0.3:
            return True
        if text and EmotionService.is_venting(text):
            return True
        return False

    @staticmethod
    def is_crisis_level(emotion_result: Dict) -> bool:
        """是否达到危机级别（建议跳转正念/日记）"""
        emotion = emotion_result.get("emotion", "")
        confidence = emotion_result.get("confidence", 0.0)
        return emotion in EmotionService.CRISIS_EMOTIONS and confidence >= EmotionService.CRISIS_CONFIDENCE_THRESHOLD

    # === ↑↑↑ 模块1新增结束 ↑↑↑ ===
