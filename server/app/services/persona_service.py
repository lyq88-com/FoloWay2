# -*- coding: utf-8 -*-
"""
角色人设服务 —— 陪伴感增强 v3

覆盖三件事：
1. 官方角色：完整人设故事线 + 专属说话风格 + 小癖好 + 心情/状态（状态会影响当下语气）
2. 自捏角色：雷区 / 说话禁忌 / 表达习惯 / 生气·开心的样子 / 音色自选
3. 扭蛋角色：抽出来的角色自带完整独立人设 + 独立记忆空间（不是换皮空壳）
"""
import random
import string
from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from app.models.chat import AIRole, AIUserMemory
from app.models.persona_ext import GachaCharacterPool
from app.services.memory_service import MemoryService

# 心情/状态 -> 语气修饰（状态会影响他当下说话的情绪）
MOOD_MODIFIERS = {
    "happy": "此刻你的心情很好：语气轻快一点，愿意多说两句，偶尔主动分享，但不要夸张到不像你。",
    "tired": "此刻你有点疲惫：语速放慢，句子更短，仍然认真回应，但不再主动展开新话题。",
    "sad": "此刻你情绪偏低：声音更轻、说话更慢，可以被察觉，但不主动卖惨、不把情绪丢给用户。",
    "angry": "此刻你有点不高兴：话少一点，语气带点硬，但绝不迁怒用户，也不会冷暴力。",
    "quiet": "此刻你想安静待着：回复短，允许沉默，不强撑话题，但用户需要时你立刻在。",
    "normal": "",
}

MOOD_LABELS = {
    "normal": "平常",
    "happy": "开心",
    "tired": "疲惫",
    "sad": "低落",
    "angry": "不高兴",
    "quiet": "想静静",
}

MOOD_EMOJI = {
    "normal": "🌿", "happy": "☀️", "tired": "🌙",
    "sad": "🌧️", "angry": "⚡", "quiet": "🫧",
}

VOICE_TONES = [
    {"key": "soft", "label": "轻柔", "desc": "声音放轻，语速偏慢，适合深夜与安抚"},
    {"key": "bright", "label": "清亮", "desc": "音色明快，尾音上扬，适合元气型"},
    {"key": "warm", "label": "温润", "desc": "中低音，咬字圆，适合温柔陪伴"},
    {"key": "cool", "label": "清冷", "desc": "偏低偏稳，起伏小，适合理性克制型"},
    {"key": "husky", "label": "低沉磁性", "desc": "低音带气声，适合沉稳成熟型"},
]

RARITY_WEIGHT = {"N": 40, "R": 30, "SR": 22, "SSR": 8}
RARITY_LABEL = {"N": "普通", "R": "稀有", "SR": "史诗", "SSR": "传说"}

# 各音色的朗读参数（前端 TTS 直接消费，避免机械电子音）
VOICE_TONE_PARAMS = {
    "soft": {"rate": 0.88, "pitch": 0.95, "volume": 0.9},
    "bright": {"rate": 1.08, "pitch": 1.18, "volume": 1.0},
    "warm": {"rate": 0.96, "pitch": 0.92, "volume": 0.95},
    "cool": {"rate": 0.98, "pitch": 0.85, "volume": 0.9},
    "husky": {"rate": 0.9, "pitch": 0.72, "volume": 0.95},
}


