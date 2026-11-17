# -*- coding: utf-8 -*-
"""
虚拟经济 API - 把 common/economy.js 的 localStorage 状态搬到云端

接口:
  GET /economy/state       读取云端经济状态(未初始化返回默认空状态)
  PUT /economy/state       全量覆盖保存(前端整体读写, 不做增量合并)

约定:
  - 首次读取若无记录, 不自动建行 —— 避免给从未打开过商城的用户插一堆空数据
  - 保存时用 INSERT ... ON DUPLICATE KEY UPDATE 的等价实现(先查后写), 幂等
"""
import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.economy import UserEconomy
from app.schemas.common import ResponseBase
from app.schemas.economy import EconomyStateIn
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/economy", tags=["虚拟经济"])

# 与前端 common/economy.js 的 MAX_BILLS 保持一致
MAX_BILLS = 300


def _dump(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return "{}" if isinstance(value, dict) else "[]"


def _load(text, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _to_dict(row: UserEconomy) -> dict:
    return {
        "coins": row.coins,
        "bills": _load(row.bills, []),
        "giftInventory": _load(row.gift_inventory, {}),
        "gachaTickets": row.gacha_tickets,
        "unlockedDecos": _load(row.unlocked_decos, []),
        "totalCheckinRewarded": row.total_checkin_rewarded,
        "giftedCount": row.gifted_count,
    }


@router.get("/state")
def get_state(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """读取云端经济状态"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端经济数据", 403)

    row = db.query(UserEconomy).filter(UserEconomy.user_id == user_id).first()
    if not row:
        return ResponseBase.success({
            "initialized": False,
            "state": {
                "coins": 0, "bills": [], "giftInventory": {},
                "gachaTickets": 0, "unlockedDecos": [],
                "totalCheckinRewarded": 0, "giftedCount": 0,
            },
        })
    return ResponseBase.success({"initialized": True, "state": _to_dict(row)})


@router.put("/state")
def save_state(req: EconomyStateIn, user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """全量保存经济状态(幂等)"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端保存", 403)

    bills: List[Any] = list(req.bills)[-MAX_BILLS:]

    row = db.query(UserEconomy).filter(UserEconomy.user_id == user_id).first()
    if not row:
        row = UserEconomy(user_id=user_id)
        db.add(row)

    row.coins = req.coins
    row.gacha_tickets = req.gachaTickets
    row.total_checkin_rewarded = req.totalCheckinRewarded
    row.gifted_count = req.giftedCount
    row.gift_inventory = _dump(req.giftInventory)
    row.unlocked_decos = _dump(req.unlockedDecos)
    row.bills = _dump(bills)

    db.commit()
    db.refresh(row)
    return ResponseBase.success(_to_dict(row), "已同步到云端")
