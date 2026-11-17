# -*- coding: utf-8 -*-
"""
长效记忆服务 —— 陪伴感增强 v3

三条设计原则：
1. 分层：profile(长期固定信息) / event(对话事件) / preference(偏好)
2. 绑定角色：记忆带 role_key，A 角色记住的内容不会串到 B 角色；role_key='' 为共享记忆
3. 可治理：用户可查看、单条删除、一键清空（软删除，保留审计）

记忆不是摘抄存档：recall() 按「相关性 + 重要度 + 新鲜度」打分召回，
build_prompt_block() 明确要求模型自然提起、禁止复读罗列、禁止追问已知信息。
"""
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.chat import AIUserMemory

# ---------------- 分层定义 ----------------
LAYER_PROFILE = "profile"        # 长期固定信息：喜好/肤质/忌口/作息/目标/重要日期/MBTI/烦心事
LAYER_EVENT = "event"            # 对话事件：聊过的故事/情绪节点/约定/秘密
LAYER_PREFERENCE = "preference"  # 偏好：饮品口味/讨厌的话术/喜欢的互动方式

LAYER_LABELS = {
    LAYER_PROFILE: "长期信息",
    LAYER_EVENT: "共同经历",
    LAYER_PREFERENCE: "偏好习惯",
}
LAYER_ICONS = {
    LAYER_PROFILE: "📌",
    LAYER_EVENT: "🫧",
    LAYER_PREFERENCE: "💫",
}
VALID_LAYERS = (LAYER_PROFILE, LAYER_EVENT, LAYER_PREFERENCE)

# 各层召回上限（控制 prompt 体积）
LAYER_LIMITS = {LAYER_PROFILE: 12, LAYER_EVENT: 8, LAYER_PREFERENCE: 8}


def normalize_layer(layer: str) -> str:
    layer = (layer or "").strip().lower()
    return layer if layer in VALID_LAYERS else LAYER_EVENT


