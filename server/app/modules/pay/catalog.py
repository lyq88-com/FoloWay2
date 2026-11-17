# -*- coding: utf-8 -*-
"""支付商品目录（服务端定价权威来源，前端传的价格一律不认）"""

VIP_PACKAGES = [
    {"id": "1", "name": "VIP月卡", "days": 30, "priceCents": 1990, "originalCents": 2990},
    {"id": "2", "name": "VIP季卡", "days": 90, "priceCents": 5290, "originalCents": 8970},
    {"id": "3", "name": "VIP年卡", "days": 365, "priceCents": 17800, "originalCents": 35880},
]

_VIP_MAP = {p["id"]: p for p in VIP_PACKAGES}


def get_product(product_type: str, product_id: str):
    """按类型取商品，不存在返回 None"""
    if product_type == "vip":
        return _VIP_MAP.get(str(product_id))
    return None


def list_packages():
    return [
        {
            "id": int(p["id"]),
            "name": p["name"],
            "days": p["days"],
            "price": round(p["priceCents"] / 100, 2),
            "priceCents": p["priceCents"],
            "originalPrice": round(p["originalCents"] / 100, 2),
        }
        for p in VIP_PACKAGES
    ]
