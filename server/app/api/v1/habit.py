# -*- coding: utf-8 -*-
"""
习惯管理 API - 习惯CRUD + 打卡 + 补卡 + 模板使用 + 鼓励语 + 成就 + 日记
"""
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.habit import TaskTemplate, Habit, Checkin, CheckinItem
from app.models.archive import CheckinDiary
from app.models.emotion import EmotionRecord
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.habit import HabitCreate, HabitUpdate, CheckinRequest, MakeupRequest
from app.middleware.auth import get_current_user
# 【四大新增模块联动】打卡 → 扭蛋币/世界AI反馈笔记/剧情解锁
from app.services.checkin_linkage import run_checkin_linkage
# 【习惯-伙伴融合】生命周期记忆 / 情绪差异化 / 总开关
from app.services.habit_companion_service import (
    HabitCompanionService as HCS,
    EVT_CREATE, EVT_CHECKIN, EVT_MISSED, EVT_PAUSE, EVT_RESUME,
)

router = APIRouter(prefix="/habit", tags=["习惯"])


def _try_habit_event(db, user_id, habit, event, role_key="", emotion="", note="", extra=None):
    """
    写习惯生命周期记忆：任何异常都不允许影响主流程（打卡/创建照常成功）
    """
    try:
        return HCS.write_event(db, user_id, habit, event, role_key=role_key,
                               emotion=emotion, note=note, extra=extra)
    except Exception as e:
        print(f"[habit-companion][WARN] 写记忆失败({event}): {type(e).__name__}: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return None


def _compute_streak(checkin_dates_desc):
    """
    计算连续打卡天数（基于 Checkin.checkin_date，不是 created_at）
    - 补卡场景下 created_at 是今天，但 checkin_date 是被补的日期，应用 checkin_date 才正确
    - 入参：按日期倒序排列的 checkin_date 列表（list[date]）
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    streak = 0
    if not checkin_dates_desc:
        return 0
    # 若今天没打卡则从昨天起算
    cursor = today if checkin_dates_desc[0] == today else yesterday
    for d in checkin_dates_desc:
        if d == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif d < cursor:
            break
    return streak


@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    """获取习惯模板列表"""
    templates = db.query(TaskTemplate).filter(TaskTemplate.status == 1).order_by(TaskTemplate.sort_order).all()
    return ResponseBase.success([{
        "id": t.id, "type": t.type, "name": t.name, "icon": t.icon,
        "description": t.description, "default_target": t.default_target,
        "breakdown": t.breakdown or [], "difficulty_targets": t.difficulty_targets or {},
    } for t in templates])


@router.get("/list")
def get_habits(user_id: int = Depends(get_current_user), db: Session = Depends(get_db),
               include_paused: int = 0):
    """include_paused: 是否包含已暂停的习惯 0否 1是（HTTP 下为 query 参数）"""
    """获取用户习惯列表（含 streak / can_makeup / last_checkin_date / is_paused）"""
    query = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    )
    # 【习惯-伙伴融合】默认不展示暂停中的习惯：暂停态不参与每日打卡校验
    if not include_paused:
        query = query.filter(Habit.is_paused == 0)
    habits = query.order_by(Habit.sort_order).all()

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 拉取所有已完成的 CheckinItem（用于 streak 计算），join Checkin 直接取 checkin_date
    # 注意: CheckinItem 模型上没有 checkin relationship, 不能访问 item.checkin, 否则 AttributeError
    all_items = db.query(CheckinItem, Checkin.checkin_date).filter(
        CheckinItem.user_id == user_id, CheckinItem.completed == 1
    ).join(Checkin, Checkin.id == CheckinItem.checkin_id).all()

    habit_dates = {}
    for item, checkin_date in all_items:
        habit_dates.setdefault(item.habit_id, []).append(checkin_date)

    today_checkin = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.checkin_date == today
    ).first()
    completed_items = {}
    if today_checkin:
        items = db.query(CheckinItem).filter(CheckinItem.checkin_id == today_checkin.id).all()
        completed_items = {item.habit_id: item.completed for item in items}

    result = []
    for h in habits:
        checkin_dates = sorted(set(habit_dates.get(h.id, [])), reverse=True)
        streak = _compute_streak(checkin_dates)
        last_checkin_date = checkin_dates[0] if checkin_dates else None
        # can_makeup：昨天漏打
        yesterday_checkin_item = db.query(CheckinItem).filter(
            CheckinItem.user_id == user_id, CheckinItem.habit_id == h.id
        ).join(Checkin, Checkin.id == CheckinItem.checkin_id).filter(
            Checkin.checkin_date == yesterday
        ).first()
        can_makeup = yesterday_checkin_item is None

        result.append({
            "id": h.id, "name": h.name, "icon": h.icon, "description": h.description,
            "target": h.target, "difficulty": h.difficulty, "color": h.color,
            "xp_value": h.xp_value, "reminder_time": h.reminder_time,
            "completed": completed_items.get(h.id, 0),
            "sort_order": h.sort_order,
            "streak": streak,
            "can_makeup": can_makeup,
            "last_checkin_date": str(last_checkin_date) if last_checkin_date else "",
            # ↓↓↓ 习惯-伙伴融合 ↓↓↓
            "is_paused": bool(h.is_paused),
            "paused_reason": h.paused_reason or "",
            "resume_count": int(h.resume_count or 0),
        })
    return ResponseBase.success(result)


@router.get("/today")
def get_today_habits(user_id: int = Depends(get_current_user), db: Session = Depends(get_db),
                     include_paused: int = 0):
    """获取今日习惯列表（精简版，复用 /list 逻辑）"""
    result = get_habits(user_id=user_id, db=db, include_paused=include_paused)
    # result 是 ResponseBase 实例，直接返回
    return result


@router.post("/create")
def create_habit(req: HabitCreate, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """创建习惯"""
    xp_map = {"easy": 10, "medium": 20, "hard": 30}
    habit = Habit(
        user_id=user_id,
        template_id=req.template_id,
        name=req.name, icon=req.icon, description=req.description,
        target=req.target, difficulty=req.difficulty, color=req.color,
        xp_value=xp_map.get(req.difficulty, 20),
        reminder_time=req.reminder_time,
        habit_type=req.habit_type or "other",
        ai_style=req.ai_style or "gentle",
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)

    # 【习惯-伙伴融合】节点1：创建习惯 → 写事件记忆（目标 + 期待获得的感受）
    _try_habit_event(
        db, user_id, habit, EVT_CREATE,
        role_key=getattr(req, "role_key", "") or "",
        extra={
            "target": req.target,
            "hope": getattr(req, "hope", "") or req.description or "",
        },
    )

    return ResponseBase.success({
        "id": habit.id,
        "name": habit.name,
        "companion_reply": HCS.build_create_text(habit),
    })


@router.put("/update/{habit_id}")
def update_habit(habit_id: int, req: HabitUpdate,
                 user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新习惯"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    if req.difficulty:
        xp_map = {"easy": 10, "medium": 20, "hard": 30}
        habit.xp_value = xp_map.get(req.difficulty, 20)
    db.commit()
    return ResponseBase.success({"id": habit.id})


@router.delete("/delete/{habit_id}")
def delete_habit(habit_id: int, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """删除习惯(软删除)"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)
    habit.status = 0
    db.commit()
    return ResponseBase.success({"id": habit_id})


@router.post("/checkin")
def checkin(req: CheckinRequest, user_id: int = Depends(get_current_user),
            db: Session = Depends(get_db)):
    """打卡"""
    habit = db.query(Habit).filter(Habit.id == req.habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    # 【习惯-伙伴融合】暂停中的习惯不参与打卡校验 —— 数据保留，只是先歇着
    if habit.is_paused:
        return ResponseBase.error(
            f"「{habit.name}」正在休息中，不参与今日打卡。想重新开始的话我可以陪你。", 409
        )

    today = date.today()

    # ↓↓↓ 安全合规批次：打卡幂等防重（同用户同习惯同一天，并发窗口内重复点击只生效一次） ↓↓↓
    from app.utils import idempotency as idem
    from app.utils.content_security import ContentSecurity
    if not idem.try_acquire(idem.checkin_key(user_id, req.habit_id, today.isoformat()),
                            ttl_seconds=30):
        return ResponseBase.error("打卡处理中，请勿重复点击", 429)
    # 打卡感想做一次内容安全校验（可选字段，为空直接放行）
    if (req.note or "").strip():
        _sec = ContentSecurity.check_user_text(req.note, max_length=500)
        if not _sec["ok"]:
            return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    # 获取或创建今日打卡主记录
    checkin = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.checkin_date == today
    ).first()
    if not checkin:
        # 统计今日习惯总数
        total = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == 1).count()
        checkin = Checkin(
            user_id=user_id, checkin_date=today,
            total_habits=total, completed_count=0, completion_rate=0,
            streak_days=0,
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)

    # 【修复】习惯总数只在打卡主表创建时写过一次；若用户当天新增/删除习惯，
    # 分母会过期导致完成率超过 100%，这里按当前生效习惯数刷新
    current_total = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    ).count()
    if current_total != checkin.total_habits:
        checkin.total_habits = current_total

    # 检查是否已打卡
    existing = db.query(CheckinItem).filter(
        CheckinItem.checkin_id == checkin.id, CheckinItem.habit_id == req.habit_id
    ).first()
    if existing:
        return ResponseBase.error("今日已打卡", 409)

    # 创建打卡明细
    item = CheckinItem(
        checkin_id=checkin.id, user_id=user_id, habit_id=req.habit_id,
        completed=1, note=req.note, difficulty_rating=req.difficulty_rating,
        duration_min=req.duration_min,
    )
    db.add(item)
    # 更新主记录
    checkin.completed_count += 1
    checkin.completion_rate = min(100.0, round(checkin.completed_count / max(checkin.total_habits, 1) * 100, 2))
    db.commit()
    db.refresh(item)

    # ===== 【四大新增模块联动】打卡成功后：发扭蛋币 + 世界AI反馈笔记 + 剧情解锁 =====
    # run_checkin_linkage 内部自带 try/except 隔离，联动失败不影响打卡结果
    user = db.query(User).filter(User.id == user_id).first()
    linkage = run_checkin_linkage(
        db, user_id, habit_name=habit.name, habit_id=habit.id,
        user_name=(user.nickname or user.username) if user else "",
    )

    # ===== 【习惯-伙伴融合】节点2：打卡成功 =====
    # 1) 情绪打通：优先用前端传的 emotion_id 查 emotion_records，
    #    其次按 emotion 字段找最近一条记录，最后才用前端直接给的情绪值
    emotion = (req.emotion or "").strip()
    emotion_record = None
    if req.emotion_id:
        emotion_record = db.query(EmotionRecord).filter(
            EmotionRecord.id == req.emotion_id, EmotionRecord.user_id == user_id
        ).first()
    if emotion_record is None and emotion:
        emotion_record = db.query(EmotionRecord).filter(
            EmotionRecord.user_id == user_id,
            EmotionRecord.emotion == emotion,
            EmotionRecord.record_date >= today - timedelta(days=1),
        ).order_by(EmotionRecord.id.desc()).first()
    if emotion_record is None and not emotion:
        emotion_record = HCS.latest_emotion(db, user_id, habit_id=habit.id)
    if emotion_record is not None:
        emotion = emotion_record.emotion or emotion
    if emotion:
        habit.emotion_status = emotion

    # 1.5) 【习惯-伙伴融合】情绪落库：打卡时选的情绪写进 emotion_records
    #      只补不覆盖——用户自己在情绪页记过的不动；同一天同一情绪不重复写，避免污染情绪统计
    if emotion and emotion_record is None:
        try:
            existed = db.query(EmotionRecord).filter(
                EmotionRecord.user_id == user_id,
                EmotionRecord.emotion == emotion,
                EmotionRecord.record_date == today,
            ).first()
            if existed:
                emotion_record = existed
            else:
                emotion_record = EmotionRecord(
                    user_id=user_id,
                    habit_id=habit.id,
                    emotion=emotion,
                    intensity=5,
                    description=(req.note or "")[:200],
                    record_date=today,
                )
                db.add(emotion_record)
                db.flush()
        except Exception as e:
            print(f"[habit-companion][WARN] 情绪落库失败: {type(e).__name__}: {e}")

    # 2) 连续天数（沿用既有算法，失败不影响主流程）
    try:
        from app.services.habit_ai_service import HabitAIService
        continuous_day = HabitAIService.calculate_continuous_days(db, user_id, habit.id)
        habit.continuous_day = continuous_day
        db.commit()
    except Exception as e:
        print(f"[habit-companion][WARN] 连续天数计算失败: {type(e).__name__}: {e}")
        continuous_day = int(habit.continuous_day or 0)

    # 3) 写事件记忆（含本次情绪）
    _try_habit_event(
        db, user_id, habit, EVT_CHECKIN,
        role_key=req.role_key or "",
        emotion=emotion, note=req.note,
        extra={
            "continuous_day": continuous_day,
            "emotion_id": emotion_record.id if emotion_record else 0,
        },
    )

    # 4) 情绪差异化鼓励（禁止统一话术 / 禁止说教打气）
    companion_reply = HCS.build_checkin_encouragement(
        habit, emotion=emotion, continuous_day=continuous_day, note=req.note
    )

    return ResponseBase.success({
        "id": item.id, "habit_id": req.habit_id, "completed": 1,
        "note": req.note, "completion_rate": float(checkin.completion_rate),
        "linkage": linkage,  # 新增字段：前端可展示 "+10扭蛋币/剧情解锁" 提示
        # ↓↓↓ 习惯-伙伴融合 ↓↓↓
        "emotion": emotion,
        "continuous_day": continuous_day,
        "companion_reply": companion_reply,
        "habit_paused": bool(habit.is_paused),
        # ↓↓↓ 新增（2026-10-28 打卡上下文延续）：把本次事件交给聊天页 ↓↓↓
        # 前端把它挂在 AI 回复气泡上，用户点「继续聊聊这件事」时原样回传 /chat/send，
        # 于是这条回复不再是「一句一次性鼓励」，而是一段可延续对话的起点。
        "chat_context": HCS.build_chat_context(
            habit, EVT_CHECKIN, emotion, item_id=item.id, note=req.note or ""
        ),
    })


