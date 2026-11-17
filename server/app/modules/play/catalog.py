# -*- coding: utf-8 -*-
"""
商城商品服务端目录（价格权威来源）

必须与前端 frontend/common/economy.js 的 GIFT_CATALOG / MALL_GOODS 保持一致：
  - 前端展示可以用本地目录；
  - 真正下单时服务端只认这里的价格与品类，杜绝前端改价 / 伪造品类。
"""

MALL_CATALOG = {
    # ---- 礼物 ----
    "flower": {"name": "小花花", "price": 10, "kind": "gift"},
    "star": {"name": "小星星", "price": 20, "kind": "gift"},
    "milktea": {"name": "奶茶", "price": 30, "kind": "gift"},
    "cake": {"name": "小蛋糕", "price": 50, "kind": "gift"},
    "rose": {"name": "玫瑰花", "price": 66, "kind": "gift"},
    "bear": {"name": "小熊玩偶", "price": 88, "kind": "gift"},
    "fireworks": {"name": "烟花", "price": 128, "kind": "gift"},
    "diamond": {"name": "钻石项链", "price": 199, "kind": "gift"},
    "moon": {"name": "月亮", "price": 520, "kind": "gift"},
    # ---- 扭蛋券 ----
    "gacha_ticket": {"name": "扭蛋券", "price": 60, "kind": "ticket"},
    # ---- 装扮 ----
    "deco_bubble": {"name": "限定气泡·星河", "price": 120, "kind": "deco"},
    "deco_bubble_sakura": {"name": "限定气泡·樱花", "price": 120, "kind": "deco"},
    "deco_bg_aurora": {"name": "限定聊天背景·极光", "price": 150, "kind": "deco"},
    "deco_voice": {"name": "限定音色·精灵", "price": 180, "kind": "deco"},
}
