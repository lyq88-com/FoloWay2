# -*- coding: utf-8 -*-
"""
日程提醒 API（模块2）
端点：
  POST   /schedule/create           创建日程
  GET    /schedule/list             按日期/月份查日程
  GET    /schedule/detail/{id}      详情
  PUT    /schedule/update/{id}      更新
  DELETE /schedule/delete/{id}      删除
  POST   /schedule/ai-generate      AI伙伴根据打卡情况生成建议日程
  POST   /schedule/complete/{id}    完成日程（绑定习惯则自动打卡）
  GET    /schedule/remind/scan      扫描到点提醒（前端定时/回前台时调用，AI据此主动发消息）
"""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schedule import Schedule
from app.models.habit import Habit, Checkin, CheckinItem
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleAiGenerate
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/schedule", tags=["日程提醒"])


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _serialize(s: Schedule) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "schedule_date": str(s.schedule_date),
        "start_time": s.start_time,
        "end_time": s.end_time,
        "habit_id": s.habit_id,
        "is_done": s.is_done,
        "source": s.source,
        "remind_minutes": s.remind_minutes,
    }


# ============ 1. 创建日程 ============
@router.post("/create")
def create_schedule(payload: ScheduleCreate,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    sched_date = _parse_date(payload.schedule_date)
    # 绑定的习惯必须属于当前用户
    if payload.habit_id:
        habit = db.query(Habit).filter(
            Habit.id == payload.habit_id, Habit.user_id == user_id
        ).first()
        if not habit:
            return ResponseBase.error("绑定的习惯不存在", 400)

    s = Schedule(
        user_id=user_id, title=payload.title, description=payload.description,
        schedule_date=sched_date, start_time=payload.start_time, end_time=payload.end_time,
        habit_id=payload.habit_id, remind_minutes=payload.remind_minutes,
        source="manual", status=1,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ResponseBase.success(_serialize(s))


# ============ 2. 查询日程（单日 或 整月） ============
@router.get("/list")
def list_schedules(day: str = Query("", description="查单日 YYYY-MM-DD"),
                   month: str = Query("", description="查整月 YYYY-MM"),
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    q = db.query(Schedule).filter(Schedule.user_id == user_id, Schedule.status == 1)
    if day:
        d = _parse_date(day)
        q = q.filter(Schedule.schedule_date == d).order_by(Schedule.start_time.asc())
    elif month:
        first = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        # 下个月 1 号
        if first.month == 12:
            nxt = first.replace(year=first.year + 1, month=1)
        else:
            nxt = first.replace(month=first.month + 1)
        q = q.filter(Schedule.schedule_date >= first, Schedule.schedule_date < nxt) \
             .order_by(Schedule.schedule_date.asc(), Schedule.start_time.asc())
    else:
        # 默认：今天
        q = q.filter(Schedule.schedule_date == date.today()).order_by(Schedule.start_time.asc())
    return ResponseBase.success([_serialize(s) for s in q.all()])


# ============ 3. 详情 ============
@router.get("/detail/{schedule_id}")
def detail_schedule(schedule_id: int,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id, Schedule.user_id == user_id, Schedule.status == 1
    ).first()
    if not s:
        return ResponseBase.error("日程不存在", 404)
    return ResponseBase.success(_serialize(s))


# ============ 4. 更新 ============
@router.put("/update/{schedule_id}")
def update_schedule(schedule_id: int,
                    payload: ScheduleUpdate,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id, Schedule.user_id == user_id, Schedule.status == 1
    ).first()
    if not s:
        return ResponseBase.error("日程不存在", 404)

    data = payload.model_dump(exclude_none=True)
    if "schedule_date" in data:
        data["schedule_date"] = _parse_date(data["schedule_date"])
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return ResponseBase.success(_serialize(s))


# ============ 5. 删除 ============
@router.delete("/delete/{schedule_id}")
def delete_schedule(schedule_id: int,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id, Schedule.user_id == user_id, Schedule.status == 1
    ).first()
    if not s:
        return ResponseBase.error("日程不存在", 404)
    s.status = 0
    db.commit()
    return ResponseBase.success({"id": schedule_id})


# ============ 6. AI 伙伴生成建议日程（根据用户习惯 + 打卡情况） ============
@router.post("/ai-generate")
def ai_generate(payload: ScheduleAiGenerate,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """
    差异化创新：AI 读取用户启用的习惯，自动排出当天建议日程。
    - 有打卡记录/连续打卡的习惯安排在更合适的时段；
    - 已存在同时段日程则跳过，避免重复。
    """
    target_day = _parse_date(payload.for_date)
    habits = db.query(Habit).filter(
        Habit.user_id == user_id, Habit.status == 1
    ).order_by(Habit.sort_order.asc()).all()
    if not habits:
        return ResponseBase.error("你还没有习惯，先去添加习惯吧", 400)

    # 建议时段模板（按习惯顺序依次排）
    time_slots = [
        ("07:00", "07:30"), ("12:30", "13:00"), ("18:00", "18:30"),
        ("19:30", "20:00"), ("21:00", "21:30"), ("06:30", "07:00"),
    ]
    # 已存在日程的标题（防重复生成）
    existed = {s.title for s in db.query(Schedule).filter(
        Schedule.user_id == user_id, Schedule.schedule_date == target_day,
        Schedule.status == 1
    ).all()}

    created = []
    for idx, h in enumerate(habits):
        start, end = time_slots[idx % len(time_slots)]
        title = f"{h.name}（AI建议）"
        if title in existed:
            continue
        s = Schedule(
            user_id=user_id, title=title,
            description=f"AI伙伴根据你的「{h.name}」习惯安排，完成打卡会给你鼓励~",
            schedule_date=target_day, start_time=start, end_time=end,
            habit_id=h.id, source="ai", remind_minutes=10, status=1,
        )
        db.add(s)
        created.append(s)
    db.commit()
    for s in created:
        db.refresh(s)
    return ResponseBase.success({
        "list": [_serialize(s) for s in created],
        "tip": f"已为你生成 {len(created)} 条建议日程",
    })


# ============ 7. 完成日程（绑定习惯则自动打卡，数据互通） ============
@router.post("/complete/{schedule_id}")
def complete_schedule(schedule_id: int,
                      user_id: int = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(
        Schedule.id == schedule_id, Schedule.user_id == user_id, Schedule.status == 1
    ).first()
    if not s:
        return ResponseBase.error("日程不存在", 404)

    auto_checkin = False
    # 绑定了习惯：完成日程 → 自动打卡（仅当日日程且未打卡时）
    if s.habit_id and s.schedule_date == date.today():
        today_checkin = db.query(Checkin).filter(
            Checkin.user_id == user_id, Checkin.checkin_date == date.today()
        ).first()
        already = False
        if today_checkin:
            already = db.query(CheckinItem).filter(
                CheckinItem.checkin_id == today_checkin.id,
                CheckinItem.habit_id == s.habit_id,
            ).first() is not None
        if not already:
            # 复用打卡主逻辑：必要时创建 Checkin
            if not today_checkin:
                total = db.query(Habit).filter(
                    Habit.user_id == user_id, Habit.status == 1
                ).count()
                today_checkin = Checkin(
                    user_id=user_id, checkin_date=date.today(),
                    total_habits=total, completed_count=0, completion_rate=0, streak_days=0,
                )
                db.add(today_checkin)
                db.commit()
                db.refresh(today_checkin)
            item = CheckinItem(
                checkin_id=today_checkin.id, user_id=user_id,
                habit_id=s.habit_id, completed=1,
            )
            db.add(item)
            today_checkin.completed_count += 1
            today_checkin.completion_rate = round(
                today_checkin.completed_count / max(today_checkin.total_habits, 1) * 100, 2
            )
            auto_checkin = True

    s.is_done = 1
    db.commit()
    return ResponseBase.success({
        "id": s.id, "is_done": 1, "auto_checkin": auto_checkin,
    })


# ============ 8. 提醒扫描：返回到点该提醒的日程（AI 主动发消息依据） ============
@router.get("/remind/scan")
def remind_scan(user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """
    前端在回前台/定时轮询时调用：
    找今天「开始时间 - 提前提醒 ≤ 现在」且未提醒、未完成的日程，
    标记 reminded 并返回，前端据此让 AI 伙伴主动发消息提醒。
    """
    now = datetime.now()
    today = now.date()
    schedules = db.query(Schedule).filter(
        Schedule.user_id == user_id, Schedule.schedule_date == today,
        Schedule.status == 1, Schedule.reminded == 0, Schedule.is_done == 0,
    ).all()

    due = []
    for s in schedules:
        try:
            hh, mm = map(int, s.start_time.split(":"))
        except ValueError:
            continue
        due_dt = datetime(today.year, today.month, today.day, hh, mm) \
            - timedelta(minutes=s.remind_minutes)
        if now >= due_dt:
            s.reminded = 1
            due.append(_serialize(s))
    db.commit()

    # 组装 AI 伙伴提醒消息文本（贴合陪伴定位）
    reminders = []
    for s in due:
        reminders.append({
            "schedule": s,
            "ai_message": f"提醒你一下~「{s['title']}」{s['start_time']} 就要开始了，我陪着你，慢慢来。",
        })
    return ResponseBase.success(reminders)
