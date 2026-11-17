# -*- coding: utf-8 -*-
"""
admin 模块服务层：把旧表数据整理成管理后台需要的结构。

约定：
  - 只读旧表（users/habits/checkins/chat_messages/...），写入仅限 admin_logs / admin_reviews；
  - 返回字段统一 camelCase，与前端 admin/src/mock/index.js 的契约保持一致。
"""
from datetime import date, datetime, timedelta

from sqlalchemy import func

from app.models.user import User
from app.models.habit import Habit, Checkin, CheckinItem, TaskTemplate
from app.models.chat import AIRole, AIRoleAsset, ChatMessage, ChatSession
from app.models.achievement import Badge, UserBadge
from app.models.archive import CheckinDiary
from app.modules.admin.models import AdminLog, AdminReview

LEVELS = [
    (100, "自律传奇"),
    (60, "习惯大师"),
    (30, "坚持达人"),
    (10, "自律学徒"),
    (0, "习惯新手"),
]

ROLE_TYPE_LABEL = {
    "cute": "可爱型",
    "gentle": "温柔型",
    "serious": "严肃型",
    "energetic": "活力型",
}

CHART_COLORS = ["#4FC3F7", "#FF6B6B", "#FFD93D", "#4DD0E1", "#7986CB", "#BA68C8", "#81C784", "#78909C"]


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dt, (datetime, date)) else ""


def level_of(total_checkins: int):
    for threshold, name in LEVELS:
        if total_checkins >= threshold:
            return threshold, name
    return 0, "习惯新手"


def add_log(db, admin, action, target_type="", target_id=0, detail="", ip=""):
    """写一条操作日志（调用方负责 commit）"""
    db.add(AdminLog(
        admin_id=int(admin.get("id") or 0),
        admin_name=admin.get("nickname") or admin.get("username") or "管理员",
        action=action,
        target_type=target_type,
        target_id=int(target_id or 0),
        detail=(detail or "")[:255],
        ip=ip or "",
    ))


def user_aggregates(db, user_ids):
    """批量取用户维度的聚合指标，避免列表页 N+1 查询"""
    if not user_ids:
        return {}
    result = {uid: {"habitCount": 0, "totalCheckins": 0, "streakDays": 0, "aiRole": ""}
              for uid in user_ids}

    for uid, cnt in (
        db.query(Habit.user_id, func.count(Habit.id))
        .filter(Habit.user_id.in_(user_ids), Habit.status == 1)
        .group_by(Habit.user_id)
        .all()
    ):
        result[uid]["habitCount"] = int(cnt or 0)

    for uid, total in (
        db.query(Checkin.user_id, func.coalesce(func.sum(Checkin.completed_count), 0))
        .filter(Checkin.user_id.in_(user_ids), Checkin.status == 1)
        .group_by(Checkin.user_id)
        .all()
    ):
        result[uid]["totalCheckins"] = int(total or 0)

    # 最近一次打卡的连续天数 = 当前连续天数
    latest = (
        db.query(Checkin.user_id, func.max(Checkin.checkin_date).label("d"))
        .filter(Checkin.user_id.in_(user_ids), Checkin.status == 1)
        .group_by(Checkin.user_id)
        .subquery()
    )
    for uid, streak in (
        db.query(Checkin.user_id, Checkin.streak_days)
        .join(latest, (Checkin.user_id == latest.c.user_id) & (Checkin.checkin_date == latest.c.d))
        .all()
    ):
        result[uid]["streakDays"] = int(streak or 0)

    # 最近一次会话用的 AI 角色
    latest_session = (
        db.query(ChatSession.user_id, func.max(ChatSession.id).label("sid"))
        .filter(ChatSession.user_id.in_(user_ids))
        .group_by(ChatSession.user_id)
        .subquery()
    )
    for uid, role_type in (
        db.query(ChatSession.user_id, ChatSession.role_type)
        .join(latest_session, ChatSession.id == latest_session.c.sid)
        .all()
    ):
        result[uid]["aiRole"] = role_type or ""

    return result


