# -*- coding: utf-8 -*-
"""
支付接口（/api/v1/pay/*）

  POST /pay/orders                     创建订单，返回渠道支付参数
  GET  /pay/orders/{order_no}          查询订单状态
  POST /pay/orders/{order_no}/mock-pay 模拟收银台确认（仅 mock 渠道）
  POST /pay/callback/{provider}        渠道异步回调占位（真渠道上线后在此验签+确认）
  GET  /pay/packages                   VIP 套餐（服务端定价）
  GET  /pay/vip/status                 当前用户会员状态
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.modules.pay import service as pay_service
from app.modules.pay.catalog import list_packages
from app.modules.pay.providers import UnknownProvider, get_provider
from app.schemas.common import ResponseBase

router = APIRouter(prefix="/pay", tags=["支付"])


class CreateOrderIn(BaseModel):
    productType: str = Field("vip", max_length=20)
    productId: str = Field(..., max_length=40)
    idempotencyKey: str = Field("", max_length=64)


class MockPayIn(BaseModel):
    success: bool = True


@router.get("/packages")
def packages():
    return ResponseBase.success(list_packages())


@router.post("/orders")
def create_order(req: CreateOrderIn, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        order, provider = pay_service.create_order(
            db, user_id, req.productType, req.productId, req.idempotencyKey)
    except pay_service.PayError as e:
        return ResponseBase.error(e.message, e.code)
    except UnknownProvider:
        return ResponseBase.error("支付渠道未配置", 500)

    data = pay_service.serialize(order)
    data.update(provider.create_payment(order))
    return ResponseBase.success(data)


@router.get("/orders/{order_no}")
def order_detail(order_no: str, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        order = pay_service.get_order(db, user_id, order_no)
    except pay_service.PayError as e:
        return ResponseBase.error(e.message, e.code)
    return ResponseBase.success(pay_service.serialize(order))


@router.post("/orders/{order_no}/mock-pay")
def mock_pay(order_no: str, req: MockPayIn, user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """模拟收银台：仅用于演示/联调，生产环境请移除或加开关"""
    try:
        order = pay_service.get_order(db, user_id, order_no)
    except pay_service.PayError as e:
        return ResponseBase.error(e.message, e.code)

    if order.provider != "mock":
        return ResponseBase.error("该订单不是模拟支付订单", 403)
    if not req.success:
        if order.status == "created":
            order.status = "closed"
            db.commit()
        return ResponseBase.success({"paid": False, "orderNo": order.order_no})

    try:
        order = pay_service.pay_order(db, user_id, order_no)
    except pay_service.PayError as e:
        return ResponseBase.error(e.message, e.code)
    data = pay_service.serialize(order)
    data.update(pay_service.vip_status(db, user_id))
    return ResponseBase.success(data)


@router.post("/callback/{provider}")
async def pay_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """渠道异步回调（占位）

    真实渠道接入时：在此完成验签 → 根据回调里的订单号调用 pay_service.pay_order。
    mock 渠道默认放行，便于本地联调；配置 PAY_MOCK_SECRET 后要求 HMAC 签名。
    """
    try:
        impl = get_provider(provider)
    except UnknownProvider:
        return ResponseBase.error("未知支付渠道", 404)

    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    headers = dict(request.headers)
    if not impl.verify_callback(headers, body):
        return ResponseBase.error("回调签名校验失败", 401)

    order_no = str(body.get("orderNo") or body.get("order_no") or "")
    order = pay_service.get_order_by_no(db, order_no)
    if order is None:
        # 按渠道规范：找不到订单也返回成功，避免渠道无限重试；由告警日志排查
        return ResponseBase.success({"received": True, "orderNo": order_no})

    success = body.get("success", True)
    if success is False:
        if order.status == "created":
            order.status = "failed"
            db.commit()
        return ResponseBase.success({"received": True, "orderNo": order_no})

    try:
        pay_service.pay_order(db, order.user_id, order_no)
    except pay_service.PayError as e:
        return ResponseBase.success({"received": True, "orderNo": order_no, "note": e.message})
    return ResponseBase.success({"received": True, "orderNo": order_no})


@router.get("/vip/status")
def vip_status(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return ResponseBase.success(pay_service.vip_status(db, user_id))
