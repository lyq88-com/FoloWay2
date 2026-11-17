# -*- coding: utf-8 -*-
"""
高危情绪检测（danger_sentiment）—— 安全合规批次新增

定位：比 CrisisService 更前置的一道「硬闸门」。
- CrisisService 关注的是「用户此刻很痛苦，需要共情陪伴」；
- danger_sentiment 关注的是「内容里出现了明确的高危信号词，业务链路必须先拦截并给出求助资源」。

使用位置：
- chat.py /chat/send 前置检测（返回 is_danger 事件给前端弹 danger_warn 弹窗）；
- 前端 common/content-check.js 有一份同源的关键词镜像，改这里时记得同步。

设计原则：零外部依赖、纯函数、绝不抛异常（检测失败按"未检出"放行，
不能因为安全模块挂掉导致用户无法聊天）。
"""
import re
from typing import Dict, List

# 高危信号词（自伤/自杀意图的明确表达）
DANGER_KEYWORDS = [
    "不想活", "想死", "自杀", "结束生命", "活不下去", "了结自己", "跳楼",
    "割腕", "吞安眠药", "安眠药", "想消失", "世界没有我更好", "没有我会更好",
    "撑不下去", "活着的意义是什么都无所谓", "想解脱", "告别了", "最后一句话",
    "kill myself", "suicide", "end my life",
]

# 自残相关（次级危险，提示但不强拦截语气可以更温和）
SELF_HARM_KEYWORDS = [
    "划自己", "伤害自己", "掐自己", "打自己", "self-harm",
]

# 求助资源（与 CrisisService.HOTLINES 保持一致的展示结构）
HOTLINES = [
    {"name": "全国心理援助热线", "phone": "400-161-9995", "hours": "24小时"},
    {"name": "北京心理危机研究与干预中心", "phone": "010-82951332", "hours": "24小时"},
    {"name": "希望24热线", "phone": "400-161-9995", "hours": "24小时"},
]

DANGER_MESSAGE = (
    "我听到了你话里很沉重的信号，我很担心你。\n"
    "你此刻的感受很重要，但它不适合只由 AI 来承接。\n"
    "请考虑联系下面这些 24 小时在线的专业热线，会有真人认真听你说话：\n"
)

# 命中时的公共干预话术（前端弹窗正文也可以直接用）
INTERVENTION_TEXT = (
    "你不需要一个人扛着这些。如果你愿意，可以拨打上面的电话，"
    "或者告诉你信任的人。我也会一直在这里陪着你。"
)

_WORD_RE = re.compile(r"[a-zA-Z]+")


def _contains_keyword(text: str, keywords: List[str]) -> List[str]:
    """返回命中的关键词列表（中英混合：英文按词边界匹配）"""
    hits = []
    low = (text or "").lower()
    for kw in keywords:
        if re.search(r"[a-zA-Z]", kw):
            # 英文关键词按词边界匹配，避免 "class" 误伤 "ass"
            if re.search(r"\b" + re.escape(kw.lower()) + r"\b", low):
                hits.append(kw)
        else:
            if kw in (text or ""):
                hits.append(kw)
    return hits


def detect_danger(text: str) -> Dict:
    """
    高危情绪检测。

    返回:
        {
          "is_danger": bool,          # 是否命中高危信号
          "level": "high"|"medium"|"none",
          "keywords": [...],           # 命中的关键词
          "message": str,              # 拦截时的提示话术
          "resources": HOTLINES,       # 求助资源（前端弹窗渲染用）
        }
    """
    result = {
        "is_danger": False,
        "level": "none",
        "keywords": [],
        "message": "",
        "resources": [],
    }
    try:
        text = text or ""
        if not text.strip():
            return result

        high_hits = _contains_keyword(text, DANGER_KEYWORDS)
        if high_hits:
            result.update({
                "is_danger": True,
                "level": "high",
                "keywords": high_hits,
                "message": DANGER_MESSAGE + "\n".join(
                    f"· {h['name']} {h['phone']}（{h['hours']}）" for h in HOTLINES
                ) + f"\n\n{INTERVENTION_TEXT}",
                "resources": HOTLINES,
            })
            return result

        harm_hits = _contains_keyword(text, SELF_HARM_KEYWORDS)
        if harm_hits:
            result.update({
                "is_danger": True,
                "level": "medium",
                "keywords": harm_hits,
                "message": (
                    "你提到想伤害自己，我有点担心。\n"
                    "不管发生了什么，先答应我对自己温柔一点。\n"
                    + "\n".join(f"· {h['name']} {h['phone']}（{h['hours']}）" for h in HOTLINES)
                ),
                "resources": HOTLINES,
            })
        return result
    except Exception as e:  # 绝不让安全检测反过来阻塞业务
        print(f"[danger_sentiment][WARN] 检测异常，按未检出处理: {type(e).__name__}: {e}")
        return result