def user_to_dict(user, agg=None):
    agg = agg or {}
    total = int(agg.get("totalCheckins") or 0)
    _, level_name = level_of(total)
    level = next((i + 1 for i, (threshold, _) in enumerate(reversed(LEVELS)) if total >= threshold), 1)
    return {
        "id": user.id,
        "username": user.username or "",
        "phone": user.phone or "",
        "nickname": user.nickname or "",
        "avatar": user.avatar or "",
        "gender": int(user.gender or 0),
        "genderText": {1: "男", 2: "女"}.get(int(user.gender or 0), "未知"),
        "status": int(user.status or 0),
        "statusText": "正常" if int(user.status or 0) == 1 else "禁用",
        "level": level,
        "levelName": level_name,
        "habitCount": int(agg.get("habitCount") or 0),
        "totalCheckins": total,
        "streakDays": int(agg.get("streakDays") or 0),
        "aiRole": agg.get("aiRole") or "",
        "registerTime": fmt(user.register_time),
        "lastLoginTime": fmt(user.last_login_time),
    }


def dashboard_stats(db):
    today = date.today()
    week_ago = datetime.now() - timedelta(days=7)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = (
        db.query(func.count(User.id)).filter(User.last_login_time >= week_ago).scalar() or 0
    )
    new_today = (
        db.query(func.count(User.id)).filter(func.date(User.register_time) == today).scalar() or 0
    )
    total_checkins = (
        db.query(func.coalesce(func.sum(Checkin.completed_count), 0))
        .filter(Checkin.status == 1).scalar() or 0
    )
    today_checkins = (
        db.query(func.coalesce(func.sum(Checkin.completed_count), 0))
        .filter(Checkin.status == 1, Checkin.checkin_date == today).scalar() or 0
    )
    last_30 = today - timedelta(days=29)
    rate_row = (
        db.query(func.coalesce(func.avg(Checkin.completion_rate), 0))
        .filter(Checkin.status == 1, Checkin.checkin_date >= last_30).scalar() or 0
    )
    total_habits = db.query(func.count(Habit.id)).filter(Habit.status == 1).scalar() or 0
    ai_conversations = db.query(func.count(ChatSession.id)).scalar() or 0

    # 近 30 天注册趋势
    reg_rows = dict(
        (str(d), int(c)) for d, c in
        db.query(func.date(User.register_time), func.count(User.id))
        .filter(User.register_time >= datetime.combine(last_30, datetime.min.time()))
        .group_by(func.date(User.register_time))
        .all()
    )
    user_trend = []
    for i in range(30):
        d = last_30 + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        user_trend.append({
            "date": d.strftime("%m-%d"),
            "new": reg_rows.get(key, 0),
            "total": int(total_users),
        })

    # 近 7 天打卡趋势
    checkin_rows = dict(
        (str(d), (int(c or 0), float(r or 0))) for d, c, r in
        db.query(Checkin.checkin_date,
                 func.coalesce(func.sum(Checkin.completed_count), 0),
                 func.coalesce(func.avg(Checkin.completion_rate), 0))
        .filter(Checkin.status == 1, Checkin.checkin_date >= today - timedelta(days=6))
        .group_by(Checkin.checkin_date)
        .all()
    )
    checkin_trend = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        count, rate = checkin_rows.get(str(d), (0, 0.0))
        checkin_trend.append({
            "date": d.strftime("%m-%d"),
            "count": count,
            "rate": round(rate, 1),
        })

    # 习惯分布（按用户正在培养的习惯名统计）
    habit_dist = []
    for idx, (name, color, cnt) in enumerate(
        db.query(Habit.name, func.max(Habit.color), func.count(Habit.id))
        .filter(Habit.status == 1)
        .group_by(Habit.name)
        .order_by(func.count(Habit.id).desc())
        .limit(8)
        .all()
    ):
        habit_dist.append({"name": name, "value": int(cnt or 0),
                           "color": color or CHART_COLORS[idx % len(CHART_COLORS)]})

    # AI 角色分布（按会话使用的角色）
    role_names = {r.role_type: r.name for r in db.query(AIRole.role_type, AIRole.name).all()}
    role_dist = []
    for idx, (role_type, cnt) in enumerate(
        db.query(ChatSession.role_type, func.count(ChatSession.id))
        .group_by(ChatSession.role_type)
        .order_by(func.count(ChatSession.id).desc())
        .limit(8)
        .all()
    ):
        label = role_names.get(role_type) or role_type or "未知"
        suffix = ROLE_TYPE_LABEL.get(role_type, role_type or "")
        role_dist.append({
            "name": f"{label}({suffix})" if suffix else label,
            "value": int(cnt or 0),
            "color": CHART_COLORS[idx % len(CHART_COLORS)],
        })

    recent = (
        db.query(AdminLog).order_by(AdminLog.id.desc()).limit(8).all()
    )

    return {
        "overview": {
            "totalUsers": int(total_users),
            "activeUsers": int(active_users),
            "newUsersToday": int(new_today),
            "totalCheckins": int(total_checkins),
            "todayCheckins": int(today_checkins),
            "avgCompletionRate": round(float(rate_row), 1),
            "totalHabits": int(total_habits),
            "aiConversations": int(ai_conversations),
        },
        "userTrend": user_trend,
        "checkinTrend": checkin_trend,
        "habitDistribution": habit_dist,
        "roleDistribution": role_dist,
        "recentActivities": [r.to_dict() for r in recent],
    }


