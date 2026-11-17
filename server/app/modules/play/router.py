# -*- coding: utf-8 -*-
"""
纯本地玩法上云 - HTTP 路由
==========================

挂载前缀：/api/v1/play（由 app/main.py 追加注册）

接口：
  GET   /play/state?keys=box,fragment,postcard   批量读取
  PUT   /play/state                              批量写入（乐观锁，冲突返回 409 + 服务端快照）
  GET   /play/capsules                           我的时光胶囊
  POST  /play/capsule                            封一颗新胶囊
  POST  /play/capsule/{id}/open                  开启胶囊（到期才可开）
  POST  /play/shop/order                         服务端定价下单（行锁扣币 + 写订单）
  GET   /play/shop/orders                        我的订单

安全约定：
  - user_id 只从 JWT 取，客户端传什么都不认；
  - play_key 白名单，payload 必须可 JSON 序列化且 <= 64KB；
  - 写接口按用户限流（进程内滑动窗口），日志不打印 payload 内容；
  - 商城价格只认服务端 catalog，客户端不能传价格。
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.modules.idea.content_safety import SlidingWindowLimiter
from app.schemas.common import ResponseBase

from .catalog import MALL_CATALOG
from .models import ShopOrder, UserCapsule, UserPlayState
from .schemas import CapsuleCreateIn, PlayStateBatchIn, ShopOrderIn

router = APIRouter(prefix="/play", tags=["玩法数据上云"])

PLAY_KEYS = ("box", "fragment", "postcard")
MAX_PAYLOAD_BYTES = 64 * 1024
MAX_BILLS = 300

# 写接口限流：60 次/分钟（单机内存版，够挡住高频刷写）
_limiter = SlidingWindowLimiter()
WRITE_LIMIT = 60
WRITE_WINDOW = 60


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _load(text: Optional[str], default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _parse_open_at(value: Optional[str]) -> Optional[datetime]:
    """解析开启时间，支持 YYYY-MM-DD 与 YYYY-MM-DD HH:MM:SS"""
    if not value:
        return None
    v = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(v, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt + timedelta(hours=23, minutes=59, seconds=59)
            return dt
        except ValueError:
            continue
    return None


# ============================================================
# 玩法状态（盲盒 / 碎片 / 明信片）
# ============================================================
@router.get("/state")
def get_play_state(
    keys: str = Query("box,fragment,postcard", description="逗号分隔的玩法 key"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量读取玩法状态；从未上传过的 key 返回 null（前端继续用本地数据）"""
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端玩法数据", 403)

    wanted = [k.strip() for k in (keys or "").split(",") if k.strip()]
    wanted = [k for k in wanted if k in PLAY_KEYS]
    if not wanted:
        return ResponseBase.error("keys 不合法", 400)

    rows = (
        db.query(UserPlayState)
        .filter(UserPlayState.user_id == user_id, UserPlayState.play_key.in_(wanted))
        .all()
    )
    found = {r.play_key: r for r in rows}

    states: Dict[str, Any] = {}
    for k in wanted:
        row = found.get(k)
        states[k] = None if not row else {
            "payload": _load(row.payload, None),
            "version": int(row.version or 0),
            "updatedAt": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else "",
        }
    return ResponseBase.success({"states": states})


