# -*- coding: utf-8 -*-
"""
纯本地玩法上云 - ORM 模型（3 张独立新表）

  user_play_state  盲盒 / 碎片 / 明信片 3 类玩法状态的通用键值存储
  user_capsule     时光胶囊
  shop_order       商城订单（服务端定价 + 服务端扣币的凭据）

设计：
  - play_key 收敛为 box / fragment / postcard 三个白名单值；
  - payload 用 MEDIUMTEXT 存 JSON，结构由前端定义，服务端只做大小与合法性校验，
    兼容 MySQL 5.7（不使用 JSON 列）；
  - version 做乐观锁：每写一次 +1，客户端带旧版本写入时返回 409 + 服务端快照，
    避免多设备同时写入时后写覆盖先写。
"""
from sqlalchemy import Column, BigInteger, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import VARCHAR, INTEGER, TINYINT, DATETIME, MEDIUMTEXT
from sqlalchemy.sql import func

from app.core.database import Base


class UserPlayState(Base):
    """用户玩法状态（一个用户 × 一个玩法 一行）"""
    __tablename__ = "user_play_state"
    __table_args__ = (
        UniqueConstraint("user_id", "play_key", name="uk_play_state_user_key"),
        {"comment": "纯本地玩法状态上云(box/fragment/postcard)"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID(users.id)")
    play_key = Column(VARCHAR(32), nullable=False, comment="玩法标识 box/fragment/postcard")
    payload = Column(MEDIUMTEXT, nullable=True, comment="状态 JSON 字符串(<=64KB)")
    version = Column(INTEGER, nullable=False, default=1, comment="乐观锁版本号")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        comment="创建时间")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp(), comment="更新时间")


class UserCapsule(Base):
    """时光胶囊（写给未来的一段话，可设定开启时间）"""
    __tablename__ = "user_capsule"
    __table_args__ = (
        Index("idx_capsule_user", "user_id"),
        {"comment": "时光胶囊"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    title = Column(VARCHAR(60), nullable=False, default="", comment="胶囊标题")
    content = Column(VARCHAR(2000), nullable=False, default="", comment="胶囊正文")
    open_at = Column(DATETIME, nullable=True, comment="开启时间, NULL=不设期限(随时可开)")
    is_opened = Column(TINYINT, nullable=False, default=0, comment="是否已开启 0否 1是")
    open_time = Column(DATETIME, nullable=True, comment="实际开启时间")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除 0正常 1已删除")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        comment="封存时间")

    def to_dict(self):
        from datetime import datetime
        now = datetime.now()
        openable = bool(self.open_at is None or self.open_at <= now)
        return {
            "id": self.id,
            "title": self.title or "",
            "content": self.content or "",
            "openAt": self.open_at.strftime("%Y-%m-%d %H:%M:%S") if self.open_at else "",
            "isOpened": int(self.is_opened or 0),
            "isOpenable": bool(openable or self.is_opened),
            "openTime": self.open_time.strftime("%Y-%m-%d %H:%M:%S") if self.open_time else "",
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class ShopOrder(Base):
    """商城订单（服务端定价扣币后的凭证，前端不可指定价格）"""
    __tablename__ = "shop_order"
    __table_args__ = (
        Index("idx_shop_order_user", "user_id"),
        {"comment": "商城订单"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    goods_id = Column(VARCHAR(64), nullable=False, comment="商品ID")
    goods_name = Column(VARCHAR(64), nullable=False, default="", comment="商品名称快照")
    kind = Column(VARCHAR(16), nullable=False, default="", comment="gift/ticket/deco")
    price = Column(INTEGER, nullable=False, default=0, comment="单价(服务端定价)")
    qty = Column(INTEGER, nullable=False, default=1, comment="数量")
    total = Column(INTEGER, nullable=False, default=0, comment="总价")
    coins_after = Column(INTEGER, nullable=False, default=0, comment="扣款后余额")
    status = Column(VARCHAR(16), nullable=False, default="paid", comment="paid")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        comment="下单时间")

    def to_dict(self):
        return {
            "id": self.id,
            "goodsId": self.goods_id,
            "goodsName": self.goods_name,
            "kind": self.kind,
            "price": self.price,
            "qty": self.qty,
            "total": self.total,
            "coinsAfter": self.coins_after,
            "status": self.status,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }
