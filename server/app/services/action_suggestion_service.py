# -*- coding: utf-8 -*-
"""
行动建议服务 —— 根据用户这句话，推荐 App 内可以立刻去做的事

设计原则：
1. 纯规则、不查库、不调大模型，异常时一律返回空列表（原有对话行为完全不变）
2. 只做「推荐入口」，不替用户执行、不写入任何数据
3. 用户明确说「不用安慰 / 别给建议」时不推荐；危机情绪不推荐（前端已有危机/情绪引导弹窗）
4. 同一会话内同一建议有冷却时间，避免每条消息都在推销功能
"""
import re
import time
from typing import Dict, List, Optional

from app.services.emotion_service import EmotionService


# 功能清单：key -> {label, desc, icon, route, keywords}
# route 均为 pages.json 中已存在、可直接 navigateTo 的页面
SUGGESTION_CATALOG = {
    "meditation": {
        "label": "正念呼吸 3 分钟",
        "desc": "把呼吸放慢，先让心静下来",
        "icon": "🧘",
        "route": "/pages/meditation/meditation",
        "keywords": [
            "焦虑", "压力", "心烦", "烦躁", "心慌", "睡不着", "失眠", "喘不过气",
            "崩溃", "冷静", "深呼吸", "冥想", "正念", "放松", "紧绷", "emo",
        ],
    },
    "emotion": {
        "label": "写进情绪树洞",
        "desc": "把此刻的心情写下来，理一理",
        "icon": "📖",
        "route": "/pages/emotion/emotion",
        "keywords": [
            "难过", "委屈", "失落", "孤独", "想哭", "不开心", "郁闷", "心事",
            "难受", "心里堵", "憋", "日记", "记录心情", "写下来",
        ],
    },
    "focus": {
        "label": "一起专注 25 分钟",
        "desc": "我陪你开一轮专注，先做一点点",
        "icon": "⏳",
        "route": "/pages/focus/focus-home",
        "keywords": [
            "拖延", "学不进去", "静不下心", "分心", "效率", "复习", "写作业",
            "赶due", "做不完", "专注",
        ],
    },
    "walk": {
        "label": "出去走走",
        "desc": "去环球行走散散步，换口气",
        "icon": "🌍",
        "route": "/pages/walk/walk",
        "keywords": ["无聊", "闷", "想出去", "散步", "走走", "透透气", "没意思"],
    },
    "schedule": {
        "label": "理一下明天的安排",
        "desc": "把要做的事记下来，心里会踏实些",
        "icon": "🗓️",
        "route": "/pages/schedule/schedule",
        "keywords": ["明天", "安排", "计划", "日程", "待办", "来不及", "忘了", "事情太多", "忙不过来"],
    },
}

# 情绪 -> 功能加权（只在情绪为负面/疲惫时才生效）
EMOTION_BOOST = {
    "sad": {"emotion": 4, "meditation": 1},
    "tired": {"meditation": 3, "emotion": 1},
    "angry": {"meditation": 3, "emotion": 2},
    "calm": {"walk": 1},
}

# 命中一个关键词的分数（阈值=2，即至少要有一个明确信号）
KEYWORD_SCORE = 2
# 同一会话里同一建议的冷却时间（秒）
COOLDOWN_SECONDS = 20 * 60
MAX_ITEMS = 1

# 用户明确拒绝「建议」本身的说法（EmotionService 只管「别安慰」，不管「别建议」）
# 用正则覆盖「别/不用/不要…（最多4个字）…建议/推荐」这类变体
REJECT_SUGGESTION_PATTERN = re.compile(
    r"(别|不要|不用|不需要|无需)[^，。！？,!?]{0,4}(建议|推荐)|不用你教|别教我"
)


