# -*- coding: utf-8 -*-
"""
AI对话 API - SSE流式 + 上下文管理 + 危机干预
"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.schemas.common import ResponseBase
from app.schemas.chat import ChatSendRequest, ChatQuickRequest
from app.services.ai_service import AIService
from app.services.emotion_service import EmotionService
from app.services.crisis_service import CrisisService
# ↓↓↓ 陪伴感增强 v3 ↓↓↓
from app.services.memory_service import MemoryService
from app.services.persona_service import PersonaService
from app.services.proactive_service import build_empathy_instruction
from app.services.persona_service import MOOD_LABELS, MOOD_EMOJI
# ↑↑↑ 新增结束 ↑↑↑
# ↓↓↓ 新增（2026-11-15）：行动建议（推荐正念/情绪树洞/专注等 App 内功能） ↓↓↓
from app.services.action_suggestion_service import ActionSuggestionService
# ↑↑↑ 新增结束 ↑↑↑
# ↓↓↓ 安全合规批次 ↓↓↓ 高危检测 / AI输出后置过滤 / 幂等防重
from app.utils.danger_sentiment import detect_danger
from app.utils.content_security import ContentSecurity
from app.utils import idempotency as idem
# ↑↑↑ 新增结束 ↑↑↑
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["AI对话"])


def _build_habit_summary(db: Session, user_id: int) -> str:
    """查询用户近期习惯数据，格式化为可注入 prompt 的摘要

    仅在话题与习惯/打卡相关时才调用（见 AIService.should_inject_habit_context）
    """
    from app.models.habit import Habit, Checkin, CheckinItem

    habits = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    ).order_by(Habit.sort_order).limit(10).all()

    rows = db.query(CheckinItem, Habit.name).join(
        Habit, Habit.id == CheckinItem.habit_id
    ).filter(
        CheckinItem.user_id == user_id
    ).order_by(CheckinItem.id.desc()).limit(14).all()

    recent_items = []
    for item, habit_name in rows:
        d = item.created_at.strftime("%m-%d") if item.created_at else ""
        recent_items.append((d, habit_name, bool(item.completed)))

    latest = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.status == 1
    ).order_by(Checkin.checkin_date.desc()).first()
    streak = latest.streak_days if latest else 0

    return AIService.format_habit_summary(habits, recent_items, streak)


# ↓↓↓ 新增（2026-10-28 需求5 / 需求7） ↓↓↓
# 用户说出「先不说这个了」这类退出指令时，作为一条硬性指令注入 system prompt。
# 不拼进 habit_story_block，是因为此刻要的是「立刻停止」，而不是继续回忆这条习惯。
EXIT_HABIT_TOPIC_DIRECTIVE = (
    "【话题切换】用户刚刚明确表示不想再聊这个话题了。"
    "请先简短地接住这句话（可以说「好，那我们先不说这个啦」），然后立刻停止这个话题："
    "不要追问原因、不要挽留、不要总结、不要提任何打卡/目标/进度/完成情况，"
    "安静地回到普通陪伴，等他先开口。"
)
# ↑↑↑ 新增结束 ↑↑↑


@router.post("/crisis-check")
async def crisis_check(content: str = Body(..., embed=True)):
    """危机检测(前端发送消息前先行调用)"""
    result = CrisisService.check_crisis(content)

    is_crisis = result["level"] == "critical"
    severity = "high" if result["level"] == "critical" else (
        "medium" if result["level"] == "high" else "low"
    )
    resources = result.get("resources", [])
    hotline = resources[0]["phone"] if resources else ""

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "is_crisis": is_crisis,
            "severity": severity,
            "keywords": [result["trigger"]] if result.get("trigger") else [],
            "response": result.get("message", ""),
            "hotline": hotline,
            "resources": resources,
        },
    }


@router.post("/send")
async def send_message(req: ChatSendRequest, user_id: int = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """发送消息(SSE流式响应)"""
    # ↓↓↓ 安全合规批次：发消息幂等防重（相同内容短窗口内重复提交只处理一次） ↓↓↓
    idem_key, idem_window = idem.chat_key(user_id, req.content)
    if not idem.try_acquire(idem_key, idem_window):
        return ResponseBase.error("消息正在发送中，请稍等片刻再试", code=429)
    # ↑↑↑ 新增结束 ↑↑↑

    # 获取或创建会话
    session = None
    if req.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == req.session_id, ChatSession.user_id == user_id
        ).first()
    if not session:
        session = ChatSession(
            user_id=user_id, role_type=req.role_type,
            title=req.content[:50] if req.content else "新对话",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 保存用户消息
    emotion_analysis = EmotionService.analyze_emotion(req.content)
    user_msg = ChatMessage(
        session_id=session.id, user_id=user_id, role="user",
        content=req.content, emotion=emotion_analysis["valence"],
    )
    db.add(user_msg)
    db.flush()          # 立即拿到自增 id，供下方从历史中排除

    # 危机检测
    crisis = CrisisService.check_crisis(req.content)

    # ↓↓↓ 安全合规批次：高危信号前置检测（比危机共情更硬的一道闸门） ↓↓↓
    # 命中时走 danger SSE 事件，前端弹 danger_warn 弹窗并附求助热线，本次不进入大模型。
    danger = detect_danger(req.content)
    if danger["is_danger"]:
        crisis = {"level": "critical", "message": danger["message"], "resources": danger["resources"]}
        crisis["_danger"] = True
    # ↑↑↑ 新增结束 ↑↑↑

    # ↓↓↓ 新增（2026-10-28 打卡上下文延续 / 需求1·2·5·7） ↓↓↓
    # 习惯会话模式：这次对话要不要带着某一条习惯的完整历程。
    # 规则优先级：退出指令 > 总开关关闭 > 危机期 > 静默期 > 沿用会话已挂载的习惯
    from app.services.habit_companion_service import HabitCompanionService as HCS
    focus_habit = None
    habit_story_block = ""
    habit_context_payload = {
        "habit_id": 0, "habit_name": "", "active": False,
        "exited": False, "reason": "",
    }
    topic_exit_directive = ""
    try:
        prev_focus = int(session.habit_id or 0)
        req_habit = int(req.habit_id) if req.habit_id is not None else None
        want_exit = (req_habit == -1) or HCS.detect_exit_habit_topic(req.content)

        if want_exit and prev_focus:
            # 用户说「先不说这个了」→ 立刻退出，并把这条习惯静默 3 天
            HCS.mute_habit_topic(db, user_id, prev_focus)
            session.habit_id = 0
            db.commit()
            habit_context_payload.update({"exited": True, "reason": "user_exit"})
            topic_exit_directive = EXIT_HABIT_TOPIC_DIRECTIVE
        elif not HCS.habit_topic_allowed(db, user_id):
            # 总开关关闭：任何习惯上下文都不挂载，AI 完全回归纯情绪陪伴
            if prev_focus:
                session.habit_id = 0
                db.commit()
            habit_context_payload["reason"] = "topic_switch_off"
        elif crisis["level"] == "critical":
            # 危机期：情绪急救优先，不挂习惯话题
            habit_context_payload["reason"] = "crisis"
        else:
            hid = req_habit if (req_habit and req_habit > 0) else prev_focus
            if hid:
                muted = HCS.is_habit_muted(db, user_id, hid)
                if muted and req_habit and req_habit > 0:
                    # 用户主动重新聊起 → 解除静默（静默只限制「主动提起」，不限制用户自己开口）
                    HCS.clear_habit_mute(db, user_id, hid)
                    muted = False
                if muted:
                    if prev_focus == hid:
                        session.habit_id = 0
                        db.commit()
                    habit_context_payload["reason"] = "habit_muted"
                else:
                    focus_habit = HCS.resolve_focus_habit(db, user_id, hid)

        if focus_habit is not None:
            session.habit_id = focus_habit.id
            db.commit()
            # 本次打卡事件：取 24h 内最近的一条，AI 才能顺着「刚刚这件事」继续聊
            event, emotion = "", ""
            try:
                for m in HCS.list_habit_memories(db, user_id, habit_id=focus_habit.id, limit=5):
                    ev = (m.context_data or {}).get("event", "")
                    if not ev:
                        continue
                    if m.created_at and (datetime.now() - m.created_at).total_seconds() <= 86400:
                        event, emotion = ev, (m.context_data or {}).get("emotion", "")
                    break
            except Exception as _e:
                print(f"[chat][WARN] 读取最近习惯事件失败，仅注入历程: {type(_e).__name__}: {_e}")
            # role_key 在下方「角色人设」那段才算出来，这里先按同一规则取一份
            _rk = (req.role_key or "").strip() or (req.role_type or "")
            habit_story_block = HCS.build_habit_focus_block(
                db, user_id, focus_habit, event=event, emotion=emotion, role_key=_rk
            )
            habit_context_payload.update({
                "habit_id": focus_habit.id,
                "habit_name": focus_habit.name or "",
                "active": True,
                "event": event,
                "emotion": emotion,
            })
    except Exception as e:
        print(f"[chat][WARN] 习惯上下文处理失败，本次按普通闲聊处理: {type(e).__name__}: {e}")
    # ↑↑↑ 新增结束 ↑↑↑

    # 获取历史消息(上下文)
    # ★ 必须排除刚 add 的当前这条：SQLAlchemy 默认 autoflush 会让它出现在查询结果里，
    #   而 build_context_messages 又会在数组末尾追加一次用户输入 —— 不排除就会重复发给大模型。
    history = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id,
        ChatMessage.id != user_msg.id,
    ).order_by(ChatMessage.id).limit(30).all()

    history_list = [{"role": h.role, "content": h.content} for h in history]

    # 习惯记忆锚点：仅当用户话题与习惯/打卡相关时才注入，日常闲聊不注入（避免污染上下文）
    # ↓↓↓ 修正（2026-10-28）：已进入习惯会话模式时不再注入这份「所有习惯混在一起的打卡流水」，
    #      否则会和单条习惯的完整历程重复，模型又会被拉回碎片化读数。
    habit_summary = ""
    if focus_habit is None and AIService.should_inject_habit_context(req.content):
        try:
            habit_summary = _build_habit_summary(db, user_id)
        except Exception as e:
            print(f"[chat][WARN] 构建习惯摘要失败，本次跳过注入: {type(e).__name__}: {e}")

    # ↓↓↓ 陪伴感增强 v3：角色人设 + 分层记忆 + 分层共情 ↓↓↓
    # 角色标识约定（v3.1 修正）：
    #   role_type 历史语义是「对话风格 token」（relaxed/y2k/gentle…），前端一直用它传风格；
    #   新增的 role_key 才是 ai_roles.role_type（官方 linxi / 自捏 custom_12_xxx / 扭蛋 gacha_12_xxx）。
    #   为空时回退到 role_type，保证老调用方行为完全不变。
    role_key = (req.role_key or "").strip() or (req.role_type or "")
    _role = PersonaService.get_role_by_key(db, role_key)
    # 越权保护：别人的自捏/扭蛋角色不允许被当成人设使用
    if _role and _role.creator_id and _role.creator_id != user_id:
        _role = None
        role_key = ""
    persona_prompt = PersonaService.build_persona_prompt(_role) if _role else ""

    memory_block = ""
    try:
        # 规则抽取：高信号句式（我叫/我喜欢/约好/记住…）立刻入库，零延迟
        MemoryService.extract_by_rules(db, user_id, role_key, req.content,
                                       _role.id if _role else 0)
        # 召回：相关性 + 重要度 + 新鲜度
        memory_block = MemoryService.build_prompt_block(db, user_id, role_key, req.content)
    except Exception as e:
        print(f"[chat][WARN] 记忆读写失败，本次跳过注入: {type(e).__name__}: {e}")

    empathy_block = build_empathy_instruction(
        emotion_analysis.get("emotion", ""),
        int(emotion_analysis.get("intensity", 0) or 0),
        crisis["level"] == "critical",
    )
    # ↑↑↑ 新增结束 ↑↑↑

    # ↓↓↓ 新增（2026-11-15）：根据这句话推荐 App 内可做的事 ↓↓↓
    # 纯规则、失败静默；危机期 / 用户拒绝建议时返回空列表，原有行为不变
    action_suggestions = []
    try:
        if crisis["level"] != "critical":
            action_suggestions = ActionSuggestionService.suggest(
                req.content, emotion_analysis, session_key=session.id
            )
    except Exception as e:
        print(f"[chat][WARN] 行动建议生成失败，本次不推荐: {type(e).__name__}: {e}")
    # ↑↑↑ 新增结束 ↑↑↑

    # 构建 system prompt
    system_prompt = AIService.build_system_prompt(
        role_type=req.role_type,
        dialogue_style=req.dialogue_style,
        user_emotion=emotion_analysis["emotion"],
        scene_type=req.scene_type,
        scene_name=req.scene_name,
        habit_summary=habit_summary,
        language=req.language,
        # ↓↓↓ 陪伴感增强 v3（三个参数默认空 → 老行为不变） ↓↓↓
        persona_prompt=persona_prompt,
        memory_block=memory_block,
        empathy_block=empathy_block,
        # ↓↓↓ 新增（2026-10-28）：单条习惯的完整历程（空串=老行为不变） ↓↓↓
        habit_story_block=habit_story_block,
        # ↓↓↓ 新增（2026-10-28）：退出习惯专题时的硬性指令 ↓↓↓
        topic_exit_directive=topic_exit_directive,
        # ↓↓↓ 群聊场景：前端拼好的群成员列表 + 最近发言 ↓↓↓
        group_context=req.group_context or "",
        # ↓↓↓ 新增（2026-11-15）：可推荐功能的邀请规则（空串=不注入） ↓↓↓
        suggestion_block=ActionSuggestionService.build_prompt_block(action_suggestions),
        # ↑↑↑ 新增结束 ↑↑↑
    )

    # 构建上下文消息（取最近 15 轮 = 30 条消息，glm-4-flash 足够接住）
    messages = AIService.build_context_messages(
        history_list, system_prompt, req.content, max_rounds=15
    )

    # 更新会话
    session.message_count += 2
    session.last_message_time = datetime.now(timezone.utc)
    db.commit()

    async def event_stream():
        """SSE 流式输出"""
        full_reply = ""
        try:
            # ↓↓↓ v3.1：先回传会话 id ↓↓↓
            # 前端一直没有拿到过 session_id（只有请求里传，没有回传），于是每条消息都开新会话，
            # 服务端历史永远是空的 —— 这是"AI 记不住上一句"的根因。
            # 这里作为第一个事件下发，不含 content，老前端会忽略，不影响现有行为。
            yield f"data: {json.dumps({'session_id': session.id}, ensure_ascii=False)}\n\n"

            # ↓↓↓ 新增（2026-10-28）：回传习惯会话模式状态 ↓↓↓
            # 前端据此在输入框上方显示「正在聊：XX」并可一键退出，
            # 老前端不认这个字段，直接忽略（与 session_id 同一个事件通道）。
            yield f"data: {json.dumps({'habit_context': habit_context_payload}, ensure_ascii=False)}\n\n"

            # ↓↓↓ 模块1新增：情绪陪伴事件（让前端知道用户当前情绪 + 是否触发陪伴分支） ↓↓↓
            try:
                from app.services.emotion_service import EmotionService as _ES
                _comfort_data = {
                    "type": "emotion_comfort",
                    "emotion": emotion_analysis.get("emotion", "neutral"),
                    "valence": emotion_analysis.get("valence", "neutral"),
                    "confidence": emotion_analysis.get("confidence", 0.0),
                    "triggered": _ES.should_trigger_comfort(emotion_analysis, req.content),
                    "venting": _ES.is_venting(req.content),
                    "rejected": _ES.is_rejecting_comfort(req.content),
                    "crisis": _ES.is_crisis_level(emotion_analysis),
                }
                yield f"data: {json.dumps(_comfort_data, ensure_ascii=False)}\n\n"
            except Exception:
                pass
            # ↑↑↑ 模块1结束 ↑↑↑

            # ↓↓↓ 新增（2026-11-15）：行动建议事件（前端渲染为可点击的功能卡片） ↓↓↓
            if action_suggestions:
                yield f"data: {json.dumps({'type': 'suggestion', 'items': action_suggestions}, ensure_ascii=False)}\n\n"
            # ↑↑↑ 新增结束 ↑↑↑

            if crisis["level"] == "critical":
                crisis_data = {
                    "type": "crisis",
                    "level": "critical",
                    "message": crisis["message"],
                    "resources": crisis["resources"],
                }
                # ↓↓↓ 安全合规批次：高危检测命中时补 is_danger 标记，前端弹 danger_warn 而非普通危机弹窗 ↓↓↓
                if crisis.get("_danger"):
                    crisis_data["is_danger"] = True
                # ↑↑↑ 新增结束 ↑↑↑
                yield f"data: {json.dumps(crisis_data, ensure_ascii=False)}\n\n"
                full_reply = crisis["message"]

            async for chunk in AIService.chat_stream(messages):
                data = json.loads(chunk[6:].strip())
                if data.get("content"):
                    full_reply += data["content"]
                yield chunk

            # ↓↓↓ 安全合规批次：AI 输出后置过滤（违规词清洗后再入库，兜底大模型漏网之鱼） ↓↓↓
            full_reply = ContentSecurity.filter_ai_output(full_reply)
            # ↑↑↑ 新增结束 ↑↑↑

            ai_msg = ChatMessage(
                session_id=session.id, user_id=user_id, role="assistant",
                content=full_reply, ai_status="chat",
            )
            if crisis["level"] != "normal":
                ai_msg.comfort_text = crisis.get("message", "")
            db.add(ai_msg)
            db.commit()

            # ↓↓↓ 羁绊碎片：异步检查是否达到解锁阈值（fire-and-forget，不阻塞 SSE 流式返回） ↓↓↓
            try:
                import asyncio as _asyncio
                from app.services.bond_service import BondService
                if req.role_key and req.role_key != 'companion':
                    _asyncio.create_task(
                        BondService.check_and_unlock(user_id, req.role_key)
                    )
            except Exception:
                pass  # bond 解锁任何异常都静默，不影响对话主链路
            # ↑↑↑ 羁绊碎片结束 ↑↑↑

            # ↓↓↓ 模块1新增：情绪陪伴 hook（fire-and-forget，不阻塞主链路） ↓↓↓
            try:
                import asyncio as _asyncio2
                from app.services.emotion_service import EmotionService
                # 用户明确说"不要安慰" → 跳过所有情绪陪伴
                if not EmotionService.is_rejecting_comfort(req.content):
                    _asyncio2.create_task(_emotion_comfort_hook(user_id, req, emotion_analysis))
            except Exception:
                pass
            # ↑↑↑ 模块1结束 ↑↑↑

            # ↓↓↓ 陪伴感增强 v3.1：每 2 轮用大模型补抽一次记忆（静默，失败不影响对话） ↓↓↓
            # 频率从 3 轮改成 2 轮：规则只覆盖固定句式，其余细节（职业/近况/心事）
            # 全靠这次补抽，太稀疏就会"聊了半天什么都没记住"。
            try:
                user_turns = sum(1 for h in history_list if h.get("role") == "user") + 1
                if user_turns % 2 == 0:
                    saved = await MemoryService.extract_by_llm(
                        db, user_id, role_key,
                        history_list[-4:] + [
                            {"role": "user", "content": req.content},
                            {"role": "assistant", "content": full_reply},
                        ],
                        _role.id if _role else 0,
                    )
                    print(f"[chat][memory] turn={user_turns} role={role_key or '-'} saved={saved}")
            except Exception as e:
                print(f"[chat][WARN] 记忆抽取失败，忽略: {type(e).__name__}: {e}")
            # ↑↑↑ 新增结束 ↑↑↑

        except Exception as e:
            yield f"data: {json.dumps({'content': f'回复出错: {str(e)}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ↓↓↓ 新增 ↓↓↓
# 业务触发式 AI（打卡鼓励 / 情绪疏导 / 正念引导 / 地图节点分享）走的是
# common/ai-service.js -> common/ai-cloud-service.js，那一层原先无论配什么 provider
# 最终都落到 mockCloudCall() 返回本地模板，等于"假 AI"。
# 这里补一个非流式端点，让它能真正打到大模型；失败时前端仍会降级到本地模板。
MAX_QUICK_MESSAGES = 20


@router.get("/ai-status")
def ai_status():
    """AI 链路状态（供前端探测是否处于降级/离线陪伴模式；不含任何密钥信息）"""
    st = AIService.status()
    return ResponseBase.success({
        "configured": st["configured"],
        "degraded": st["degraded"],
        "circuit_open": st["circuit_open"],
    })


@router.post("/quick")
async def quick_chat(req: ChatQuickRequest, user_id: int = Depends(get_current_user)):
    """一次性对话(非流式) - 供业务触发式 AI 使用，返回完整文本"""
    cleaned = [
        {"role": m.role, "content": m.content}
        for m in req.messages
        if m.role in ("system", "user", "assistant") and m.content.strip()
    ][-MAX_QUICK_MESSAGES:]

    if not cleaned or cleaned[-1]["role"] != "user":
        return ResponseBase.error("消息格式不正确：最后一条必须是用户消息", code=422)

    reply, ai_meta = await AIService.chat_non_stream(cleaned, with_meta=True)
    if not reply:
        return ResponseBase.error("AI 暂时没有回应，请稍后再试", code=500)
    # ↓↓↓ 安全合规批次：业务触发式 AI 同样过后置过滤 ↓↓↓
    reply = ContentSecurity.filter_ai_output(reply)
    # ↑↑↑ 新增结束 ↑↑↑
    # degraded=true 表示本次回复来自本地离线兜底（大模型未配置 / 熔断 / 上游失败）
    return ResponseBase.success({"reply": reply, "degraded": bool(ai_meta.get("degraded")),
                                 "reason": ai_meta.get("reason", "")})
# ↑↑↑ 新增结束 ↑↑↑


@router.get("/history")
def get_history(session_id: int = 0, page: int = 1, page_size: int = 30,
                user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取对话历史"""
    query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if session_id:
        query = query.filter(ChatMessage.session_id == session_id)

    total = query.count()
    messages = query.order_by(ChatMessage.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    messages.reverse()

    return ResponseBase.success({
        "list": [{
            "id": m.id, "session_id": m.session_id, "role": m.role,
            "content": m.content, "emotion": m.emotion,
            "ai_status": m.ai_status, "comfort_text": m.comfort_text,
            "created_at": str(m.created_at),
        } for m in messages],
        "total": total, "page": page, "page_size": page_size,
    })


@router.get("/sessions")
def get_sessions(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取会话列表"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id, ChatSession.status == 1
    # MySQL 不支持 NULLS LAST 语法; DESC 时 NULL 本就排在最后, 直接 desc 即可
    ).order_by(ChatSession.last_message_time.desc()).limit(20).all()

    return ResponseBase.success([{
        "id": s.id, "role_type": s.role_type, "title": s.title,
        "message_count": s.message_count,
        "last_message_time": str(s.last_message_time) if s.last_message_time else "",
    } for s in sessions])


@router.get("/personas")
def get_personas(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """AI 角色列表（前端 user.js getAiRoles 调用）

    ↓↓↓ BUG-001 修复 ↓↓↓
    原实现返回 3 条硬编码假数据：id 为字符串（"companion"/"mentor"/"friend"）、
    avatar 为空、无 traits/personality，导致：
      1) 角色选择页头像为空白块、副标题统一显示兜底文案「贴心伙伴」；
      2) 选中后 role_id 传字符串给 POST /companion/start（schema 为 int）→ 422
         → 前端走异常兜底进入本地陪伴页，陪伴记录不入库。
    现改为读取 ai_roles 表（status=1，按 sort_order 排序），返回真实整型主键。
    """
    from app.models.chat import AIRole

    # role_type → 兜底头像（avatar 列为空时补上，避免前端出现空白块）
    DEFAULT_AVATAR = {
        "cute": "🌸", "gentle": "🌿", "serious": "📘", "energetic": "⚡",
    }

    # ↓↓↓ 陪伴感增强 v3：只暴露官方角色 + 本人捏的角色（别人的自捏/扭蛋角色不可见） ↓↓↓
    roles = db.query(AIRole).filter(
        AIRole.status == 1,
        (AIRole.creator_id == 0) | (AIRole.creator_id == user_id),
    ).order_by(
        AIRole.sort_order.asc(), AIRole.id.asc()
    ).all()

    data = []
    for r in roles:
        personality = r.personality or ""
        # traits：人格描述按中文顿号拆分，供前端 shortTraits() 直接取首项
        traits = [t for t in personality.split("、") if t] or ([personality] if personality else [])
        data.append({
            "id": r.id,                              # 整型主键，可直接作为 role_id 入库
            "name": r.name,
            "description": r.description or "",
            "personality": personality,
            "traits": traits,
            "roleType": r.role_type,
            "avatar": r.avatar or DEFAULT_AVATAR.get(r.role_type, "🌿"),
            # ↓↓↓ 陪伴感增强 v3：心情状态 / 音色 / 来源（老字段一个没动） ↓↓↓
            "mood": r.mood or "normal",
            "moodLabel": MOOD_LABELS.get(r.mood or "normal", "平常"),
            "moodEmoji": MOOD_EMOJI.get(r.mood or "normal", "🌿"),
            "moodNote": r.mood_note or "",
            "voiceTone": r.voice_tone or "",
            "nickname": r.nickname or "",
            "origin": r.origin or "official",
        })
    return ResponseBase.success(data)
    # ↑↑↑ BUG-001 修复结束 ↑↑↑


@router.get("/greeting")
def get_greeting(user_id: int = Depends(get_current_user)):
    """AI 情绪问候语（前端 user.js getAiEmotion 调用）"""
    return ResponseBase.success({
        "greeting": "你好呀，今天感觉怎么样？",
        "tip": "记得给自己一些温柔的时刻",
    })


# === ↓↓↓ 模块1新增：情绪陪伴后台 hook（fire-and-forget） ↓↓↓ ===
async def _emotion_comfort_hook(user_id: int, req: ChatSendRequest, emotion_analysis: dict):
    """
    后台异步：负面情绪时保存 emotion_records 记录。
    不阻塞 SSE 主链路。任何异常静默。
    """
    try:
        from app.services.emotion_service import EmotionService
        if not EmotionService.should_trigger_comfort(emotion_analysis, req.content):
            return  # 中性/正面情绪不需要写

        # 用 pymysql 直连（避免 SQLAlchemy async Session 并发问题）
        import pymysql
        from app.core.config import settings
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port,
            user=settings.db_user, password=settings.db_password,
            database=settings.db_name, charset='utf8mb4'
        )
        try:
            cur = conn.cursor()
            emotion = emotion_analysis.get("emotion", "neutral")
            intensity = 8 if EmotionService.is_crisis_level(emotion_analysis) else 6
            tags = ["chat", "emotion_comfort"]
            if EmotionService.is_venting(req.content):
                tags.append("venting")
            # emotion_records.description VARCHAR(200)，这里截断 200 避免 MySQL 警告
            cur.execute(
                "INSERT INTO emotion_records (user_id, emotion, intensity, tags, description, record_date) "
                "VALUES (%s, %s, %s, %s, %s, CURDATE())",
                (user_id, emotion, intensity, ",".join(tags), (req.content or "")[:200])
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # 静默，不影响主链路
# === ↑↑↑ 模块1结束 ↑↑↑ ===
