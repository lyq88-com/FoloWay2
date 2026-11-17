# -*- coding: utf-8 -*-
"""
内容安全 & 防刷限流（模块内自包含）
====================================

1. 内容审核：先做一道本地敏感词 / 违法信息拦截，命中即拒绝入库。
   真实生产环境应叠加平台级「内容安全」接口（如微信 security.msgSecCheck、
   或云端文本审核）。这里把审核抽象成 `audit_text()`，替换实现即可，调用方不变，
   不依赖任何既有审核代码（项目内目前也没有通用的文本审核服务）。

2. 防刷：进程内滑动窗口限流（单机内存版）。够用来挡住「高频发布 / 高频点亮」，
   后续可无痛换成 Redis 计数（接口签名保持一致）。
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


# ------------------------------------------------------------
# 敏感词（示例集，覆盖违规交易 / 涉黄涉赌 / 辱骂等常见类别）
# 可自行扩充；命中后统一拒绝发布。
# ------------------------------------------------------------
SENSITIVE_WORDS = [
    # 违法违规交易
    "代开发票", "办证", "刷单", "赌球", "博彩", "六合彩", "私彩",
    # 涉黄涉赌
    "约炮", "一夜情", "援交", "嫖", "卖淫",
    # 辱骂/攻击（简表）
    "傻逼", "傻B", "滚你", "去死", "贱人", "杂种",
    # 诈骗/引流
    "加微信", "加VX", "加qq", "私聊加", "扫码进群", "兼职日结", "高薪日结",
]

# 明显不适合公开传播的广告式引流字符组合（正则级别可再增强）
_BLOCK_PATTERNS = ["http://", "https://", "www."]


def audit_text(text: str) -> Tuple[bool, str]:
    """
    审核一段文本。
    返回 (是否通过, 拒绝原因)。
    通过 → (True, "")
    拒绝 → (False, "原因")
    """
    t = (text or "").strip()
    if not t:
        return False, "内容不能为空"
    if len(t) > 200:
        return False, "想法最多 200 字"

    low = t.lower()
    for w in SENSITIVE_WORDS:
        if w.lower() in low:
            return False, "内容包含违规信息，发布失败"
    for p in _BLOCK_PATTERNS:
        if p in low:
            return False, "请勿发布外部链接"
    return True, ""


# ------------------------------------------------------------
# 限流器
# ------------------------------------------------------------
class SlidingWindowLimiter:
    """进程内滑动窗口限流（按 key 记录最近 N 次操作时间戳）"""

    def __init__(self):
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        允许则 True 并记录一次；超限则 False。
        key: 例如 "publish:12" / "light:12"
        """
        now = time.time()
        q = self._hits[key]
        # 弹出窗口外的记录
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


# 全局单例
limiter = SlidingWindowLimiter()

# 各行为阈值（调用方直接用常量，便于统一调整）
PUBLISH_LIMIT = 5       # 发布：5 次 / 10 分钟
PUBLISH_WINDOW = 600
LIGHT_LIMIT = 40        # 点亮：40 次 / 10 分钟
LIGHT_WINDOW = 600
REACT_LIMIT = 60        # 轻互动
REACT_WINDOW = 600
MSG_LIMIT = 60          # 私聊发送
MSG_WINDOW = 60
