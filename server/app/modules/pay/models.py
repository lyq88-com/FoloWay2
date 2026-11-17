# -*- coding: utf-8 -*-
"""
支付模块 ORM（新增表，不改旧表）

  pay_orders  支付订单（含幂等键、状态机、渠道、回调时间）
  user_vip    VIP 会员状态（当前只售卖 VIP，后续可扩展其它权益）
"""
from sqlalchemy import Column, BigInteger, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class PayOrder(Base):
    __tablename__ = "pay_orders"
    __table_args__ = (
        UniqueConstraint("order_no", name="uk_pay_order_no"),
        Index("idx_pay_order_user", "user_id", "id"),
        {"comment": "支付订单"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(VARCHAR(40), nullable=False, comment="业务订单号")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    product_type = Column(VARCHAR(20), nullable=False, default="vip", comment="商品类型")
    product_id = Column(VARCHAR(40), nullable=False, default="", comment="商品ID")
    product_name = Column(VARCHAR(100), nullable=False, default="", comment="商品名称快照")
    amount_cents = Column(Integer, nullable=False, default=0, comment="金额(分)")
    currency = Column(VARCHAR(8), nullable=False, default="CNY")
    provider = Column(VARCHAR(20), nullable=False, default="mock", comment="支付渠道")
    status = Column(VARCHAR(16), nullable=False, default="created",
                    comment="created/paid/closed/failed")
    idempotency_key = Column(VARCHAR(64), nullable=True, comment="幂等键")
    paid_at = Column(DATETIME, nullable=True, comment="支付时间")
    expire_at = Column(DATETIME, nullable=True, comment="订单过期时间")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())


class UserVip(Base):
    __tablename__ = "user_vip"
    __table_args__ = (
        UniqueConstraint("user_id", name="uk_user_vip_user"),
        {"comment": "用户 VIP 会员状态"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    expire_at = Column(DATETIME, nullable=False)
    source_order_no = Column(VARCHAR(40), nullable=False, default="")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
