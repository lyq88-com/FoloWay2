# -*- coding: utf-8 -*-
"""
支付渠道抽象

  真实渠道（微信/支付宝）只需实现同一接口：
    - create_payment(order) -> dict  返回给前端的支付参数
    - verify_callback(headers, body) -> bool  回调验签
  然后注册到 _PROVIDERS，配置 PAY_PROVIDER=wechat 即可切换，业务层无需改动。
"""
import hashlib
import hmac

from app.core.config import settings


class PayProvider:
    name = "base"

    def create_payment(self, order) -> dict:
        raise NotImplementedError

    def verify_callback(self, headers, body) -> bool:
        return False


class MockProvider(PayProvider):
    """演示渠道：返回「模拟收银台」参数，由前端调用 mock-pay 完成支付

    - 不涉及真实资金；
    - 订单、幂等、状态机与真实渠道完全一致，切换渠道不影响业务数据；
    - 若配置了 PAY_MOCK_SECRET，回调必须带 X-Mock-Signature = HMAC-SHA256(secret, orderNo)。
    """
    name = "mock"

    def create_payment(self, order) -> dict:
        return {
            "provider": "mock",
            "orderNo": order.order_no,
            "amountCents": order.amount_cents,
            "payParams": {"type": "mock-cashier", "orderNo": order.order_no},
            "demo": True,
        }

    def verify_callback(self, headers, body) -> bool:
        secret = (settings.pay_mock_secret or "").strip()
        if not secret:
            return True  # 未配置密钥时仅用于本地/测试环境
        order_no = str((body or {}).get("orderNo") or (body or {}).get("order_no") or "")
        signature = ""
        for key, value in (headers or {}).items():
            if str(key).lower() == "x-mock-signature":
                signature = str(value)
                break
        expected = hmac.new(secret.encode(), order_no.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)


_PROVIDERS = {
    "mock": MockProvider(),
}


class UnknownProvider(Exception):
    pass


def get_provider(name: str = "") -> PayProvider:
    key = (name or settings.pay_provider or "mock").strip().lower()
    provider = _PROVIDERS.get(key)
    if provider is None:
        raise UnknownProvider(key)
    return provider


def available_providers():
    return list(_PROVIDERS.keys())