# ============================================================
# 规则抽取：高信号句式直接命中，零延迟、不依赖大模型
# 这是「已经告诉过你的，不许再问一遍」的基本盘
# ============================================================
# (正则, 分层, 标题, 重要度, 取值分组)
RULE_PATTERNS = [
    # --- 长期固定信息 ---
    (r"(?:我叫|我的名字是|我的名字叫|你可以叫我|叫我)\s*([^\s，。,.!！?？]{1,12})",
     LAYER_PROFILE, "称呼", 9, 1),
    (r"\b(I{0,1}N{0,1}T{0,1}F{0,1}J{0,1}P{0,1}E{0,1}S{0,1})\b", None, None, 0, 0),  # 占位，下面单独处理
    (r"(?:我(?:的)?(?:皮肤|肤质)(?:是|属于|比较|偏)?)([^\s，。,.!！?？]{1,15})",
     LAYER_PROFILE, "肤质", 6, 1),
    (r"(?:我对|我吃)\s*([^\s，。,.!！?？]{1,10})\s*过敏", LAYER_PROFILE, "过敏源", 9, 1),
    (r"(?:我不吃|我忌口|忌口是|我不喝)\s*([^\s，。,.!！?？]{1,20})", LAYER_PROFILE, "忌口", 8, 1),
    (r"我(?:一般|通常|习惯|基本)?(?:都是)?(?:在)?\s*(\d{1,2})\s*点(?:左右)?(?:才)?睡",
     LAYER_PROFILE, "作息", 6, 1),
    (r"我(?:一般|通常|习惯|基本)?(?:都是)?(?:在)?\s*(\d{1,2})\s*点(?:左右)?起",
     LAYER_PROFILE, "作息", 6, 1),
    (r"(?:我的目标|我想做到|我想坚持|我的计划是|我打算)\s*([^\n，。,.!！?？]{1,40})",
     LAYER_PROFILE, "目标", 7, 1),
    (r"(?:让我)?(?:最|很|挺|特别)?(?:烦|纠结|难受|焦虑|在意)的(?:是|一件事)?\s*([^\n。.!！?？]{1,40})",
     LAYER_PROFILE, "在意的事", 8, 1),
    (r"(?:我(?:的)?(?:生日|纪念日|考试|面试|婚礼|答辩|搬家)[^0-9]{0,6})"
     r"(\d{1,2}\s*月\s*\d{1,2}\s*[日号]?|\d{1,2}\s*[-/]\s*\d{1,2})",
     LAYER_PROFILE, "重要日期", 9, 1),

    # --- 偏好 ---
    (r"(?:我喜欢|我爱|我超爱|我偏好|我一般喝|我只喝)\s*([^\n，。,.!！?？]{1,24})",
     LAYER_PREFERENCE, "喜欢", 6, 1),
    (r"(?:我不(?:太)?喜欢|我讨厌|我烦|我受不了|别跟我提)\s*([^\n，。,.!！?？]{1,24})",
     LAYER_PREFERENCE, "讨厌", 7, 1),
    (r"(?:不要(?:跟我|对)?说|别(?:跟我)?说|别用)\s*([^\n，。,.!！?？]{1,24})",
     LAYER_PREFERENCE, "讨厌的话术", 8, 1),
    (r"我(?:更)?喜欢你(?:跟我)?([^\n，。,.!！?？]{1,24})", LAYER_PREFERENCE, "喜欢的互动方式", 7, 1),

    # --- 对话事件 ---
    (r"(?:我们?约(?:好|定)了?|约定|说好了?|下次一起)\s*([^\n。.!！?？]{1,40})",
     LAYER_EVENT, "约定", 9, 1),
    (r"(?:记住|记一下|帮我记着|别忘了)\s*([^\n。.!！?？]{1,50})", LAYER_EVENT, "叮嘱", 9, 1),
    (r"(?:告诉你(?:一个)?秘密|我跟你(?:说|讲)个秘密|其实我)\s*([^\n。.!！?？]{1,50})",
     LAYER_EVENT, "秘密", 9, 1),

    # --- 职业 / 近况（"TA 记得我是干嘛的"是最直观的记忆力） ---
    # 允许两种说法：「我是/我是一名…设计师」和「我做平面设计的」
    (r"(?:我是|我是一名|我是一个|我的职业是|我做|我在做|我干|我从事)\s*"
     r"([^\s，。,.!！?？、]{2,16}?(?:师|员|生|工|老板|主播|博主|店主|司机|会计|律师|运营|策划|编辑|助理|顾问|经理|设计|开发|编程|摄影|写作|翻译|销售|客服))",
     LAYER_PROFILE, "职业", 8, 1),
    (r"(?:我(?:最近|这阵子|这几天|这两天)|最近我)\s*(?:在|正|得)?\s*([^\n。.!！?？]{2,30})",
     LAYER_EVENT, "近况", 7, 1),
]

MBTI_RE = re.compile(
    r"(?:我是|我的(?:性格|类型)是|mbti是)?\s*"
    r"(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)",
    re.IGNORECASE)

STOPWORDS = set("今天昨天前天明天这个那个什么怎么可以就是自己我们你们他们因为所以如果不过还是真的有点非常特别".strip())


def _tokenize(text: str) -> set:
    """极简中文分词：取 2-gram；英文取单词。够用且零依赖。"""
    if not text:
        return set()
    tokens = set()
    for w in re.findall(r"[a-zA-Z]{2,}", text.lower()):
        tokens.add(w)
    zh = re.sub(r"[^一-龥]", " ", text)
    for seg in zh.split():
        for i in range(len(seg) - 1):
            tokens.add(seg[i:i + 2])
        if len(seg) == 1:
            tokens.add(seg)
    return {t for t in tokens if t not in STOPWORDS}


