# -*- coding: utf-8 -*-
"""
打卡联动服务（模块1/3/4 与原有打卡系统的数据互通层）
打卡成功后调用 run_checkin_linkage()：
  1) 发放扭蛋币（每打卡一个习惯 +10，写入 user_gacha_wallet）
  2) 用户所在世界：世界打卡总数+1、AI 角色发布打卡反馈笔记、检查剧情碎片解锁

设计原则：
  - 全程 try/except 隔离，任何联动失败都不影响打卡主流程（不抛异常）
  - 每次调用独立 commit，避免污染打卡事务
"""
import traceback

from sqlalchemy.orm import Session

from app.models.gacha import UserGachaWallet
from app.services import world_service

CHECKIN_COIN_REWARD = 10  # 每次习惯打卡奖励扭蛋币


def _award_coin(db: Session, user_id: int) -> int:
    """发放扭蛋币，返回发放后余额"""
    wallet = db.query(UserGachaWallet).filter(
        UserGachaWallet.user_id == user_id
    ).first()
    if not wallet:
        wallet = UserGachaWallet(
            user_id=user_id, coin_balance=CHECKIN_COIN_REWARD,
            total_earned=CHECKIN_COIN_REWARD, total_cost=0,
        )
        db.add(wallet)
    else:
        wallet.coin_balance += CHECKIN_COIN_REWARD
        wallet.total_earned += CHECKIN_COIN_REWARD
    db.commit()
    return wallet.coin_balance


def run_checkin_linkage(db: Session, user_id: int,
                        habit_name: str, habit_id: int = 0,
                        user_name: str = "") -> dict:
    """
    打卡联动主入口（habit.py checkin 成功后调用）。
    绝不抛出异常；返回联动结果摘要，用于响应中带给前端展示。
    """
    result = {"coin_awarded": 0, "coin_balance": 0,
              "worlds_affected": 0, "plots_unlocked": 0, "linkage_error": ""}
    try:
        # 1) 扭蛋币
        result["coin_balance"] = _award_coin(db, user_id)
        result["coin_awarded"] = CHECKIN_COIN_REWARD

        # 2) 世界联动（AI反馈笔记 + 剧情解锁）
        summary = world_service.handle_checkin(
            db, user_id, habit_name=habit_name,
            user_name=user_name or "小伙伴", habit_id=habit_id,
        )
        result["worlds_affected"] = len(summary.get("worlds", []))
        result["plots_unlocked"] = len(summary.get("unlocked", []))
    except Exception:
        # 联动失败仅记录，不影响打卡
        traceback.print_exc()
        db.rollback()
        result["linkage_error"] = "linkage failed (ignored)"
    return result
