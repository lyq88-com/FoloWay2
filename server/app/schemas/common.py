# -*- coding: utf-8 -*-
"""
通用Schema - 统一响应/分页
"""
from typing import Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ResponseBase(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "ok"
    data: Optional[Any] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "ok") -> "ResponseBase":
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = 400) -> "ResponseBase":
        return cls(code=code, message=message, data=None)


class PageResult(BaseModel):
    """分页结果"""
    list: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