class MemoryService:
    """长效记忆：写入 / 召回 / 组装 prompt / 治理"""

    # ---------------- 基础查询 ----------------
    @staticmethod
    def _base_query(db: Session, user_id: int, role_key: str = ""):
        """角色隔离：只取该角色的记忆 + 共享记忆(role_key='')"""
        q = db.query(AIUserMemory).filter(
            AIUserMemory.user_id == user_id,
            AIUserMemory.is_deleted == 0,
        )
        if role_key:
            q = q.filter(
                (AIUserMemory.role_key == role_key) | (AIUserMemory.role_key == "")
            )
        return q

    # ---------------- 写入 ----------------
    @staticmethod
    def add_memory(db: Session, user_id: int, content: str, layer: str = LAYER_EVENT,
                   role_key: str = "", role_id: int = 0, title: str = "",
                   salience: int = 5, source: str = "auto", memory_type: str = "chat",
                   emotion_score: int = 5, is_long_term: bool = False,
                   context_data: Optional[Dict] = None) -> Optional[AIUserMemory]:
        """写入一条记忆；内容与同层已有记忆重复则跳过（返回 None）"""
        content = (content or "").strip()
        if not content or len(content) > 500:
            return None
        layer = normalize_layer(layer)

        # 去重：同用户同角色同层下，完全一样或互为子串的内容不重复存
        exists = MemoryService._base_query(db, user_id, role_key).filter(
            AIUserMemory.memory_layer == layer
        ).order_by(AIUserMemory.id.desc()).limit(60).all()
        for m in exists:
            old = (m.memory_content or "").strip()
            if old == content or content in old or (len(content) > 8 and old in content):
                # 更新重要度（只升不降），不新增行
                if salience > (m.salience or 0):
                    m.salience = min(10, salience)
                    m.updated_at = datetime.now()
                    db.commit()
                return None

        mem = AIUserMemory(
            user_id=user_id,
            memory_type=memory_type,
            memory_layer=layer,
            role_key=role_key or "",
            role_id=role_id or 0,
            memory_content=content[:500],
            title=(title or "")[:64],
            salience=max(1, min(10, int(salience or 5))),
            source=source,
            emotion_score=emotion_score,
            is_long_term=1 if (is_long_term or layer == LAYER_PROFILE) else 0,
            context_data=context_data,
            is_deleted=0,
            updated_at=datetime.now(),
        )
        db.add(mem)
        db.commit()
        return mem

    # ---------------- 规则抽取 ----------------
    @staticmethod
    def extract_by_rules(db: Session, user_id: int, role_key: str, text: str,
                         role_id: int = 0) -> int:
        """从用户这句话里抽取高信号记忆，返回新增条数"""
        if not text:
            return 0
        saved = 0

        m = MBTI_RE.search(text)
        if m:
            val = m.group(1).upper()
            if MemoryService.add_memory(db, user_id, f"用户的 MBTI 是 {val}",
                                        layer=LAYER_PROFILE, role_key=role_key,
                                        role_id=role_id, title="MBTI", salience=8,
                                        source="rule"):
                saved += 1

        for pattern, layer, title, salience, group in RULE_PATTERNS:
            if layer is None:      # 占位规则，跳过
                continue
            for mm in re.finditer(pattern, text):
                try:
                    val = mm.group(group).strip()
                except (IndexError, AttributeError):
                    continue
                if not val:
                    continue
                if title == "作息":
                    content = (f"用户通常 {val} 点"
                               + ("睡" if "睡" in mm.group(0) else "起"))
                elif title == "重要日期":
                    kind = "重要日期"
                    for k in ("生日", "纪念日", "考试", "面试", "婚礼", "答辩", "搬家"):
                        if k in mm.group(0):
                            kind = k
                            break
                    content = f"用户的{kind}是 {val}"
                elif title == "职业":
                    # 「做平面设计的」→ 平面设计
                    content = f"用户的工作是 {val.rstrip('的')}"
                elif title == "近况":
                    content = f"用户最近{val}"
                else:
                    content = f"用户{title}：{val}"
                if MemoryService.add_memory(db, user_id, content, layer=layer,
                                            role_key=role_key, role_id=role_id,
                                            title=title, salience=salience,
                                            source="rule"):
                    saved += 1
        return saved

    # ---------------- 大模型抽取 ----------------
    EXTRACT_PROMPT = """你是记忆抽取器。从下面这段对话里，抽取值得长期记住的信息。

只抽这三类：
- profile：用户的长期固定信息（身份/称呼/职业/肤质/忌口/作息/目标/重要日期/MBTI/在意的烦心事）
- event：你们之间发生过的具体事（聊过的故事、情绪节点、约定、秘密）
- preference：用户的偏好（口味、讨厌的话术、喜欢的互动方式）

规则：
1. 只抽用户明确表达过的，不要脑补、不要推断。
2. 每条 content 写成一句完整的第三人称陈述，20-60 字，能脱离上下文独立理解。
3. 没值得记的就返回空数组 []。
4. 最多 4 条，按重要度排序。
5. 只返回 JSON 数组，不要任何解释，不要 markdown 代码块。
6. 信息不完整就不要写（例如只有「最近」没有具体日期，就不要写「重要日期」；
   用户没说清楚职业就不要猜）。宁可少写一条，也不要写一条含糊又占位的记忆。

输出格式：[{"layer":"profile","title":"称呼","content":"用户让大家叫她小青","salience":9}]

对话：
{dialogue}
"""

    @staticmethod
    async def extract_by_llm(db: Session, user_id: int, role_key: str,
                             messages: List[Dict], role_id: int = 0,
                             max_items: int = 4) -> int:
        """用大模型抽取记忆（非流式）。失败时静默降级为不抽取，绝不影响对话。"""
        from app.services.ai_service import AIService

        dialogue = "\n".join(
            f"{'用户' if m.get('role') == 'user' else 'AI'}：{m.get('content', '')[:200]}"
            for m in messages[-6:]
        )
        if not dialogue.strip():
            return 0

        try:
            # 注意：这里绝对不能用 .format() —— EXTRACT_PROMPT 里的 JSON 示例自带 {"layer":...}
            # 花括号，.format 会把它当成占位符并抛 KeyError，导致 LLM 抽取 100% 静默失败。
            sys_prompt = MemoryService.EXTRACT_PROMPT.replace("{dialogue}", dialogue[:2000])
            raw = await AIService.chat_non_stream([
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "请抽取。"},
            ])
        except Exception as e:
            print(f"[memory][WARN] LLM 抽取失败，跳过: {type(e).__name__}: {e}")
            return 0

        items = MemoryService._parse_json_array(raw)
        saved = 0
        for it in items[:max_items]:
            if not isinstance(it, dict):
                continue
            layer = normalize_layer(it.get("layer", ""))
            content = str(it.get("content", "")).strip()
            if not content or len(content) > 200:
                continue
            try:
                sal = int(it.get("salience", 6))
            except (TypeError, ValueError):
                sal = 6
            if MemoryService.add_memory(db, user_id, content, layer=layer,
                                        role_key=role_key, role_id=role_id,
                                        title=str(it.get("title", ""))[:32] or LAYER_LABELS[layer],
                                        salience=sal, source="auto"):
                saved += 1
        return saved

    @staticmethod
    def _parse_json_array(raw: str) -> list:
        """从大模型输出里抠出 JSON 数组（允许被 ```json 包裹或带前后废话）"""
        if not raw:
            return []
        s = raw.strip()
        s = re.sub(r"^```(?:json)?", "", s).strip()
        s = re.sub(r"```$", "", s).strip()
        start, end = s.find("["), s.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            data = json.loads(s[start:end + 1])
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    # ---------------- 召回 ----------------
    @staticmethod
    def recall(db: Session, user_id: int, role_key: str = "", query: str = "",
               layer: str = "", limit: int = 20, days: int = 180) -> List[AIUserMemory]:
        """相关性召回：关键词重叠 * 2 + 重要度/2 + 新鲜度加分"""
        q = MemoryService._base_query(db, user_id, role_key)
        if layer:
            q = q.filter(AIUserMemory.memory_layer == layer)
        since = datetime.now() - timedelta(days=days)
        rows = q.filter(AIUserMemory.created_at >= since).all()

        q_tokens = _tokenize(query)
        now = datetime.now()
        scored = []
        for m in rows:
            score = (m.salience or 5) / 2.0
            if q_tokens:
                overlap = len(q_tokens & _tokenize(m.memory_content or ""))
                score += overlap * 2.0
                if m.title and m.title in query:
                    score += 3.0
            age = (now - (m.created_at or now)).days
            if age <= 3:
                score += 3.0
            elif age <= 14:
                score += 1.5
            elif age <= 45:
                score += 0.5
            scored.append((score, m))

        scored.sort(key=lambda x: (-x[0], -(x[1].salience or 0), -(x[1].id or 0)))
        return [m for _, m in scored[:limit]]

    # ---------------- 组装 prompt ----------------
    @staticmethod
    def build_prompt_block(db: Session, user_id: int, role_key: str = "",
                           query: str = "") -> str:
        """把记忆拼成可注入 system prompt 的片段（无记忆时返回空串，保持原 prompt 不变）"""
        parts = []
        total = 0
        for layer in (LAYER_PROFILE, LAYER_PREFERENCE, LAYER_EVENT):
            rows = MemoryService.recall(db, user_id, role_key, query,
                                        layer=layer, limit=LAYER_LIMITS[layer])
            if not rows:
                continue
            lines = "\n".join(f"- {m.memory_content}" for m in rows)
            parts.append(f"【{LAYER_LABELS[layer]}】\n{lines}")
            total += len(rows)

        if not parts:
            return ""

        return (
            "以下是你和用户之间真实积累下来的记忆（{total} 条）。\n"
            "{body}\n"
            "使用要求：\n"
            "1. 这些是你亲身经历、亲耳听来的事，不是外部资料。\n"
            "2. 可以在合适的时机自然提起（比如「你上次说的那个…」），让对话有连续性；"
            "但不要生硬罗列、不要原样复读、不要每句都带「我记得你说过」。\n"
            "3. 上面对话中已经明确记录过的信息，禁止再向用户追问一遍。\n"
            "4. 如果用户现在说的话和某条记忆冲突，以用户现在说的为准，并自然更新你的理解。\n"
        ).format(total=total, body="\n\n".join(parts))

    # ---------------- 治理：列表 / 删除 / 清空 ----------------
    @staticmethod
    def list_memories(db: Session, user_id: int, role_key: str = "", layer: str = "",
                      page: int = 1, page_size: int = 50) -> Tuple[List[AIUserMemory], int]:
        q = MemoryService._base_query(db, user_id, role_key)
        if layer:
            q = q.filter(AIUserMemory.memory_layer == layer)
        total = q.count()
        rows = q.order_by(
            AIUserMemory.salience.desc(), AIUserMemory.id.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        return rows, total

    @staticmethod
    def delete_memory(db: Session, user_id: int, memory_id: int) -> bool:
        """单条软删除（只允许删自己的）"""
        m = db.query(AIUserMemory).filter(
            AIUserMemory.id == memory_id,
            AIUserMemory.user_id == user_id,
            AIUserMemory.is_deleted == 0,
        ).first()
        if not m:
            return False
        m.is_deleted = 1
        m.updated_at = datetime.now()
        db.commit()
        return True

    @staticmethod
    def update_memory(db: Session, user_id: int, memory_id: int,
                      content: str = "", title: str = "",
                      layer: str = "", salience: Optional[int] = None) -> bool:
        m = db.query(AIUserMemory).filter(
            AIUserMemory.id == memory_id,
            AIUserMemory.user_id == user_id,
            AIUserMemory.is_deleted == 0,
        ).first()
        if not m:
            return False
        if content:
            m.memory_content = content[:500]
        if title:
            m.title = title[:64]
        if layer:
            m.memory_layer = normalize_layer(layer)
        if salience is not None:
            m.salience = max(1, min(10, int(salience)))
        m.updated_at = datetime.now()
        db.commit()
        return True

    @staticmethod
    def clear_memories(db: Session, user_id: int, role_key: str = "") -> int:
        """一键清空。role_key 为空且 all_roles=True 时清空该用户全部记忆"""
        q = db.query(AIUserMemory).filter(
            AIUserMemory.user_id == user_id,
            AIUserMemory.is_deleted == 0,
        )
        if role_key:
            q = q.filter(AIUserMemory.role_key == role_key)
        rows = q.all()
        now = datetime.now()
        for m in rows:
            m.is_deleted = 1
            m.updated_at = now
        db.commit()
        return len(rows)

    @staticmethod
    def stats(db: Session, user_id: int, role_key: str = "") -> Dict:
        q = MemoryService._base_query(db, user_id, role_key)
        by_layer = {}
        for layer in VALID_LAYERS:
            by_layer[layer] = q.filter(AIUserMemory.memory_layer == layer).count()
        return {"total": q.count(), "by_layer": by_layer}


def to_dict(m: AIUserMemory) -> Dict:
    """统一输出结构（前端列表/管理页直接用）"""
    created = m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else ""
    return {
        "id": m.id,
        "layer": m.memory_layer,
        "layerLabel": LAYER_LABELS.get(m.memory_layer, "记忆"),
        "layerIcon": LAYER_ICONS.get(m.memory_layer, "•"),
        "title": m.title or LAYER_LABELS.get(m.memory_layer, "记忆"),
        "content": m.memory_content,
        "salience": m.salience or 5,
        "source": m.source,
        "roleKey": m.role_key or "",
        "shared": not (m.role_key or ""),
        "createdAt": created,
    }
