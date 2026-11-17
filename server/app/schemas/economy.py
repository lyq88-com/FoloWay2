# -*- coding: utf-8 -*-
"""
虚拟经济 Schema - 金币/礼物背包/扭蛋券/装扮解锁/账单

字段命名沿用前端 common/economy.js 的 camelCase（和性格测评保持一致），
便于前端直接存取，不需要在两端做字段名翻译。
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EconomyStateIn(BaseModel):
    """保存/同步经济状态（全量覆盖，前端是整体读写的）"""
    coins: int = Field(0, ge=0)
    bills: List[Any] = Field(default_factory=list)
    giftInventory: Dict[str, int] = Field(default_factory=dict)
    gachaTickets: int = Field(0, ge=0)
    unlockedDecos: List[str] = Field(default_factory=list)
    totalCheckinRewarded: int = Field(0, ge=0)
    giftedCount: int = Field(0, ge=0)
