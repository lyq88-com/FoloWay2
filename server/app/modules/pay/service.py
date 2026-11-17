# -*- coding: utf-8 -*-
"""
支付业务层：下单 / 支付确认 / 会员状态

状态机：created → paid
        created → closed（超时未支付）
        created → failed（渠道返回失败）
  已 paid 的订单重复确认不会重复发放权益（幂等）。
"""
import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.pay.catalog import get_product
from app.modules.pay.models import PayOrder, UserVip
from app.modules.pay.providers import get_provider

ORDER_TTL_MINUTES = 30


class PayError(Exception):
    def __init__(self, message, code=400):
        super().__init__(message)
        self.message = message
        self.code = code


def _order_no() -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tail = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"P{stamp}{tail}"


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def serialize(order: PayOrder) -> dict:
    now = datetime.now()
    paid = order.status == "paid"
    return {
        "orderNo": order.order_no,
        "productType": order.product_type,
        "productId": order.product_id,
        "productName": order.product_name,
        "amountCents": int(order.amount_cents or 0),
        "payAmount": int(order.amount_cents or 0),
        "currency": order.currency,
        "provider": order.provider,
        "status": order.status,
        "paid": paid,
        "expireAt": _fmt(order.paid_at) if paid else None,
        "orderExpireAt": _fmt(order.expire_at),
        "createdAt": _fmt(order.created_at),
        "remainingSeconds": max(0, int((order.expire_at - now).total_seconds()))
        if order.expire_at and not paid else 0,
    }


def create_order(db: Session, user_id: int, product_type: str, product_id: str,
                 idempotency_key: str = "") -> tuple:
    product = get_product(product_type, product_id)
    if product is None:
        raise PayError("商品不存在", 404)

    # 幂等 1：显式幂等键
    if idempotency_key:
        exist = (db.query(PayOrder)
                 .filter(PayOrder.user_id == user_id,
                         PayOrder.idempotency_key == idempotency_key)
                 .first())
        if exist is not None:
            return exist, get_provider(exist.provider)

    # 幂等 2：同一用户 5 分钟内重复点同一个商品，复用未支付订单
    recent = (db.query(PayOrder)
              .filter(PayOrder.user_id == user_id,
                      PayOrder.product_type == product_type,
                      PayOrder.product_id == str(product_id),
                      PayOrder.status == "created",
                      PayOrder.created_at >= datetime.now() - timedelta(minutes=5))
              .order_by(PayOrder.id.desc())
              .first())
    if recent is not None and recent.expire_at and recent.expire_at > datetime.now():
        return recent, get_provider(recent.provider)

    provider = get_provider()
    order = PayOrder(
        order_no=_order_no(),
        user_id=user_id,
        product_type=product_type,
        product_id=str(product_id),
        product_name=product["name"],
        amount_cents=int(product["priceCents"]),
        currency="CNY",
        provider=provider.name,
        status="created",
        idempotency_key=(idempotency_key or None),
        expire_at=datetime.now() + timedelta(minutes=ORDER_TTL_MINUTES),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order, provider


def get_order(db: Session, user_id: int, order_no: str) -> PayOrder:
    order = (db.query(PayOrder)
             .filter(PayOrder.order_no == order_no, PayOrder.user_id == user_id)
             .first())
    if order is None:
        raise PayError("订单不存在", 404)
    if order.status == "created" and order.expire_at and order.expire_at < datetime.now():
        order.status = "closed"
        db.commit()
    return order


def get_order_by_no(db: Session, order_no: str):
    """回调场景：按订单号查（不限制用户），不存在返回 None"""
    return db.query(PayOrder).filter(PayOrder.order_no == order_no).first()


def pay_order(db: Session, user_id: int, order_no: str) -> PayOrder:
    """确认支付（mock 收银台 / 真实渠道回调最终都走这里）"""
    order = (db.query(PayOrder)
             .filter(PayOrder.order_no == order_no, PayOrder.user_id == user_id)
             .with_for_update()
             .first())
    if order is None:
        raise PayError("订单不存在", 404)
    if order.status == "paid":
        return order  # 幂等：重复确认不重复发放
    if order.status != "created":
        raise PayError("订单已关闭，请重新下单", 409)
    if order.expire_at and order.expire_at < datetime.now():
        order.status = "closed"
        db.commit()
        raise PayError("订单已过期，请重新下单", 409)

    _grant(db, user_id, order)

    order.status = "paid"
    order.paid_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def _grant(db: Session, user_id: int, order: PayOrder):
    """发放权益：VIP 到期时间顺延（不覆盖未到期时长）"""
    product = get_product(order.product_type, order.product_id)
    if product is None:
        raise PayError("商品已下架", 409)

    vip = db.query(UserVip).filter(UserVip.user_id == user_id).with_for_update().first()
    now = datetime.now()
    if vip is None:
        vip = UserVip(user_id=user_id,
                      expire_at=now + timedelta(days=int(product["days"])),
                      source_order_no=order.order_no)
        db.add(vip)
    else:
        base = vip.expire_at if vip.expire_at and vip.expire_at > now else now
        vip.expire_at = base + timedelta(days=int(product["days"]))
        vip.source_order_no = order.order_no


def vip_status(db: Session, user_id: int) -> dict:
    vip = db.query(UserVip).filter(UserVip.user_id == user_id).first()
    now = datetime.now()
    if vip is None or vip.expire_at is None or vip.expire_at <= now:
        return {"isVip": False, "expireAt": None, "remainDays": 0}
    remain = max(0, (vip.expire_at - now).days + (1 if (vip.expire_at - now).seconds else 0))
    return {
        "isVip": True,
        "expireAt": _fmt(vip.expire_at),
        "remainDays": remain,
    }
