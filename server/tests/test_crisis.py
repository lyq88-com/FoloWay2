# -*- coding: utf-8 -*-
"""
危机干预服务测试 - 关键词检测/干预话术/热线资源
"""
import pytest
from app.services.crisis_service import CrisisService


class TestCrisisDetection:
    """危机检测"""

    def test_normal_text(self):
        """正常文本不触发危机"""
        result = CrisisService.check_crisis("今天天气真好，出去散步了")
        assert result["level"] == "normal"
        assert result["message"] == ""
        assert result["resources"] == []

    def test_empty_text(self):
        """空文本不触发危机"""
        result = CrisisService.check_crisis("")
        assert result["level"] == "normal"

    def test_none_text(self):
        """None 不触发危机"""
        result = CrisisService.check_crisis(None)
        assert result["level"] == "normal"

    @pytest.mark.parametrize("keyword", [
        "不想活", "想死", "自杀", "结束生命", "活不下去",
        "了结", "跳楼", "割腕", "安眠药", "想消失",
        "撑不下去", "绝望", "放弃一切", "解脱",
    ])
    def test_crisis_keywords(self, keyword):
        """高危关键词触发 critical 级别"""
        result = CrisisService.check_crisis(f"我真的很{keyword}")
        assert result["level"] == "critical"
        assert len(result["message"]) > 0
        assert len(result["resources"]) > 0
        assert result["trigger"] == keyword

    @pytest.mark.parametrize("keyword", [
        "难过", "伤心", "哭", "不开心", "郁闷", "焦虑",
        "烦躁", "孤独", "无助", "疲惫", "心累", "压力大",
    ])
    def test_negative_keywords(self, keyword):
        """负面情绪关键词触发 high 级别"""
        result = CrisisService.check_crisis(f"今天很{keyword}")
        assert result["level"] == "high"
        assert len(result["message"]) > 0
        # high 级别不提供热线资源
        assert result["resources"] == []

    def test_crisis_has_hotlines(self):
        """危机干预包含热线电话"""
        result = CrisisService.check_crisis("我不想活了")
        assert result["level"] == "critical"
        resources = result["resources"]
        assert len(resources) >= 3
        for r in resources:
            assert "name" in r
            assert "phone" in r
            assert "hours" in r

    def test_crisis_intervention_text(self):
        """危机干预话术包含关怀内容"""
        result = CrisisService.check_crisis("想自杀")
        assert result["level"] == "critical"
        msg = result["message"]
        assert "不是一个人" in msg or "生命" in msg or "帮助" in msg

    def test_negative_comfort_text(self):
        """负面情绪话术包含安慰内容"""
        result = CrisisService.check_crisis("我好难过")
        assert result["level"] == "high"
        msg = result["message"]
        assert len(msg) > 10  # 有实质内容

    def test_get_resources(self):
        """获取热线资源列表"""
        resources = CrisisService.get_resources()
        assert len(resources) >= 3
        assert any(r["phone"] == "400-161-9995" for r in resources)

    def test_crisis_in_long_text(self):
        """长文本中的危机关键词也能检测到"""
        long_text = "今天工作很忙，开了很多会，回来之后觉得压力很大，真的撑不下去了，感觉不想活了"
        result = CrisisService.check_crisis(long_text)
        assert result["level"] == "critical"
        assert result["trigger"] == "不想活"
