# -*- coding: utf-8 -*-
"""
成长档案Schema
"""
from pydantic import BaseModel, Field


class ArchiveQuery(BaseModel):
    """档案查询"""
    period: str = "monthly"
    date: str = Field(default="", description="指定月份/季度/年份 YYYY-MM")


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = "json"
    start_date: str = ""
    end_date: str = ""
