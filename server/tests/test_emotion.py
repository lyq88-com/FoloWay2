# -*- coding: utf-8 -*-
"""
情绪分析服务测试 - 文本情绪识别/趋势分析/触发因素分析
"""
import pytest
from app.services.emotion_service import EmotionService


class TestEmotionAnalysis:
    """文本情绪分析"""

    def test_happy_text(self):
        """开心文本识别"""
        result = EmotionService.analyze_emotion("今天好开心啊，终于完成了目标")
        assert result["emotion"] == "happy"
        assert result["valence"] == "positive"
        assert result["confidence"] > 0

    def test_sad_text(self):
        """难过文本识别"""
        result = EmotionService.analyze_emotion("好难过，感觉什么都不顺利")
        assert result["emotion"] == "sad"
        assert result["valence"] == "negative"

    def test_angry_text(self):
        """生气文本识别"""
        result = EmotionService.analyze_emotion("气死我了，真的太烦了")
        assert result["emotion"] == "angry"
        assert result["valence"] == "negative"

    def test_tired_text(self):
        """疲惫文本识别"""
        result = EmotionService.analyze_emotion("今天好累，疲惫不堪")
        assert result["emotion"] == "tired"
        assert result["valence"] == "negative"

    def test_excited_text(self):
        """兴奋文本识别"""
        result = EmotionService.analyze_emotion("太棒了！终于成功了！")
        assert result["emotion"] == "excited"
        assert result["valence"] == "positive"

    def test_calm_text(self):
        """平静文本识别"""
        result = EmotionService.analyze_emotion("今天很平静，感觉还不错")
        assert result["emotion"] in ("calm", "happy")
        assert result["valence"] in ("neutral", "positive")

    def test_empty_text(self):
        """空文本返回 neutral"""
        result = EmotionService.analyze_emotion("")
        assert result["emotion"] == "neutral"
        assert result["confidence"] == 0.0

    def test_none_text(self):
        """None 返回 neutral"""
        result = EmotionService.analyze_emotion(None)
        assert result["emotion"] == "neutral"

    def test_no_keyword_text(self):
        """无关键词文本返回 neutral"""
        result = EmotionService.analyze_emotion("今天去超市买了些东西")
        assert result["emotion"] == "neutral"

    def test_mixed_emotions(self):
        """混合情绪文本取权重最高的"""
        result = EmotionService.analyze_emotion("虽然很开心但是也很累")
        # "开心"权重2, "累"权重1, 应该识别为 happy
        assert result["emotion"] == "happy"
        assert result["confidence"] > 0


class TestEmotionTrend:
    """情绪趋势分析"""

    def test_empty_records(self):
        """空记录趋势"""
        result = EmotionService.get_emotion_trend([], days=7)
        assert len(result["labels"]) == 7
        assert all(i == 0 for i in result["intensities"])
        assert result["distribution"] == {}

    def test_with_records(self):
        """有记录的趋势分析"""
        from datetime import datetime, timedelta
        today = datetime.now().date().strftime("%Y-%m-%d")
        records = [
            {"record_date": today, "emotion": "happy", "intensity": 8},
            {"record_date": today, "emotion": "sad", "intensity": 3},
        ]
        result = EmotionService.get_emotion_trend(records, days=7)
        assert len(result["labels"]) == 7
        # 今天的平均强度 = (8+3)/2 = 5.5
        today_intensity = result["intensities"][-1]
        assert today_intensity == 5.5
        # 分布统计
        assert result["distribution"]["happy"] == 1
        assert result["distribution"]["sad"] == 1

    def test_30d_trend(self):
        """30天趋势"""
        result = EmotionService.get_emotion_trend([], days=30)
        assert len(result["labels"]) == 30

    def test_90d_trend(self):
        """90天趋势"""
        result = EmotionService.get_emotion_trend([], days=90)
        assert len(result["labels"]) == 90


class TestTriggerAnalysis:
    """触发因素分析"""

    def test_empty_records(self):
        """空记录"""
        result = EmotionService.get_trigger_analysis([])
        assert result == []

    def test_with_tags(self):
        """有标签的记录"""
        records = [
            {"emotion": "sad", "intensity": 7, "tags": ["工作", "压力"]},
            {"emotion": "angry", "intensity": 8, "tags": ["工作"]},
            {"emotion": "happy", "intensity": 6, "tags": ["运动"]},
        ]
        result = EmotionService.get_trigger_analysis(records)
        assert len(result) == 3
        # "工作"出现2次, 应排第一
        assert result[0]["tag"] == "工作"
        assert result[0]["count"] == 2
        # "工作"的负面比例: 2条都是负面(sad+angry) = 100%
        assert result[0]["negative_ratio"] == 100.0

    def test_tags_as_string(self):
        """标签为JSON字符串"""
        import json
        records = [
            {
                "emotion": "sad", "intensity": 5,
                "tags": json.dumps(["工作"], ensure_ascii=False),
            },
        ]
        result = EmotionService.get_trigger_analysis(records)
        assert len(result) == 1
        assert result[0]["tag"] == "工作"

    def test_avg_intensity(self):
        """平均强度计算"""
        records = [
            {"emotion": "sad", "intensity": 6, "tags": ["工作"]},
            {"emotion": "sad", "intensity": 8, "tags": ["工作"]},
        ]
        result = EmotionService.get_trigger_analysis(records)
        assert result[0]["avg_intensity"] == 7.0


class TestEmotionLabels:
    """情绪标签映射"""

    def test_all_labels_exist(self):
        """所有情绪类型都有中文标签"""
        for emo in ["happy", "excited", "calm", "sad", "angry", "tired"]:
            assert emo in EmotionService.EMOTION_LABELS
            assert len(EmotionService.EMOTION_LABELS[emo]) > 0

    def test_valence_mapping(self):
        """情绪效价映射正确"""
        assert EmotionService.EMOTION_VALENCE["happy"] == "positive"
        assert EmotionService.EMOTION_VALENCE["excited"] == "positive"
        assert EmotionService.EMOTION_VALENCE["calm"] == "neutral"
        assert EmotionService.EMOTION_VALENCE["sad"] == "negative"
        assert EmotionService.EMOTION_VALENCE["angry"] == "negative"
        assert EmotionService.EMOTION_VALENCE["tired"] == "negative"