class ActionSuggestionService:
    """行动建议：规则打分 + prompt 片段生成"""

    # (session_id, 建议 key) -> 上次推荐时间戳
    _recent: Dict[tuple, float] = {}

    @staticmethod
    def _is_rejected(text: str, emotion_result: Optional[Dict]) -> bool:
        """用户明确拒绝建议时不推荐

        注意：这里不把「强烈负面情绪」当危机处理 —— 真正的高危/危机
        由 chat.py 的 CrisisService / danger 闸门拦截（crisis_level=critical 时调用方不会调用这里）。
        """
        if not text:
            return True
        if EmotionService.is_rejecting_comfort(text):
            return True
        lowered = text.lower()
        if REJECT_SUGGESTION_PATTERN.search(lowered):
            return True
        return False

    @classmethod
    def suggest(cls, text: str, emotion_result: Optional[Dict] = None,
                session_key: int = 0) -> List[Dict]:
        """返回最多 MAX_ITEMS 条建议；无明确信号时返回空列表

        session_key：会话 id（用于冷却，避免同一会话反复推销同一功能）
        """
        if cls._is_rejected(text, emotion_result):
            return []

        content = (text or "").strip()[:300]
        if not content:
            return []

        scores: Dict[str, int] = {}
        matched_kw: Dict[str, str] = {}

        # 1) 关键词命中
        for key, item in SUGGESTION_CATALOG.items():
            for kw in item["keywords"]:
                if kw and kw in content:
                    scores[key] = scores.get(key, 0) + KEYWORD_SCORE
                    matched_kw.setdefault(key, kw)

        # 2) 情绪加权
        emotion = (emotion_result or {}).get("emotion", "")
        for key, boost in EMOTION_BOOST.get(emotion, {}).items():
            scores[key] = scores.get(key, 0) + boost

        if not scores:
            return []

        # 3) 排序：分数高优先，同分按清单顺序
        order = list(SUGGESTION_CATALOG.keys())
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], order.index(kv[0])))

        now = time.time()
        items: List[Dict] = []
        for key, score in ranked:
            if score < KEYWORD_SCORE:
                continue
            cache_key = (session_key, key)
            last = cls._recent.get(cache_key, 0)
            if now - last < COOLDOWN_SECONDS:
                continue

            meta = SUGGESTION_CATALOG[key]
            items.append({
                "key": key,
                "label": meta["label"],
                "desc": meta["desc"],
                "icon": meta["icon"],
                "route": meta["route"],
                "keyword": matched_kw.get(key, ""),
            })
            cls._remember(cache_key, now)
            if len(items) >= MAX_ITEMS:
                break

        return items

    @classmethod
    def _remember(cls, cache_key: tuple, ts: float):
        """记录推荐时间；顺手清理过期缓存，避免长期运行内存增长"""
        cls._recent[cache_key] = ts
        if len(cls._recent) > 500:
            expire = ts - COOLDOWN_SECONDS * 2
            cls._recent = {k: v for k, v in cls._recent.items() if v >= expire}

    @staticmethod
    def build_prompt_block(items: List[Dict]) -> str:
        """生成注入 system prompt 的「可推荐功能 + 建议规则」片段

        始终附带功能清单（让所有角色都知道 App 里有什么可做），
        命中具体建议时额外给出本轮倾向，保证 AI 的话术与前端卡片一致。
        """
        lines = [
            "【可以邀请用户去做的事】（App 内真实功能，用户看不到这份清单）",
            "- 正念呼吸：3 分钟呼吸练习",
            "- 情绪树洞：写下此刻的心情",
            "- 一起专注：25 分钟专注一轮",
            "- 环球行走：陪她散步、解锁新地点",
            "- 日程：把要做的事记下来",
            "【建议规则】",
            "1. 只有用户正被情绪或状态困住（难受、焦虑、拖延、迷茫、无聊）时，"
            "才在回复最后顺口邀请 TA 去做其中一件，一句话即可。",
            "2. 用户正常聊天、提问、分享开心的事时，不要推荐任何功能。",
            "3. 不要列清单，不要用『我建议你使用XX功能』这种说明文口气，像朋友随口一提。",
            "4. 用户说『不用安慰』『别给建议』时，绝对不要再推荐。",
        ]
        if items:
            it = items[0]
            kw = it.get("keyword") or ""
            reason = f"用户刚提到『{kw}』，" if kw else ""
            lines.append(
                f"【本轮建议】{reason}比较适合邀请 TA 去「{it['label']}」"
                f"（{it['desc']}）。如果契合，就在最后一句轻轻提一下，不契合就不要提。"
            )
        return "\n".join(lines)