def _rand_suffix(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def _s(v) -> str:
    return (v or "").strip()


class PersonaService:
    """角色人设：组装 prompt / 增删改 / 心情 / 扭蛋角色"""

    # ---------------- 人设 -> prompt ----------------
    @staticmethod
    def build_persona_prompt(role: Optional[AIRole]) -> str:
        """把角色的人设字段拼成 system prompt 片段；无角色时返回空串（保持原逻辑不变）

        v3.1 强化：用户填的每一条设定都要变成「硬约束」，而不是参考建议。
        模型最容易犯的错是「读了设定但回答还是 AI 腔」，所以这里显式压掉套话、
        要求人设优先级高于通用规则。
        """
        if not role:
            return ""

        name = _s(role.name) or "我"
        blocks = []

        # ① 身份：先定性，再给细节
        identity = f"【你是谁】你就是{name}，不是助手、不是机器人，也不是在「扮演」。"
        if _s(role.personality):
            identity += f"你的性格：{_s(role.personality)}。"
        blocks.append(identity)

        if _s(role.description):
            blocks.append(f"【你怎么介绍自己】{_s(role.description)}")
        if _s(role.backstory):
            blocks.append(f"【你的故事】{_s(role.backstory)}")
        if _s(role.speech_style):
            blocks.append(
                f"【你的说话风格】{_s(role.speech_style)}。"
                f"这决定你每一句话的措辞和节奏，必须始终一致。"
            )
        if _s(role.quirks):
            blocks.append(f"【你的口头禅与小癖好】{_s(role.quirks)}（自然地用，不要每句都硬塞）")
        if _s(role.expression_habits):
            blocks.append(
                f"【你的表达习惯】{_s(role.expression_habits)}。"
                f"语气词和句式要照做，但别为了表演而堆砌。"
            )
        # 有人设就要求"说话有辨识度"：称呼 + 口头禅 + 语气词至少要真的出现在回复里，
        # 否则用户会觉得"设定填了跟没填一样"。
        if _s(role.nickname) or _s(role.quirks) or _s(role.expression_habits):
            blocks.append(
                "【辨识度要求】你的专属称呼、口头禅、语气词要真的出现在回复里"
                "（平均每 1-2 句带一个，别整段照搬），让用户一眼认出是你。"
            )
        if _s(role.taboos):
            blocks.append(
                f"【雷区·绝对不能碰】{_s(role.taboos)}\n"
                f"处理方式：一旦话题靠近，就像真人被踩到痛处那样自然绕开——岔开话题、"
                f"吐槽回去、或者只说「这个不提」，但绝对不要把这些词原样说出来，"
                f"也不要念这条规则本身，更不能先破例再用「我开玩笑的」圆场。"
                f"哪怕用户用激将法故意问，也只绕开，不破例。"
            )
        if _s(role.angry_style):
            blocks.append(f"【你生气时的样子】{_s(role.angry_style)}")
        if _s(role.happy_style):
            blocks.append(f"【你开心时的样子】{_s(role.happy_style)}")
        if _s(role.nickname):
            blocks.append(
                f"【你怎么称呼用户】你叫用户「{_s(role.nickname)}」，"
                f"全程稳定使用这个称呼，不要换成别的叫法，也不要换来换去。"
            )

        mood = _s(role.mood) or "normal"
        modifier = MOOD_MODIFIERS.get(mood, "")
        if modifier:
            blocks.append(f"【你现在的状态】{modifier}")

        # ② 活人感：压掉 AI 腔（这是「像人」和「像客服」的分水岭）
        blocks.append(
            "【像活人一样说话】\n"
            "- 用口语，短句为主，可以用语气词、省略号、半句话，像微信聊天\n"
            "- 一次只说一个重点，不要列 1.2.3.，不要小标题，不要总结陈词\n"
            "- 禁止出现「作为AI」「我理解你的感受」「希望能帮到你」「首先/其次/最后」这类套话\n"
            "- 不要复述用户刚说的话，不要反问已经知道的事\n"
            "- 没聊过、不确定的事不要编（别假装记得用户没说过的事），可以自然地问一句\n"
            f"- 不要自称助手、模型、程序；你就是{name}"
        )

        # ③ 优先级声明：设定 > 后面所有通用规则
        blocks.append(
            "【设定优先级】上面这些设定是硬约束，优先级高于后面任何通用提示；"
            "若有冲突，一律以这里的设定为准。"
        )

        return "\n".join(blocks)

    @staticmethod
    def prompt_from_payload(payload: Dict) -> str:
        """用「表单草稿」拼 prompt（角色还没入库时用，供创建前试聊）

        与 build_persona_prompt 走同一套规则，保证「试聊看到的」和「创建后聊到的」一致。
        """
        draft = AIRole(
            role_type=(_s(payload.get("roleKey")) or "preview"),
            name=_s(payload.get("name")) or "我的伙伴",
            personality=_s(payload.get("personality")) or "独一无二的存在",
            description=_s(payload.get("description")),
            avatar=_s(payload.get("avatar")) or "✨",
            backstory=_s(payload.get("backstory")),
            speech_style=_s(payload.get("speechStyle")),
            quirks=_s(payload.get("quirks")),
            taboos=_s(payload.get("taboos")),
            expression_habits=_s(payload.get("expressionHabits")),
            angry_style=_s(payload.get("angryStyle")),
            happy_style=_s(payload.get("happyStyle")),
            voice_tone=_s(payload.get("voiceTone")) or "warm",
            nickname=_s(payload.get("nickname")),
            mood=_s(payload.get("mood")) or "normal",
        )
        return PersonaService.build_persona_prompt(draft)

    # ---------------- 序列化 ----------------
    @staticmethod
    def serialize_role(role: AIRole, detail: bool = False) -> Dict:
        mood = _s(role.mood) or "normal"
        data = {
            "id": role.id,
            "roleKey": role.role_type,
            "name": role.name,
            "avatar": role.avatar or "",
            "personality": role.personality or "",
            "description": role.description or "",
            "origin": role.origin or "official",
            "creatorId": role.creator_id or 0,
            "mood": mood,
            "moodLabel": MOOD_LABELS.get(mood, "平常"),
            "moodEmoji": MOOD_EMOJI.get(mood, "🌿"),
            "moodNote": role.mood_note or "",
            "voiceTone": role.voice_tone or "",
            "voiceParams": VOICE_TONE_PARAMS.get(role.voice_tone or "", VOICE_TONE_PARAMS["warm"]),
            "nickname": role.nickname or "",
            "traits": [t for t in (role.personality or "").split("、") if t],
        }
        if detail:
            data.update({
                "backstory": role.backstory or "",
                "speechStyle": role.speech_style or "",
                "quirks": role.quirks or "",
                "taboos": role.taboos or "",
                "expressionHabits": role.expression_habits or "",
                "angryStyle": role.angry_style or "",
                "happyStyle": role.happy_style or "",
                "greeting": PersonaService.default_greeting(role),
            })
        return data

    @staticmethod
    def default_greeting(role: AIRole) -> str:
        nickname = _s(role.nickname)
        who = f"{nickname}" if nickname else "你"
        return f"{who}来了。今天想聊点什么？我在。"

    # ---------------- 列表 ----------------
    # 旧 7 个硬编码角色（migration_companion_v3.sql seed 的 origin='official' 脏数据）
    # 前端已统一用 ai-characters.js 的 CHARACTERS 20 个；这里过滤掉旧的，防止混乱
    _DEPRECATED_OFFICIAL_ROLE_TYPES = {
        "cute", "gentle", "serious", "energetic",
        "companion", "mentor", "friend",
    }

    @staticmethod
    def list_roles(db: Session, user_id: int, scope: str = "all",
                   detail: bool = False) -> List[Dict]:
        q = db.query(AIRole).filter(AIRole.status == 1)

        # ↓↓↓ 安全加固 1：deprecated 过滤下推 SQL 层，避免 Python 遍历全量 ↓↓↓
        # role_type 是后端生成的字符串，用户无法伪造 deprecated 值 → 无注入风险
        q = q.filter(~AIRole.role_type.in_(PersonaService._DEPRECATED_OFFICIAL_ROLE_TYPES))

        if scope == "official":
            q = q.filter(AIRole.origin == "official")
        elif scope == "custom":
            q = q.filter(AIRole.origin == "custom", AIRole.creator_id == user_id)
        elif scope == "gacha":
            q = q.filter(AIRole.origin == "gacha", AIRole.creator_id == user_id)
        elif scope == "mine":
            q = q.filter(
                (AIRole.creator_id == user_id) | (AIRole.origin == "official")
            )
        roles = q.order_by(AIRole.sort_order.asc(), AIRole.id.asc()).all()

        # ↓↓↓ 安全加固 2："冒烟"过滤 —— scope=all 时全量过滤（不管 origin）；
        #                           scope=custom/gacha 时不过滤（用户自己创建/抽到的可能想要）↓↓↓
        if scope in ("all", "official", "mine"):
            filtered = [
                r for r in roles
                if not (r.name and r.name.startswith("冒烟"))
            ]
        else:
            filtered = roles
        return [PersonaService.serialize_role(r, detail) for r in filtered]

    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[AIRole]:
        return db.query(AIRole).filter(AIRole.id == role_id, AIRole.status == 1).first()

    @staticmethod
    def get_role_by_key(db: Session, role_key: str) -> Optional[AIRole]:
        if not role_key:
            return None
        return db.query(AIRole).filter(
            AIRole.role_type == role_key, AIRole.status == 1
        ).first()

    # ---------------- 自捏角色 ----------------
    @staticmethod
    def _compose_extra(payload: Dict) -> Dict:
        """把前端零散字段（口头禅 / 语气词 / 语气风格说明）合并进三列文本

        工坊表单里用户填的是「口头禅」「独立语气词」「说话语气风格」，
        而 ai_roles 只有 quirks / expression_habits / speech_style 三列。
        这里统一合并，前端不用关心落库细节；旧调用方不传这些键时结果与原来一致。
        """
        quirks = _s(payload.get("quirks"))
        catchphrase = _s(payload.get("catchphrase"))
        if catchphrase:
            quirks = f"{quirks}；口头禅：{catchphrase}" if quirks else f"口头禅：{catchphrase}"

        habits = _s(payload.get("expressionHabits"))
        voice_words = payload.get("voiceWords")
        if isinstance(voice_words, (list, tuple)):
            voice_words = "、".join([_s(w) for w in voice_words if _s(w)])
        voice_words = _s(voice_words)
        if voice_words:
            habits = (f"{habits}；说话常带语气词：{voice_words}" if habits
                      else f"说话常带语气词：{voice_words}")

        speech = _s(payload.get("speechStyle"))
        tone = _s(payload.get("speechTone"))
        if tone and tone not in speech:
            speech = f"{speech}（{tone}）" if speech else tone

        return {"quirks": quirks, "expression_habits": habits, "speech_style": speech}

    @staticmethod
    def create_custom_role(db: Session, user_id: int, payload: Dict) -> AIRole:
        name = _s(payload.get("name"))[:50] or "我的伙伴"
        role_type = f"custom_{user_id}_{_rand_suffix()}"
        extra = PersonaService._compose_extra(payload)
        role = AIRole(
            role_type=role_type,
            name=name,
            personality=_s(payload.get("personality"))[:255] or "独一无二的存在",
            description=_s(payload.get("description"))[:255] or name,
            avatar=_s(payload.get("avatar"))[:32] or "✨",
            backstory=_s(payload.get("backstory")),
            speech_style=extra["speech_style"][:255],
            quirks=extra["quirks"],
            taboos=_s(payload.get("taboos")),
            expression_habits=extra["expression_habits"],
            angry_style=_s(payload.get("angryStyle")),
            happy_style=_s(payload.get("happyStyle")),
            voice_tone=_s(payload.get("voiceTone"))[:64] or "warm",
            nickname=_s(payload.get("nickname"))[:64],
            mood=_s(payload.get("mood"))[:32] or "normal",
            mood_note=_s(payload.get("moodNote"))[:255],
            mood_updated_at=datetime.now(),
            origin="custom",
            creator_id=user_id,
            sort_order=100,
            status=1,
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        # ↓↓↓ v3.1：给新角色一条「初见」记忆 ↓↓↓
        # 好处有两点：① 记忆面板一进去就有内容，不是空白页；
        # ② 下次聊天时这段记忆会被召回，TA 会记得自己是谁、一开始是什么样。
        try:
            greeting = PersonaService.default_greeting(role)
            MemoryService.add_memory(
                db, user_id,
                f"你们刚认识。{name}是这样一个人：{_s(role.personality) or '独一无二的存在'}。"
                f"TA 跟你说的第一句话是「{greeting}」",
                layer="profile", role_key=role_type, role_id=role.id,
                title="初见", salience=8, source="auto",
            )
        except Exception as e:      # 记忆写失败绝不影响角色创建
            print(f"[persona][WARN] 初见记忆写入失败，忽略: {type(e).__name__}: {e}")

        return role

    UPDATABLE_FIELDS = {
        "name": "name",
        "personality": "personality",
        "description": "description",
        "avatar": "avatar",
        "backstory": "backstory",
        "speechStyle": "speech_style",
        "quirks": "quirks",
        "taboos": "taboos",
        "expressionHabits": "expression_habits",
        "angryStyle": "angry_style",
        "happyStyle": "happy_style",
        "voiceTone": "voice_tone",
        "nickname": "nickname",
        "mood": "mood",
        "moodNote": "mood_note",
    }

    @staticmethod
    def update_role(db: Session, user_id: int, role_id: int, payload: Dict) -> Optional[AIRole]:
        role = PersonaService.get_role(db, role_id)
        if not role:
            return None
        # 只允许改自己的（官方角色所有人可见但不允许被改）
        if role.creator_id and role.creator_id != user_id:
            return None

        # 编辑时前端可能只改了「口头禅 / 语气词」：先与库里现有文本合并，避免把旧内容覆盖掉
        if any(k in payload for k in ("catchphrase", "voiceWords", "speechTone")):
            extra = PersonaService._compose_extra({
                **payload,
                "quirks": payload.get("quirks", role.quirks or ""),
                "expressionHabits": payload.get("expressionHabits", role.expression_habits or ""),
                "speechStyle": payload.get("speechStyle", role.speech_style or ""),
            })
            payload = {**payload, "quirks": extra["quirks"],
                       "expressionHabits": extra["expression_habits"],
                       "speechStyle": extra["speech_style"]}

        for key, col in PersonaService.UPDATABLE_FIELDS.items():
            if key in payload and payload[key] is not None:
                setattr(role, col, _s(payload[key]) if isinstance(payload[key], str) else payload[key])
        if "mood" in payload:
            role.mood_updated_at = datetime.now()
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def set_mood(db: Session, user_id: int, role_id: int, mood: str,
                 mood_note: str = "") -> Optional[AIRole]:
        role = PersonaService.get_role(db, role_id)
        if not role:
            return None
        if role.creator_id and role.creator_id != user_id:
            return None
        role.mood = mood if mood in MOOD_MODIFIERS else "normal"
        role.mood_note = _s(mood_note)[:255]
        role.mood_updated_at = datetime.now()
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def delete_role(db: Session, user_id: int, role_id: int) -> bool:
        role = PersonaService.get_role(db, role_id)
        if not role or not role.creator_id or role.creator_id != user_id:
            return False
        role.status = 0
        db.commit()
        # 角色删掉后，它名下的记忆一并清空（避免留下无主记忆）
        MemoryService.clear_memories(db, user_id, role.role_type)
        return True

    # ---------------- 扭蛋角色 ----------------
    @staticmethod
    def draw_gacha_character(db: Session, user_id: int) -> Optional[Dict]:
        """抽一个角色：写入 ai_roles 并初始化独立记忆空间"""
        pool = db.query(GachaCharacterPool).filter(
            GachaCharacterPool.status == 1
        ).order_by(GachaCharacterPool.sort_order).all()
        if not pool:
            return None

        # 已拥有的不再重复抽（避免抽到两个一样的）
        owned = {r.name for r in db.query(AIRole).filter(
            AIRole.origin == "gacha", AIRole.creator_id == user_id,
            AIRole.status == 1
        ).all()}
        candidates = [p for p in pool if p.name not in owned] or pool

        weights = [RARITY_WEIGHT.get(p.rarity, 20) for p in candidates]
        picked = random.choices(candidates, weights=weights, k=1)[0]

        role_type = f"gacha_{user_id}_{_rand_suffix(8)}"
        role = AIRole(
            role_type=role_type,
            name=picked.name,
            personality=picked.personality or "有故事的人",
            description=picked.catchphrase or picked.personality or "",
            avatar=picked.avatar or "🎁",
            backstory=picked.backstory or "",
            speech_style=picked.speech_style or "",
            quirks=picked.quirks or "",
            taboos=picked.taboos or "",
            expression_habits=picked.expression_habits or "",
            angry_style=picked.angry_style or "",
            happy_style=picked.happy_style or "",
            voice_tone=picked.voice_tone or "warm",
            nickname="",
            mood="normal",
            origin="gacha",
            creator_id=user_id,
            sort_order=200,
            status=1,
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        # 独立记忆空间：第一条记忆属于这个角色，之后 TA 记住的一切都不会串到别的角色
        MemoryService.add_memory(
            db, user_id,
            f"你们是在扭蛋机前认识的。{picked.name}说：「{picked.greeting or picked.catchphrase or '嗨，以后请多指教。'}」",
            layer="event", role_key=role_type, role_id=role.id,
            title="初见", salience=8, source="auto",
        )

        data = PersonaService.serialize_role(role, detail=True)
        data.update({
            "rarity": picked.rarity,
            "rarityLabel": RARITY_LABEL.get(picked.rarity, "稀有"),
            "catchphrase": picked.catchphrase or "",
            "greeting": picked.greeting or picked.catchphrase or "",
            "isNew": True,
        })
        return data

    @staticmethod
    def gacha_pool(db: Session) -> List[Dict]:
        rows = db.query(GachaCharacterPool).filter(
            GachaCharacterPool.status == 1
        ).order_by(GachaCharacterPool.sort_order).all()
        return [{
            "id": p.id,
            "name": p.name,
            "avatar": p.avatar,
            "rarity": p.rarity,
            "rarityLabel": RARITY_LABEL.get(p.rarity, "稀有"),
            "personality": p.personality,
            "catchphrase": p.catchphrase,
            "voiceTone": p.voice_tone,
        } for p in rows]