@router.post("/uncheckin/{habit_id}")
def uncheckin(habit_id: int, user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """取消打卡"""
    today = date.today()
    checkin = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.checkin_date == today
    ).first()
    if not checkin:
        return ResponseBase.error("今日无打卡记录", 404)

    item = db.query(CheckinItem).filter(
        CheckinItem.checkin_id == checkin.id, CheckinItem.habit_id == habit_id
    ).first()
    if not item:
        return ResponseBase.error("未找到打卡记录", 404)

    db.delete(item)
    checkin.completed_count = max(checkin.completed_count - 1, 0)
    checkin.completion_rate = min(100.0, round(checkin.completed_count / max(checkin.total_habits, 1) * 100, 2))
    db.commit()

    # ↓↓↓ 安全合规批次：取消打卡后释放幂等 key，允许立刻重新打卡 ↓↓↓
    try:
        from app.utils import idempotency as idem
        idem.release(idem.checkin_key(user_id, habit_id, today.isoformat()))
    except Exception:
        pass
    # ↑↑↑ 新增结束 ↑↑↑

    return ResponseBase.success({"habit_id": habit_id, "completed": 0})


@router.post("/checkin/makeup")
def checkin_makeup(req: MakeupRequest, user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """补卡：补昨日打卡，带宽限校验"""
    today = date.today()
    # 解析 makeup_date（None 时默认昨天）
    if req.makeup_date:
        try:
            makeup_date = datetime.strptime(req.makeup_date, "%Y-%m-%d").date()
        except ValueError:
            return ResponseBase.error("makeup_date 格式应为 YYYY-MM-DD", 400)
    else:
        makeup_date = today - timedelta(days=1)
    # 宽限校验：仅允许补昨日
    if (today - makeup_date).days != 1:
        return ResponseBase.error("仅可补昨日打卡", 400)

    habit = db.query(Habit).filter(Habit.id == req.habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    checkin = db.query(Checkin).filter(
        Checkin.user_id == user_id, Checkin.checkin_date == makeup_date
    ).first()
    if not checkin:
        total = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == 1).count()
        checkin = Checkin(
            user_id=user_id, checkin_date=makeup_date,
            total_habits=total, completed_count=0, completion_rate=0, streak_days=0,
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)

    # 【修复】补卡同样按当前生效习惯数刷新分母，避免完成率超过 100%
    current_total = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    ).count()
    if current_total != checkin.total_habits:
        checkin.total_habits = current_total

    existing = db.query(CheckinItem).filter(
        CheckinItem.checkin_id == checkin.id, CheckinItem.habit_id == req.habit_id
    ).first()
    if existing:
        return ResponseBase.error("该日期已打卡", 409)

    item = CheckinItem(
        checkin_id=checkin.id, user_id=user_id,
        habit_id=req.habit_id, completed=1, note=req.note,
    )
    db.add(item)
    checkin.completed_count += 1
    checkin.completion_rate = min(100.0, round(checkin.completed_count / max(checkin.total_habits, 1) * 100, 2))
    db.commit()
    return ResponseBase.success({"habit_id": req.habit_id, "makeup_date": str(makeup_date)})