@router.put("/state")
def save_play_state(
    req: PlayStateBatchIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    批量写入玩法状态（乐观锁）。

    请求 items 中任一条 version 与服务端不一致 → 整体不落库，
    返回 code=409 + data.conflicts（冲突 key 的服务端最新快照），
    前端据此合并后重试。
    """
    if user_id == 0:
        return ResponseBase.error("游客模式不支持云端玩法数据", 403)
    if not _limiter.allow(f"play_state:{user_id}", WRITE_LIMIT, WRITE_WINDOW):
        return ResponseBase.error("同步太频繁，请稍后再试", 429)

    items = list(req.items or [])
    if not items:
        return ResponseBase.error("items 不能为空", 400)
    if len(items) > len(PLAY_KEYS):
        return ResponseBase.error("单次最多同步 3 条", 400)

    normalized: Dict[str, PlayStateItem] = {}
    for it in items:
        if it.key not in PLAY_KEYS:
            return ResponseBase.error(f"不支持的玩法标识: {it.key}", 400)
        if it.key in normalized:
            return ResponseBase.error(f"重复的玩法标识: {it.key}", 400)
        try:
            raw = _dump(it.payload)
        except Exception:
            return ResponseBase.error(f"{it.key} 数据无法序列化", 400)
        if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            return ResponseBase.error(f"{it.key} 数据过大（上限 64KB）", 413)
        normalized[it.key] = it

    keys = list(normalized.keys())
    rows = {
        r.play_key: r
        for r in db.query(UserPlayState)
        .filter(UserPlayState.user_id == user_id, UserPlayState.play_key.in_(keys))
        .all()
    }

    # 先整体校验乐观锁，避免部分写成功造成不一致
    conflicts = []
    for k in keys:
        row = rows.get(k)
        if row is not None and int(normalized[k].version) != int(row.version or 0):
            conflicts.append({
                "key": k,
                "payload": _load(row.payload, None),
                "version": int(row.version or 0),
            })
    if conflicts:
        return ResponseBase(
            code=409,
            message="数据已在其他设备更新，请合并后重试",
            data={"conflicts": conflicts},
        )

    result = {}
    for k in keys:
        row = rows.get(k)
        raw = _dump(normalized[k].payload)
        if row is None:
            row = UserPlayState(user_id=user_id, play_key=k, payload=raw, version=1)
            db.add(row)
        else:
            row.payload = raw
            row.version = int(row.version or 0) + 1
        result[k] = {"version": int(row.version or 1)}

    db.commit()
    return ResponseBase.success({"states": result}, "已同步")


# ============================================================
# 时光胶囊
# ============================================================
@router.get("/capsules")
def list_capsules(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == 0:
        return ResponseBase.error("游客模式不支持时光胶囊", 403)
    rows = (
        db.query(UserCapsule)
        .filter(UserCapsule.user_id == user_id, UserCapsule.is_deleted == 0)
        .order_by(UserCapsule.created_at.desc())
        .limit(100)
        .all()
    )
    return ResponseBase.success({"list": [r.to_dict() for r in rows]})


@router.post("/capsule")
def create_capsule(
    req: CapsuleCreateIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == 0:
        return ResponseBase.error("游客模式不支持时光胶囊", 403)
    if not _limiter.allow(f"capsule:{user_id}", 10, 60):
        return ResponseBase.error("封存太频繁了，歇一会儿再写吧", 429)

    content = (req.content or "").strip()
    if not content:
        return ResponseBase.error("胶囊内容不能为空", 400)
    if len(content) > 2000:
        return ResponseBase.error("胶囊内容最多 2000 字", 400)

    open_at = _parse_open_at(req.openAt)
    if req.openAt and open_at is None:
        return ResponseBase.error("开启时间格式不正确", 400)
    if open_at is not None and open_at <= datetime.now():
        return ResponseBase.error("开启时间需要晚于现在", 400)

    row = UserCapsule(
        user_id=user_id,
        title=(req.title or "").strip()[:40],
        content=content,
        open_at=open_at,
        is_opened=0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseBase.success(row.to_dict(), "已封存")


@router.post("/capsule/{capsule_id}/open")
def open_capsule(
    capsule_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == 0:
        return ResponseBase.error("游客模式不支持时光胶囊", 403)

    row = (
        db.query(UserCapsule)
        .filter(
            UserCapsule.id == capsule_id,
            UserCapsule.user_id == user_id,
            UserCapsule.is_deleted == 0,
        )
        .first()
    )
    if not row:
        return ResponseBase.error("胶囊不存在", 404)
    if row.is_opened:
        return ResponseBase.success(row.to_dict())
    if row.open_at is not None and row.open_at > datetime.now():
        return ResponseBase.error("还没到开启时间", 400)

    row.is_opened = 1
    row.open_time = datetime.now()
    db.commit()
    db.refresh(row)
    return ResponseBase.success(row.to_dict(), "已开启")


# ============================================================
# 商城下单（服务端定价 + 行锁扣币）
# ============================================================
def _economy_to_dict(row) -> dict:
    return {
        "coins": int(row.coins or 0),
        "bills": _load(row.bills, []),
        "giftInventory": _load(row.gift_inventory, {}),
        "gachaTickets": int(row.gacha_tickets or 0),
        "unlockedDecos": _load(row.unlocked_decos, []),
        "totalCheckinRewarded": int(row.total_checkin_rewarded or 0),
        "giftedCount": int(row.gifted_count or 0),
    }


@router.post("/shop/order")
def create_shop_order(
    req: ShopOrderIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    服务端定价下单：
      1) 用 SELECT ... FOR UPDATE 锁住该用户的经济行，防并发重复扣款；
      2) 校验余额 → 扣币 → 发放商品 → 写订单，同一事务提交。
    前端必须在调用前先把本地经济状态同步到云端（/economy/state PUT），
    否则服务端余额为 0 会返回「云端资产尚未同步」。
    """
    if user_id == 0:
        return ResponseBase.error("游客模式请使用本地商城", 403)
    if not _limiter.allow(f"shop_order:{user_id}", 30, 60):
        return ResponseBase.error("购买太频繁，请稍后再试", 429)

    goods = MALL_CATALOG.get(req.goodsId)
    if not goods:
        return ResponseBase.error("商品不存在", 400)

    qty = max(1, min(10, int(req.qty or 1)))
    total = int(goods["price"]) * qty

    from app.models.economy import UserEconomy

    row = (
        db.query(UserEconomy)
        .filter(UserEconomy.user_id == user_id)
        .with_for_update()
        .first()
    )
    if row is None:
        return ResponseBase.error("云端资产尚未同步，请稍后重试", 400)
    if int(row.coins or 0) < total:
        return ResponseBase.error("金币不足，去打卡赚金币吧~", 400)

    # ---- 扣币 ----
    row.coins = int(row.coins or 0) - total

    gift_inventory = _load(row.gift_inventory, {}) or {}
    unlocked = _load(row.unlocked_decos, []) or []
    if goods["kind"] == "gift":
        gift_inventory[req.goodsId] = int(gift_inventory.get(req.goodsId, 0)) + qty
    elif goods["kind"] == "ticket":
        row.gacha_tickets = int(row.gacha_tickets or 0) + qty
    elif goods["kind"] == "deco":
        for _ in range(qty):
            if req.goodsId not in unlocked:
                unlocked.append(req.goodsId)

    bills: List[Any] = _load(row.bills, []) or []
    bills.append({
        "type": "expense",
        "amount": total,
        "source": "mall",
        "desc": f"商城购买「{goods['name']}」" + (f"×{qty}" if qty > 1 else ""),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    bills = bills[-MAX_BILLS:]

    row.gift_inventory = _dump(gift_inventory)
    row.unlocked_decos = _dump(unlocked)
    row.bills = _dump(bills)

    order = ShopOrder(
        user_id=user_id,
        goods_id=req.goodsId,
        goods_name=goods["name"],
        kind=goods["kind"],
        price=int(goods["price"]),
        qty=qty,
        total=total,
        coins_after=int(row.coins),
        status="paid",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    db.refresh(row)

    return ResponseBase.success({
        "order": order.to_dict(),
        "state": _economy_to_dict(row),
    }, f"购买成功：{goods['name']}")


@router.get("/shop/orders")
def list_shop_orders(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == 0:
        return ResponseBase.error("游客模式不支持订单查询", 403)
    rows = (
        db.query(ShopOrder)
        .filter(ShopOrder.user_id == user_id)
        .order_by(ShopOrder.id.desc())
        .limit(50)
        .all()
    )
    return ResponseBase.success({"list": [r.to_dict() for r in rows]})
