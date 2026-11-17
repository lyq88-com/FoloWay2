# -*- coding: utf-8 -*-
"""
陪伴模式 Schema
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CompanionStartRequest(BaseModel):
    """开始陪伴请求"""
    role_id: int = Field(1, description="陪伴AI角色ID(旧字段, 兼容用)")

    # ↓↓↓ 新增：20 个具名角色 ↓↓↓
    # role_key = frontend/common/ai-characters.js 里 CHARACTERS[].id（如 linxi）。
    # 不做白名单校验：自定义角色（character-workshop 创建）也要能进陪伴。
    role_key: str = Field("", max_length=64, description="陪伴角色标识(20个具名角色字符串id)")
    role_name: str = Field("", max_length=50, description="陪伴角色显示名快照")

    @field_validator("role_key", "role_name", mode="before")
    @classmethod
    def coerce_str(cls, v):
        if v is None:
            return ""
        if not isinstance(v, str):
            v = str(v)
        return v.strip()[:64]
    # ↑↑↑ 新增结束 ↑↑↑

    # ↓↓↓ 新增（BUG-001 兼容层） ↓↓↓
    @field_validator("role_id", mode="before")
    @classmethod
    def coerce_role_id(cls, v):
        """兼容历史客户端传字符串角色标识的情况

        旧版 GET /chat/personas 返回字符串 id（"companion"/"mentor"/"friend"），
        前端原样回传时会被 int 字段拒绝并抛出 422，导致陪伴记录无法入库。
        这里把非法值统一归一为 0，由接口层回退到默认角色，避免 422。
        """
        if isinstance(v, bool):
            return 0
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.lstrip("-").isdigit():
                try:
                    return int(s)
                except ValueError:
                    return 0
            return 0
        return 0
    # ↑↑↑ 新增结束 ↑↑↑
    scene_type: str = Field("custom", max_length=20, description="场景类型 sleep/study/work/sport/eat/custom")
    scene_name: str = Field("自定义", max_length=50, description="场景名称")
    bg_img: str = Field("", max_length=500, description="背景图标识/URL")
    bg_sound: str = Field("静音", max_length=50, description="背景音")


class CompanionEndRequest(BaseModel):
    """结束陪伴请求"""
    record_id: int = Field(..., gt=0, description="陪伴记录ID")
    remark: Optional[str] = Field(None, max_length=500, description="陪伴小结(可选)")
