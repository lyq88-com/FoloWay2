# -*- coding: utf-8 -*-
"""
通用内容安全过滤（content_security）—— 安全合规批次新增

两个入口：
1. check_user_text(text)  —— 用户提交内容的前置校验（动态/世界/扭蛋剧本/评论/昵称等）。
   命中违规词时返回 ok=False，业务方直接拦截并提示。
2. filter_ai_output(text) —— AI 输出的后置过滤（聊天链路结果入库前挂一道），
   兜底清洗大模型偶尔吐出的违规词/联系方式/超长尾巴。

设计原则：零依赖纯函数、绝不抛异常（过滤失败按原文放行，不影响主流程）。
"""
import re
from typing import Dict, List

# ============ 违规词库（演示级，可按需扩充/接第三方内容安全 API） ============

# 涉政类：一律拦截（不区分语境，演示项目从严）
POLITICAL_WORDS = [
    "习近平", "毛泽东", "周恩来", "邓小平", "李克强", "李强", "胡锦涛", "温家宝",
    "江泽民", "党和政府", "共产党", "国民党", "法轮功", "六四", "天安门事件",
    "政变", "推翻政府", "颠覆国家", "台独", "港独", "藏独", "疆独",
]

# 色情低俗类
PORN_WORDS = [
    "约炮", "援交", "一夜情", "嫖娼", "卖淫", "裸聊", "福利姬",
    "强奸", "轮奸", "猥亵", "做爱", "打炮", "内射",
]

# 暴力恐暴 / 违禁品类
VIOLENCE_WORDS = [
    "制炸弹", "做炸弹", "制毒", "冰毒", "海洛因", "大麻", "买枪", "卖枪",
    "杀人偿命", "去杀死", "砍死他", "炸掉学校",
]

# 赌博诈骗类
FRAUD_WORDS = [
    "博彩", "赌球", "六合彩", "网赌", "洗钱", "刷单兼职", "代开发票",
    "办假证", "套现", "博一下就翻本",
]

# 违规组合分类 → 提示语
_CATEGORY_MESSAGE = {
    "political": "内容包含涉政敏感信息，请修改后再发布",
    "porn": "内容包含低俗色情信息，请修改后再发布",
    "violence": "内容包含暴力违禁信息，请修改后再发布",
    "fraud": "内容包含赌博诈骗相关信息，请修改后再发布",
    "spam": "内容疑似广告引流信息，请修改后再发布",
}

_RULES: List[tuple] = [
    ("political", POLITICAL_WORDS),
    ("porn", PORN_WORDS),
    ("violence", VIOLENCE_WORDS),
    ("fraud", FRAUD_WORDS),
]

# 广告引流：手机号 / 微信号 / URL
_AD_PATTERNS = [
    (r"1[3-9]\d{9}", "spam"),
    (r"(加|+v|+V|薇信|威信|微信)\s*[:：]?\s*[a-zA-Z0-9_\-]{5,}", "spam"),
    (r"(https?://|www\.)\S+", "spam"),
]

# AI 输出兜底也要替换的词（比用户侧宽松些：只做替换不做拦截）
_AI_REPLACE_WORDS = POLITICAL_WORDS + PORN_WORDS + VIOLENCE_WORDS + FRAUD_WORDS

# 单条文本长度上限（动态/笔记/剧本等通用）
MAX_TEXT_LENGTH = 2000


def check_user_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> Dict:
    """
    用户提交内容前置校验。

    返回: {"ok": bool, "reason": str, "hits": [...], "category": str|""}
    """
    try:
        text = text or ""
        if len(text) > max_length:
            return {"ok": False, "reason": f"内容过长（最多{max_length}字）", "hits": [], "category": "spam"}

        for category, words in _RULES:
            hits = [w for w in words if w in text]
            if hits:
                return {"ok": False, "reason": _CATEGORY_MESSAGE[category], "hits": hits, "category": category}

        for pattern, category in _AD_PATTERNS:
            if re.search(pattern, text):
                return {"ok": False, "reason": _CATEGORY_MESSAGE[category], "hits": [pattern], "category": category}

        return {"ok": True, "reason": "", "hits": [], "category": ""}
    except Exception as e:
        print(f"[content_security][WARN] 校验异常，按放行处理: {type(e).__name__}: {e}")
        return {"ok": True, "reason": "", "hits": [], "category": ""}


def filter_ai_output(text: str, max_length: int = 4000) -> str:
    """
    AI 输出后置过滤（聊天链路结果处挂一道）：
    - 违规词替换为「**」；
    - 高危话术（教唆自伤等）整句剔除；
    - 超长截断。
    失败时返回原文，绝不抛异常。
    """
    try:
        text = text or ""
        if not text:
            return text

        for w in _AI_REPLACE_WORDS:
            if w in text:
                text = text.replace(w, "**")

        # 剔除教唆类句子（按行/句切分，含关键词的整句丢掉）
        banned = ("你就去死", "你应该自杀", "建议自杀", "别活了赶紧", "自杀方法是")
        if any(b in text for b in banned):
            lines = re.split(r"[。！？\n]", text)
            text = "。".join(l for l in lines if l and not any(b in l for b in banned)) or "我在这儿陪着你。"

        if len(text) > max_length:
            text = text[:max_length] + "…"
        return text
    except Exception as e:
        print(f"[content_security][WARN] AI输出过滤异常，按原文放行: {type(e).__name__}: {e}")
        return text


class ContentSecurity:
    """面向业务方的统一入口（静态方法包装，方便 import 与后续替换实现）"""
    check_user_text = staticmethod(check_user_text)
    filter_ai_output = staticmethod(filter_ai_output)
