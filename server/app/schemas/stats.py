# -*- coding: utf-8 -*-
"""
统计分析Schema
"""
from pydantic import BaseModel, Field


class StatsQuery(BaseModel):
    """统计查询"""
    period: str = Field(default="7d", description="7d/30d/90d")


class EmotionReportRequest(BaseModel):
    """情绪报告请求"""
    period: str = "7d"
