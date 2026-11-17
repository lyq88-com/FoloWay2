# -*- coding: utf-8 -*-
"""
成长档案服务 - 月/季/年报告生成 + 数据汇总
"""
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta


class ArchiveService:
    """成长档案服务"""

    @staticmethod
    def get_period_range(period: str, ref_date: date = None) -> tuple:
        """获取周期范围"""
        if ref_date is None:
            ref_date = date.today()

        if period == "monthly":
            start = ref_date.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month + 1) - timedelta(days=1)
        elif period == "quarterly":
            quarter = (ref_date.month - 1) // 3
            start_month = quarter * 3 + 1
            start = ref_date.replace(month=start_month, day=1)
            end_month = start_month + 2
            # 季度末月是 12 月时不能再用 month=13 计算，否则 replace() 直接抛 ValueError
            if end_month == 12:
                end = start.replace(month=12, day=31)
            else:
                end = start.replace(month=end_month + 1, day=1) - timedelta(days=1)
        elif period == "yearly":
            start = ref_date.replace(month=1, day=1)
            end = ref_date.replace(month=12, day=31)
        else:
            start = ref_date.replace(day=1)
            end = ref_date

        return start, end

    @staticmethod
    def build_archive_summary(
        emotion_records: List[Dict],
        checkin_records: List[Dict],
        mindfulness_records: List[Dict],
        period: str,
    ) -> Dict:
        """
        汇总数据生成档案摘要
        """
        # 情绪统计
        emotion_count = len(emotion_records)
        emotion_distribution = {}
        avg_intensity = 0
        if emotion_records:
            for r in emotion_records:
                emo = r.get("emotion", "neutral")
                emotion_distribution[emo] = emotion_distribution.get(emo, 0) + 1
            avg_intensity = sum(r.get("intensity", 5) for r in emotion_records) / len(emotion_records)

        # 打卡统计
        checkin_count = len(checkin_records)
        completed_count = sum(1 for c in checkin_records if c.get("completed"))
        completion_rate = (completed_count / checkin_count * 100) if checkin_count > 0 else 0

        # 正念统计
        mindfulness_count = len(mindfulness_records)
        total_meditation_min = sum(m.get("duration_min", 0) for m in mindfulness_records)

        # 成长亮点
        highlights = []
        if completion_rate >= 80:
            highlights.append(f"习惯完成率达到了{completion_rate:.0f}%，坚持力非常出色！")
        if mindfulness_count >= 10:
            highlights.append(f"完成了{mindfulness_count}次正念练习，累计{total_meditation_min}分钟，内心平静力提升！")
        positive_count = emotion_distribution.get("happy", 0) + emotion_distribution.get("excited", 0)
        if positive_count > 0:
            highlights.append(f"记录了{positive_count}次开心/兴奋时刻，生活中的美好值得被记住！")

        # 改进建议
        suggestions = []
        if completion_rate < 50:
            suggestions.append("可以尝试调整习惯难度，先从简单目标开始培养信心。")
        negative_ratio = (emotion_distribution.get("sad", 0) + emotion_distribution.get("angry", 0)) / max(emotion_count, 1)
        if negative_ratio > 0.4:
            suggestions.append("负面情绪占比较高，建议多进行正念练习，也可以考虑与AI伙伴多聊聊。")
        if mindfulness_count < 3:
            suggestions.append("尝试每天5分钟正念呼吸练习，帮助调节情绪。")

        return {
            "period": period,
            "emotion_count": emotion_count,
            "emotion_distribution": emotion_distribution,
            "avg_intensity": round(avg_intensity, 1),
            "checkin_count": checkin_count,
            "completed_count": completed_count,
            "completion_rate": round(completion_rate, 1),
            "mindfulness_count": mindfulness_count,
            "total_meditation_min": total_meditation_min,
            "highlights": highlights,
            "suggestions": suggestions,
            "summary": ArchiveService._generate_summary(
                emotion_count, completion_rate, mindfulness_count, highlights
            ),
        }

    @staticmethod
    def _generate_summary(emotion_count: int, completion_rate: float,
                          mindfulness_count: int, highlights: List[str]) -> str:
        """生成文字摘要"""
        parts = []
        parts.append(f"这段时间你记录了{emotion_count}次情绪，")
        parts.append(f"习惯完成率{completion_rate:.0f}%，")
        parts.append(f"完成了{mindfulness_count}次正念练习。")
        if highlights:
            parts.append(" ".join(highlights))
        parts.append("每一次记录都是对自己的关注，继续加油！")
        return "".join(parts)