@router.post("/templates/{template_id}/use")
def use_template(template_id: int, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """使用模板创建习惯"""
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not template:
        return ResponseBase.error("模板不存在", 404)
    habit = Habit(
        user_id=user_id, template_id=template_id,
        name=template.name, icon=template.icon,
        description=template.description, target=template.default_target,
        difficulty="medium", color="", xp_value=20,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return ResponseBase.success({"id": habit.id, "name": habit.name})


@router.post("/encouragement")
def get_encouragement(data: dict = Body(...), user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    AI 反馈语（习惯-伙伴融合版）

    - 按情绪差异化输出，不同情绪不同话，禁用统一固定话术
    - 禁止说教、禁止「加油/努力」式打气（出口前统一过话术安全带）
    - action: checkin 完成 / missed 未完成 / pause 暂停 / resume 重启
    """
    habit_id = int(data.get("habit_id") or 0)
    habit_name = (data.get("habit_name") or "").strip()
    action = data.get("action", "checkin")
    emotion = (data.get("emotion") or "").strip()
    role_key = data.get("role_key") or ""

    habit = None
    if habit_id:
        habit = db.query(Habit).filter(
            Habit.id == habit_id, Habit.user_id == user_id
        ).first()

    if habit is None:
        # 没有对应习惯时，按动作给通用伙伴口吻（不再是「太棒了…继续保持」）
        generic = {
            "checkin": "做完了。今天这一步就算落下了。",
            "missed": "今天没做成。没什么，明天的事明天再说。",
            "pause": "好，先放一放。想拿起来的时候随时叫我。",
            "resume": "你又把它捡起来了。这次我们不设目标。",
        }.get(action, "我在呢。")
        return ResponseBase.success({
            "message": HCS.sanitize_partner_text(generic),
            "action": action, "habit_id": 0, "emotion": emotion,
        })

    if action == "missed":
        msg = HCS.build_missed_text(habit, emotion=emotion)
        _try_habit_event(db, user_id, habit, EVT_MISSED, role_key=role_key, emotion=emotion)
    elif action == "pause":
        msg = HCS.build_pause_text(habit)
    elif action == "resume":
        msg = HCS.build_resume_text(habit)
    else:
        try:
            from app.services.habit_ai_service import HabitAIService
            day = HabitAIService.calculate_continuous_days(db, user_id, habit.id)
        except Exception:
            day = int(habit.continuous_day or 0)
        msg = HCS.build_checkin_encouragement(habit, emotion=emotion, continuous_day=day)

    return ResponseBase.success({
        "message": msg,
        "action": action,
        "habit_id": habit.id,
        "habit_name": habit.name,
        "emotion": emotion,
        # ↓↓↓ 新增（2026-10-28）：AI 反馈语同样带上下文，可一键接着聊 ↓↓↓
        "chat_context": HCS.build_chat_context(
            habit,
            {"checkin": EVT_CHECKIN, "missed": EVT_MISSED,
             "pause": EVT_PAUSE, "resume": EVT_RESUME}.get(action, EVT_CHECKIN),
            emotion,
        ),
    })


# ============================================================
# 习惯-伙伴融合：暂停 / 重启 / 未完成 / 完整过往
# ============================================================

@router.post("/{habit_id}/pause")
def pause_habit(habit_id: int, data: dict = Body(default={}),
                user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    暂停习惯（数据保留，不删除）

    暂停态语义：不参与每日打卡校验、不推送习惯提醒、历史数据全部保留。
    """
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)
    if habit.is_paused:
        return ResponseBase.success({
            "habit_id": habit_id, "is_paused": True, "changed": False,
            "companion_reply": f"「{habit.name}」已经在休息了，不用再停一次。",
        })

    reason = (data.get("reason") or "").strip()
    role_key = data.get("role_key") or ""

    habit.is_paused = 1
    habit.paused_at = datetime.now()
    habit.paused_reason = reason[:100]
    db.commit()

    # 节点3：暂停 → 写事件记忆（情绪接纳优先，标记为照顾自己的决定）
    _try_habit_event(db, user_id, habit, EVT_PAUSE, role_key=role_key,
                     emotion=(data.get("emotion") or "").strip(),
                     extra={"reason": reason or "没说原因，就是想先放一放"})

    # 主动暂停 = 自我接纳，授予徽章
    try:
        HCS.on_paused(db, user_id)
    except Exception as e:
        print(f"[habit-companion][WARN] 自我接纳徽章失败: {type(e).__name__}: {e}")

    return ResponseBase.success({
        "habit_id": habit_id,
        "is_paused": True,
        "changed": True,
        "paused_at": habit.paused_at.strftime("%Y-%m-%d %H:%M") if habit.paused_at else "",
        "companion_reply": HCS.build_pause_text(habit),
        # ↓↓↓ 新增（2026-10-28）：暂停也可以接着聊（基调=认可自我照顾） ↓↓↓
        "chat_context": HCS.build_chat_context(habit, EVT_PAUSE,
                                               (data.get("emotion") or "").strip()),
    })


@router.post("/{habit_id}/resume")
def resume_habit(habit_id: int, data: dict = Body(default={}),
                 user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """重启习惯（不新建习惯，沿用原记录）"""
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)
    if not habit.is_paused:
        return ResponseBase.success({
            "habit_id": habit_id, "is_paused": False, "changed": False,
            "companion_reply": f"「{habit.name}」还在进行中呢，不用重启。",
        })

    role_key = data.get("role_key") or ""
    emotion = (data.get("emotion") or "").strip()

    habit.is_paused = 0
    habit.resume_count = int(habit.resume_count or 0) + 1
    habit.last_resume_at = datetime.now()
    habit.paused_reason = ""
    db.commit()

    # 节点4：重启 → 写事件记忆（记录重新拾起，不追问中断原因）
    _try_habit_event(db, user_id, habit, EVT_RESUME, role_key=role_key, emotion=emotion,
                     extra={"resume_count": habit.resume_count})

    # 重启 = 重新出发，授予徽章
    try:
        HCS.on_resumed(db, user_id)
    except Exception as e:
        print(f"[habit-companion][WARN] 重启徽章失败: {type(e).__name__}: {e}")

    return ResponseBase.success({
        "habit_id": habit_id,
        "is_paused": False,
        "changed": True,
        "resume_count": habit.resume_count,
        "companion_reply": HCS.build_resume_text(habit),
        # ↓↓↓ 新增（2026-10-28） ↓↓↓
        "chat_context": HCS.build_chat_context(habit, EVT_RESUME, emotion),
    })


@router.post("/{habit_id}/missed")
def mark_missed(habit_id: int, data: dict = Body(default={}),
                user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    上报「今天没完成」（区别于暂停：不落 is_paused，只记一次事件）
    """
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)

    emotion = (data.get("emotion") or "").strip()
    role_key = data.get("role_key") or ""
    _try_habit_event(db, user_id, habit, EVT_MISSED, role_key=role_key, emotion=emotion)
    return ResponseBase.success({
        "habit_id": habit_id,
        "companion_reply": HCS.build_missed_text(habit, emotion=emotion),
        # ↓↓↓ 新增（2026-10-28）：未完成也可以接着聊（基调=接纳共情，不催补卡） ↓↓↓
        "chat_context": HCS.build_chat_context(habit, EVT_MISSED, emotion),
    })


@router.get("/{habit_id}/story")
def habit_story(habit_id: int, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """
    习惯的完整过往：开启时间 / 中断经历 / 重启经历 / 关键记忆
    供 AI 对话时读取，保证「不失忆」
    """
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return ResponseBase.error("习惯不存在", 404)
    return ResponseBase.success(HCS.habit_story(db, user_id, habit))


@router.get("/companion/setting")
def get_companion_setting(user_id: int = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """读取伙伴相处设置（含【允许伙伴和我聊习惯相关的事】总开关）"""
    row = HCS.get_setting(db, user_id)
    ratio, n = HCS.recent_negative_ratio(db, user_id, days=7)
    muted_until = row.habit_proactive_muted_until
    return ResponseBase.success({
        "allow_habit_topic": bool(row.allow_habit_topic),
        "habit_proactive_muted_until": muted_until.strftime("%Y-%m-%d %H:%M") if muted_until else "",
        "habit_topic_off_at": row.habit_topic_off_at.strftime("%Y-%m-%d %H:%M") if row.habit_topic_off_at else "",
        "negative_ratio_7d": ratio,
        "emotion_sample_count": n,
        "proactive_cooldown_hours": HCS.habit_proactive_cooldown_hours(db, user_id),
    })


@router.put("/companion/setting")
def update_companion_setting(data: dict = Body(...),
                             user_id: int = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    """
    修改伙伴相处设置
    body: { "allow_habit_topic": true/false }
    关闭后：拦截全部习惯类主动消息，自由聊天里也不主动提起习惯
    """
    if "allow_habit_topic" not in data:
        return ResponseBase.error("缺少 allow_habit_topic", 400)
    row = HCS.set_allow_habit_topic(db, user_id, bool(data.get("allow_habit_topic")))
    return ResponseBase.success({
        "allow_habit_topic": bool(row.allow_habit_topic),
        "message": "好，以后我不主动跟你聊习惯的事。" if not row.allow_habit_topic
                   else "好，习惯的事我还是可以陪你聊聊。",
    })


# ↓↓↓ 新增（2026-10-28 需求5 / 需求7 / 需求8） ↓↓↓
@router.post("/topic/mute")
def mute_habit_topic(data: dict = Body(default={}),
                     user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """
    把某条习惯短期静默（默认 3 天）

    触发场景：聊天页打卡气泡下的「✅先放一放」，或用户说出「先不说这个了」。
    静默期内：不挂载会话上下文、不主动提起这条习惯。
    body: { "habit_id": 12, "days": 3 }  —— days 省略时用默认 3 天
    """
    habit_id = int(data.get("habit_id") or 0)
    if not habit_id:
        return ResponseBase.error("缺少 habit_id", 400)
    days = data.get("days")
    days = HCS.HABIT_MUTE_DAYS if days is None else max(0, int(days))
    HCS.mute_habit_topic(db, user_id, habit_id, days=days)
    return ResponseBase.success({
        "habit_id": habit_id,
        "days": days,
        "muted": days > 0,
        # 需求8 指定的固定回应：前端可直接把这句当作 AI 的回复气泡渲染
        "reply": HCS.EXIT_REPLY,
    })


@router.post("/topic/unmute")
def unmute_habit_topic(data: dict = Body(default={}),
                       user_id: int = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """解除某条习惯的静默（用户主动重新聊起它时调用）"""
    habit_id = int(data.get("habit_id") or 0)
    if not habit_id:
        return ResponseBase.error("缺少 habit_id", 400)
    HCS.clear_habit_mute(db, user_id, habit_id)
    return ResponseBase.success({"habit_id": habit_id, "muted": False})
# ↑↑↑ 新增结束 ↑↑↑


@router.post("/verbal/parse")
def verbal_parse(data: dict = Body(...), user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """
    聊天语义识别：判断这句话是不是在口头打卡
    只做识别与候选，绝不擅自打卡
    """
    text = (data.get("text") or "").strip()
    if not HCS.looks_like_verbal_checkin(text):
        return ResponseBase.success({"is_checkin": False, "candidates": [], "confirm_question": ""})

    hits = HCS.match_habit_by_text(db, user_id, text)
    return ResponseBase.success({
        "is_checkin": True,
        "candidates": [{"habit_id": h.id, "habit_name": h.name} for h in hits],
        "confirm_question": HCS.build_confirm_question(hits),
    })


@router.post("/verbal/confirm")
def verbal_confirm(data: dict = Body(...), user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """
    口头打卡确认：用户确认后才真正打卡，事件同步写入长效记忆
    body: { "habit_id": 1, "confirmed": true, "note": "", "emotion": "", "role_key": "" }
    """
    if not data.get("confirmed"):
        return ResponseBase.success({"checked": False, "message": "那先不记，等你说是哪个我再帮你记上。"})

    habit_id = int(data.get("habit_id") or 0)
    if not habit_id:
        return ResponseBase.error("缺少 habit_id", 400)

    req = CheckinRequest(
        habit_id=habit_id,
        note=(data.get("note") or "")[:500],
        emotion=(data.get("emotion") or ""),
        role_key=(data.get("role_key") or ""),
    )
    result = checkin(req=req, user_id=user_id, db=db)
    if getattr(result, "code", 200) != 200:
        # 今日已打卡 / 习惯暂停中等：如实告诉 AI，不粉饰
        return ResponseBase.success({
            "checked": False,
            "checkin": None,
            "message": getattr(result, "message", "没能记上"),
            "code": result.code,
        })
    payload = result.data if hasattr(result, "data") else None
    return ResponseBase.success({
        "checked": True,
        "checkin": payload,
        "message": (payload or {}).get("companion_reply", "记上了。"),
    })


@router.get("/{habit_id}/world-fragment")
def world_fragment(habit_id: int, user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """把这段习惯经历改写成世界观剧情碎片素材（P2-3，只出素材不自动发布）"""
    frag = HCS.build_world_fragment(db, user_id, habit_id)
    if not frag:
        return ResponseBase.error("习惯不存在", 404)
    return ResponseBase.success(frag)


@router.get("/{habit_id}/achievements")
def get_achievements(habit_id: int, user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """获取成就列表"""
    items_count = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id, CheckinItem.habit_id == habit_id,
        CheckinItem.completed == 1
    ).count()
    return ResponseBase.success([
        {"name": "坚持一周", "icon": "🌟", "unlocked": items_count >= 7},
        {"name": "坚持一月", "icon": "🏆", "unlocked": items_count >= 30},
    ])


@router.post("/{habit_id}/achievements/check")
def check_achievements(habit_id: int, data: dict = Body(...),
                       user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """检查成就解锁"""
    items_count = db.query(CheckinItem).filter(
        CheckinItem.user_id == user_id, CheckinItem.habit_id == habit_id,
        CheckinItem.completed == 1
    ).count()
    unlocked = []
    if items_count >= 7:
        unlocked.append({"name": "坚持一周", "icon": "🌟"})
    if items_count >= 30:
        unlocked.append({"name": "坚持一月", "icon": "🏆"})
    return ResponseBase.success({"unlocked": unlocked, "total_checkins": items_count})


@router.post("/{habit_id}/checkin/diary")
def save_diary(habit_id: int, data: dict = Body(...),
               user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """保存用户打卡日记（使用 CheckinDiary 表，与 habit-ai/diary 的 AI 生成不同）

    【习惯-伙伴融合】body 可带 emotion：打卡弹窗里选的当前心情，落进 emotion_records。
    同一天同一情绪不重复写，避免污染「近期负面情绪占比」这类统计。
    """
    diary = CheckinDiary(
        user_id=user_id,
        checkin_id=data.get("checkin_id", 0),
        habit_id=habit_id,
        content=data.get("content", ""),
    )
    db.add(diary)
    db.commit()
    db.refresh(diary)

    emotion = (data.get("emotion") or "").strip()
    emotion_id = 0
    if emotion:
        try:
            today = date.today()
            existed = db.query(EmotionRecord).filter(
                EmotionRecord.user_id == user_id,
                EmotionRecord.emotion == emotion,
                EmotionRecord.record_date == today,
            ).first()
            if existed:
                emotion_id = existed.id
            else:
                rec = EmotionRecord(
                    user_id=user_id, habit_id=habit_id, emotion=emotion,
                    intensity=int(data.get("intensity") or 5),
                    description=(data.get("content") or "")[:200],
                    record_date=today,
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                emotion_id = rec.id
        except Exception as e:
            print(f"[habit-companion][WARN] 日记情绪落库失败: {type(e).__name__}: {e}")

    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    # ↓↓↓ 新增（2026-10-28 需求4）：留言里选了情绪 → 回复按情绪基调走，并把这次事件交给聊天页 ↓↓↓
    companion_reply = ""
    chat_context = None
    if habit is not None:
        companion_reply = HCS.build_event_reply(
            EVT_CHECKIN, habit, emotion=emotion, note=(data.get("content") or "")[:60]
        )
        chat_context = HCS.build_chat_context(
            habit, EVT_CHECKIN, emotion, note=(data.get("content") or "")[:60]
        )
    return ResponseBase.success({
        "id": diary.id,
        "emotion_id": emotion_id,
        "emotion": emotion,
        "companion_reply": companion_reply,
        "chat_context": chat_context,
    })


@router.get("/{habit_id}/checkin/diary")
def get_diaries(habit_id: int, user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """获取用户日记列表"""
    query = db.query(CheckinDiary).filter(CheckinDiary.user_id == user_id)
    if habit_id:
        query = query.filter(CheckinDiary.habit_id == habit_id)
    diaries = query.order_by(CheckinDiary.id.desc()).limit(50).all()
    return ResponseBase.success([{
        "id": d.id, "checkin_id": d.checkin_id, "habit_id": d.habit_id,
        "content": d.content, "created_at": str(d.created_at) if d.created_at else "",
    } for d in diaries])
