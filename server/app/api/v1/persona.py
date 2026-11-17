# -*- coding: utf-8 -*-
"""
角色人设 API —— 陪伴感增强 v3

官方角色：完整人设故事线 / 专属说话风格 / 小癖好 / 心情状态
自捏角色：雷区、说话禁忌、表达习惯、生气·开心的样子、音色自选
扭蛋角色：抽出来即配套完整独立人设 + 独立记忆空间
"""
from typing import Dict

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import ResponseBase
from app.services.persona_service import (
    PersonaService, MOOD_LABELS, MOOD_EMOJI, VOICE_TONES, VOICE_TONE_PARAMS, RARITY_LABEL,
)

router = APIRouter(prefix="/persona", tags=["角色人设"])


@router.get("/options")
def persona_options():
    """前端下拉选项：音色、心情、稀有度"""
    return ResponseBase.success(data={
        "voiceTones": VOICE_TONES,
        "voiceToneParams": VOICE_TONE_PARAMS,
        "moods": [{"key": k, "label": v, "emoji": MOOD_EMOJI.get(k, "🌿")}
                  for k, v in MOOD_LABELS.items()],
        "rarities": [{"key": k, "label": v} for k, v in RARITY_LABEL.items()],
    })


@router.get("/roles")
def list_roles(scope: str = Query(default="all", description="all/official/custom/gacha/mine"),
               detail: bool = Query(default=False, description="true=返回完整人设字段"),
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """角色列表"""
    return ResponseBase.success(data=PersonaService.list_roles(db, user_id, scope, detail))


@router.get("/role/key/{role_key}")
def get_role_by_key(role_key: str, detail: bool = Query(default=True),
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """按 role_key 取角色（前端常用入口）"""
    role = PersonaService.get_role_by_key(db, role_key)
    if not role:
        return ResponseBase.error(message="角色不存在", code=404)
    return ResponseBase.success(data=PersonaService.serialize_role(role, detail))


@router.get("/role/{role_id}")
def get_role(role_id: int, detail: bool = Query(default=True),
             user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """角色详情"""
    role = PersonaService.get_role(db, role_id)
    if not role:
        return ResponseBase.error(message="角色不存在", code=404)
    return ResponseBase.success(data=PersonaService.serialize_role(role, detail))


@router.post("/role")
def create_role(payload: Dict = Body(...), user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """创建自捏角色（含雷区/禁忌/表达习惯/生气开心表现/音色）"""
    if not (payload.get("name") or "").strip():
        return ResponseBase.error(message="角色名不能为空", code=400)
    role = PersonaService.create_custom_role(db, user_id, payload)
    return ResponseBase.success(data=PersonaService.serialize_role(role, True), message="角色已创建")


# ↓↓↓ v3.1 新增：创建前试聊（不落库，纯校验「设定是否严格生效」） ↓↓↓
@router.post("/preview")
async def preview_role(payload: Dict = Body(...), user_id: int = Depends(get_current_user)):
    """用当前表单草稿拼 prompt，让大模型以这个角色回一句

    - 不写数据库、不产生记忆，纯粹是「所见即所得」的设定自检
    - 走和正式聊天完全相同的 build_persona_prompt，所以试聊像、正式聊天就像
    """
    from app.services.ai_service import AIService

    name = (payload.get("name") or "").strip()
    if not name:
        return ResponseBase.error(message="先给 TA 起个名字，再试聊", code=400)

    test_message = (payload.get("testMessage") or "").strip()[:200] or "你好呀，第一次见面。"
    persona_prompt = PersonaService.prompt_from_payload(payload)
    system_prompt = AIService.build_system_prompt(
        role_type="companion",
        dialogue_style="gentle",
        persona_prompt=persona_prompt,
    )
    try:
        reply = await AIService.chat_non_stream([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_message},
        ])
    except Exception as e:
        print(f"[persona][WARN] 试聊调用失败: {type(e).__name__}: {e}")
        return ResponseBase.error(message="AI 暂时没有回应，请稍后再试", code=500)

    if not reply:
        return ResponseBase.error(message="AI 暂时没有回应，请稍后再试", code=500)

    return ResponseBase.success(data={
        "reply": reply,
        "name": name,
        "testMessage": test_message,
        # 把命中的设定条数回给前端，让用户知道「哪些设定被模型看到了」
        "appliedFields": [
            k for k in ("personality", "description", "backstory", "speechStyle",
                        "quirks", "expressionHabits", "taboos", "angryStyle",
                        "happyStyle", "nickname", "catchphrase", "voiceWords")
            if (payload.get(k) or "") not in ("", [], None)
        ],
    })
# ↑↑↑ 新增结束 ↑↑↑


@router.put("/role/{role_id}")
def update_role(role_id: int, payload: Dict = Body(...),
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """编辑自捏角色"""
    role = PersonaService.update_role(db, user_id, role_id, payload)
    if not role:
        return ResponseBase.error(message="角色不存在或不属于你", code=404)
    return ResponseBase.success(data=PersonaService.serialize_role(role, True), message="已保存")


@router.delete("/role/{role_id}")
def delete_role(role_id: int, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """删除自捏角色（连带清空该角色名下的记忆）"""
    ok = PersonaService.delete_role(db, user_id, role_id)
    if not ok:
        return ResponseBase.error(message="角色不存在或不属于你", code=404)
    return ResponseBase.success(message="角色已删除")


@router.post("/role/{role_id}/mood")
def set_mood(role_id: int, payload: Dict = Body(...),
             user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """设置角色心情/状态（会影响 TA 当下说话的情绪）"""
    role = PersonaService.set_mood(db, user_id, role_id,
                                   payload.get("mood", "normal"),
                                   payload.get("moodNote", ""))
    if not role:
        return ResponseBase.error(message="角色不存在或不属于你", code=404)
    return ResponseBase.success(data=PersonaService.serialize_role(role, False), message="状态已更新")


@router.get("/gacha/pool")
def gacha_pool(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """扭蛋角色池一览"""
    return ResponseBase.success(data=PersonaService.gacha_pool(db))


@router.post("/gacha/draw")
def draw_gacha(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """抽一个角色：完整独立人设 + 独立记忆空间"""
    data = PersonaService.draw_gacha_character(db, user_id)
    if not data:
        return ResponseBase.error(message="扭蛋角色池为空", code=404)
    return ResponseBase.success(data=data, message=f"抽到了 {data['name']}")