def review_map(db, target_type, ids):
    if not ids:
        return {}
    rows = (
        db.query(AdminReview)
        .filter(AdminReview.target_type == target_type, AdminReview.target_id.in_(ids))
        .all()
    )
    return {r.target_id: r.status for r in rows}


def upsert_review(db, target_type, target_id, status, admin_id, remark=""):
    row = (
        db.query(AdminReview)
        .filter(AdminReview.target_type == target_type, AdminReview.target_id == target_id)
        .first()
    )
    if row is None:
        row = AdminReview(target_type=target_type, target_id=target_id, status=status,
                          admin_id=admin_id, remark=remark)
        db.add(row)
    else:
        row.status = status
        row.admin_id = admin_id
        row.remark = remark
    return row


def user_detail(db, user):
    habits = db.query(Habit).filter(Habit.user_id == user.id, Habit.status == 1).all()
    templates = {t.id: t for t in db.query(TaskTemplate).all()}

    today = date.today()
    today_rows = (
        db.query(CheckinItem)
        .filter(CheckinItem.user_id == user.id,
                func.date(CheckinItem.created_at) == today)
        .all()
    )
    done_habit_ids = {r.habit_id for r in today_rows if int(r.completed or 0) == 1}

    habit_list = []
    for h in habits:
        tpl = templates.get(h.template_id)
        habit_list.append({
            "id": h.id,
            "type": (tpl.type if tpl else h.habit_type) or "other",
            "name": h.name,
            "icon": h.icon,
            "color": h.color,
            "target": h.target,
            "difficulty": h.difficulty,
            "streak": int(h.continuous_day or 0),
            "completed": h.id in done_habit_ids,
        })

    badge_rows = (
        db.query(UserBadge, Badge)
        .join(Badge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.user_id == user.id)
        .all()
    )
    badges = [{
        "id": b.id,
        "code": b.code,
        "name": b.name,
        "description": b.description,
        "icon": b.icon,
        "conditionType": b.condition_type,
        "conditionValue": b.condition_value,
        "status": int(b.status or 0),
        "unlocked": True,
        "unlockedAt": fmt(ub.earned_at),
    } for ub, b in badge_rows]

    recent_checkins = []
    for c in (
        db.query(Checkin)
        .filter(Checkin.user_id == user.id, Checkin.status == 1)
        .order_by(Checkin.checkin_date.desc())
        .limit(7)
        .all()
    ):
        recent_checkins.append({
            "date": c.checkin_date.strftime("%Y-%m-%d") if c.checkin_date else "",
            "total": int(c.total_habits or 0),
            "completed": int(c.completed_count or 0),
            "rate": int(round(float(c.completion_rate or 0))),
        })

    agg = user_aggregates(db, [user.id]).get(user.id, {})
    data = user_to_dict(user, agg)
    data.update({"habits": habit_list, "badges": badges, "recentCheckins": recent_checkins})
    return data


def chat_content_dict(msg, user, review_status):
    return {
        "id": msg.id,
        "userId": msg.user_id,
        "userNickname": (user.nickname if user else "") or "",
        "userAvatar": (user.avatar if user else "") or "",
        "sessionId": msg.session_id,
        "role": msg.role,
        "content": msg.content or "",
        "emotion": msg.emotion or "neutral",
        "reviewStatus": review_status or "pending",
        "createdAt": fmt(msg.created_at),
    }


def checkin_content_dict(diary, user, habit):
    return {
        "id": diary.id,
        "userId": diary.user_id,
        "userNickname": (user.nickname if user else "") or "",
        "userAvatar": (user.avatar if user else "") or "",
        "habitType": (habit.habit_type if habit else "") or "other",
        "habitName": (habit.name if habit else "") or "",
        "content": diary.content or "",
        "imageUrl": diary.ai_comic_url or "",
        "hasImage": bool(diary.ai_comic_url),
        "reviewStatus": "pending",
        "checkinTime": fmt(diary.created_at),
    }
