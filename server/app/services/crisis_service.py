# -*- coding: utf-8 -*-
"""
危机干预服务 - 负面情绪检测 + 干预话术 + 紧急联系方式
"""
import json
from typing import Dict


class CrisisService:
    """危机干预服务"""

    # 高危关键词(触发危机干预)
    CRISIS_KEYWORDS = [
        "不想活", "想死", "自杀", "结束生命", "活不下去", "了结", "跳楼",
        "割腕", "安眠药", "没有意义", "世界没有我更好", "想消失",
        "撑不下去", "绝望", "崩溃", "放弃一切", "解脱",
    ]

    # 负面情绪关键词(触发关注但非危机)
    NEGATIVE_KEYWORDS = [
        "难过", "伤心", "哭", "不开心", "郁闷", "焦虑", "烦躁",
        "孤独", "无助", "疲惫", "心累", "崩溃", "压力大", "窒息",
    ]

    # 紧急联系方式
    HOTLINES = [
        {"name": "全国心理援助热线", "phone": "400-161-9995", "hours": "24小时"},
        {"name": "北京心理危机研究与干预中心", "phone": "010-82951332", "hours": "24小时"},
        {"name": "生命热线", "phone": "400-821-1215", "hours": "每日8:00-22:00"},
        {"name": "希望24热线", "phone": "400-161-9995", "hours": "24小时"},
    ]

    # 危机干预话术
    CRISIS_INTERVENTION = (
        "我听到你说了一些让我很担心的话。你现在正在经历的痛苦，我能感受到它很沉重。\n\n"
        "请你知道，你不是一个人。此刻有很多人愿意帮助你度过难关。\n\n"
        "如果你正在有伤害自己的想法，请立刻拨打下面的热线电话，他们24小时在线，会陪伴你度过这个时刻。\n\n"
        "你的生命很珍贵，这个痛苦的时刻会过去的。请给自己一个机会，也让别人有机会帮助你。"
    )

    # 关注话术(非危机但负面)
    COMFORT_TEXT = (
        "我看到你现在不太好受。我想让你知道，所有的情绪都是被允许的，"
        "难过、焦虑、疲惫都是真实的你的一部分。不需要强撑着，"
        "你可以跟我说说发生了什么吗？我会一直在这里听着。"
    )

    @staticmethod
    def check_crisis(text: str) -> Dict:
        """
        检测危机程度
        返回: {level: "normal"|"high"|"critical", message, resources}
        """
        if not text:
            return {"level": "normal", "message": "", "resources": []}

        # 检测危机关键词
        for kw in CrisisService.CRISIS_KEYWORDS:
            if kw in text:
                return {
                    "level": "critical",
                    "message": CrisisService.CRISIS_INTERVENTION,
                    "resources": CrisisService.HOTLINES,
                    "trigger": kw,
                }

        # 检测负面情绪
        for kw in CrisisService.NEGATIVE_KEYWORDS:
            if kw in text:
                return {
                    "level": "high",
                    "message": CrisisService.COMFORT_TEXT,
                    "resources": [],
                    "trigger": kw,
                }

        return {"level": "normal", "message": "", "resources": []}

    @staticmethod
    def get_resources() -> list:
        """获取紧急联系方式列表"""
        return CrisisService.HOTLINES
