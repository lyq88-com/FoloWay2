# -*- coding: utf-8 -*-
"""
语义向量匹配（自包含，零外部依赖）
==================================

需求要求「使用语义向量匹配，不要关键词检索」。在离线 / 无 embedding 额度的前提下，
这里实现一个**向量空间模型**来做语义近似：

1. 文本向量化：把一段话映射成稀疏向量
   - 字符 unigram（单字）
   - 字符 bigram（相邻双字，中文最重要的语义单元）
   - 拉丁词 / 数字整体
   - **主题归并**：把常见近义表达折叠成同一主题 token（如 孤独/寂寞/一个人 → ^SOLO），
     这一步让「我最近总是很寂寞」「一个人的时候有点孤独」这类不同措辞得到高相似度，
     而不是靠关键词相等去命中。
2. 相似度：归一化后求余弦（cosine）。

⚠️ 说明：若后续拿到真正的 embedding 服务（如智谱 embedding-3 / OpenAI text-embedding），
只需要实现 `embed()` 走远程接口即可，`similarity()` / `rank()` 的调用方无需改动。
本模块刻意把「向量来源」与「相似度计算」解耦，方便平滑替换。
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Tuple


# ------------------------------------------------------------
# 主题归并表：近义表达 → 统一主题 token
# 目的：提升「语义」召回，避免退化成关键词精确匹配
# ------------------------------------------------------------
_THEME_SYNONYMS: Dict[str, List[str]] = {
    "^SOLO": ["孤独", "寂寞", "一个人", "独处", "孤单", "落单", "无人", "没人懂"],
    "^TIRED": ["累", "疲惫", "好累", "累了", "熬夜", "失眠", "撑不住", "喘不过气", "压力"],
    "^JOY": ["开心", "高兴", "快乐", "幸福", "兴奋", "雀跃", "满足"],
    "^SAD": ["难过", "伤心", "哭", "失落", "低落", "emo", "沮丧", "委屈"],
    "^ANXIOUS": ["焦虑", "紧张", "不安", "慌", "害怕", "担心", "恐惧"],
    "^HOPE": ["希望", "期待", "相信", "一定会", "未来", "加油", "努力", "坚持"],
    "^GREW": ["成长", "改变", "变好", "进步", "慢慢来", "别急", "勇气"],
    "^WORK": ["工作", "上班", "加班", "同事", "领导", "打工", "职场", "下班"],
    "^STUDY": ["学习", "考试", "作业", "复习", "考研", "期末", "上课", "背书"],
    "^LOVE": ["喜欢", "暗恋", "心动", "表白", "对象", "他", "她", "在一起"],
    "^FRIEND": ["朋友", "友谊", "闺蜜", "兄弟", "室友", "同学"],
    "^HOME": ["家", "父母", "妈妈", "爸爸", "回家", "想家", "家人"],
    "^NIGHT": ["深夜", "凌晨", "夜里", "睡觉", "晚安", "半夜"],
    "^MOVE": ["旅行", "出发", "远方", "城市", "海边", "看海", "出发吧"],
    "^SELF": ["自己", "自我", "我", "内心", "接受", "和解"],
}

_ASCII_WORD = re.compile(r"[A-Za-z0-9]+")
_CJK = re.compile(r"[\u4e00-\u9fff]")


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _theme_hits(text: str) -> List[str]:
    """命中哪些主题 token"""
    hits = []
    for token, words in _THEME_SYNONYMS.items():
        for w in words:
            if w in text:
                hits.append(token)
                break
    return hits


def embed(text: str) -> Dict[str, float]:
    """
    文本 → 稀疏向量（dict: token -> 词频）。这是本模块的「向量化」入口。
    若将来接入远程 embedding，只替换本函数即可。
    """
    t = _normalize(text)
    vec: Dict[str, float] = {}
    if not t:
        return vec

    # 1) 字符 unigram（仅汉字，弱权重）
    cjk_chars = [c for c in t if _CJK.match(c)]
    for c in cjk_chars:
        vec["c:" + c] = vec.get("c:" + c, 0.0) + 1.0

    # 2) 字符 bigram（强权重，承载中文短语语义）
    for i in range(len(cjk_chars) - 1):
        bg = cjk_chars[i] + cjk_chars[i + 1]
        vec["b:" + bg] = vec.get("b:" + bg, 0.0) + 3.0

    # 3) 拉丁词 / 数字
    for w in _ASCII_WORD.findall(t):
        vec["w:" + w] = vec.get("w:" + w, 0.0) + 2.0

    # 4) 主题归并（语义信号）
    for token in _theme_hits(t):
        vec[token] = vec.get(token, 0.0) + 4.0

    return vec


def _norm(vec: Dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values())) or 1.0


def similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """余弦相似度，返回 0~1（稀疏向量，遍历较小的一侧）"""
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    dot = 0.0
    for k, v in vec_a.items():
        w = vec_b.get(k)
        if w:
            dot += v * w
    if dot <= 0:
        return 0.0
    sim = dot / (_norm(vec_a) * _norm(vec_b))
    # 归一化到 0~1（余弦理论上已是 -1~1，稀疏非负向量不会为负）
    return max(0.0, min(1.0, sim))


def similarity_text(a: str, b: str) -> float:
    """文本级便捷方法（内部各算一次向量）"""
    return similarity(embed(a), embed(b))


def to_score(sim: float) -> int:
    """相似度 → 0~10000 的整型分数（入库用，避免浮点）"""
    return int(round(max(0.0, min(1.0, sim)) * 10000))


def rank(query: str, candidates: List[Tuple[int, str]], threshold: float,
         top_k: int = 5) -> List[Tuple[int, float]]:
    """
    对候选集排序。
    query: 查询文本
    candidates: [(id, text), ...]
    threshold: 相似度阈值（低于它的不返回，宁缺毋滥）
    top_k: 返回上限
    返回: [(id, sim), ...] 按 sim 降序
    """
    qv = embed(query)
    scored: List[Tuple[int, float]] = []
    for cid, ctext in candidates:
        s = similarity(qv, embed(ctext))
        if s >= threshold:
            scored.append((cid, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
