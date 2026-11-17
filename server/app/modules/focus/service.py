# -*- coding: utf-8 -*-
"""
「专注」模块核心服务
======================

所有业务规则集中在这里，router 只做参数/鉴权/序列化外壳。

- 备考计划生成 → 落任务/步骤/提醒（AI，含本地兜底）
- 大任务拆解 → focus_step（分步引导核心）
- 专注会话：开始 / 跳出检测记录 / 结束（自动生成专注记录）
- 统计报表：日/周/月/自定义（时长、次数、最早开始、标签饼图、时段热力）
- 专注动态：仅自己 / 互关好友可见；点赞 + AI 角色自动鼓励留言
- 提醒：任务提醒 / 聊天指令建日程（createRemindFromChat）
- 引导记录：保存 / 搜索 / 回放 / 导出文本
- 删除任务/记录/动态 → 级联清除子步骤、提醒、会话

联动（单向，不改旧表）：打卡同步由前端调用现有 /habit 接口完成。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, time as dtime
from typing import Dict, List, Optional

from sqlalchemy import or_, and_, func as sa_func
from sqlalchemy.orm import Session

from app.models.user import User

from . import focus_ai
from .models import (
    FocusTask, FocusStep, FocusSession, FocusRecord,
    FocusDynamic, FocusDynamicComment, FocusDynamicLike,
    FocusRemind, FocusFollow, FocusSetting,
)

# 引用「小想法」模块的审核与限流工具（独立 import，不改其任何代码）
from app.modules.idea.content_safety import audit_text, limiter


# ============================================================
# 开关
# ============================================================
def get_or_create_setting(db: Session, uid: int) -> FocusSetting:
    row = db.query(FocusSetting).filter(FocusSetting.user_id == uid).first()
    if not row:
        row = FocusSetting(user_id=uid, allow_dynamic=1, allow_remind=1)
        db.add(row)
        db.flush()
    return row


# ============================================================
# 互关好友
# ============================================================
def follow_user(db: Session, uid: int, target_uid: int) -> Dict:
    if uid == target_uid:
        return {"__error__": "不能关注自己", "__code__": 400}
    exists = db.query(FocusFollow).filter(
        FocusFollow.user_id == uid, FocusFollow.friend_uid == target_uid).first()
    if not exists:
        db.add(FocusFollow(user_id=uid, friend_uid=target_uid))
    db.commit()
    return {"followed": True, "mutual": is_mutual(db, uid, target_uid)}


def unfollow_user(db: Session, uid: int, target_uid: int) -> Dict:
    db.query(FocusFollow).filter(
        FocusFollow.user_id == uid, FocusFollow.friend_uid == target_uid).delete()
    db.commit()
    return {"followed": False}


def is_mutual(db: Session, a: int, b: int) -> bool:
    return db.query(FocusFollow).filter(
        FocusFollow.user_id == a, FocusFollow.friend_uid == b).first() is not None and \
        db.query(FocusFollow).filter(
            FocusFollow.user_id == b, FocusFollow.friend_uid == a).first() is not None


def my_friend_ids(db: Session, uid: int) -> List[int]:
    """互关好友 ID 列表（双向都有记录才算互关）"""
    follows = db.query(FocusFollow).filter(FocusFollow.user_id == uid).all()
    out = []
    for f in follows:
        if is_mutual(db, uid, f.friend_uid):
            out.append(f.friend_uid)
    return out


# ============================================================
# 任务
# ============================================================
def create_task(db: Session, uid: int, title: str, description: str = "",
                tag: str = "学习", est_minutes: int = 25,
                start_date: str = "", due_date: str = "",
                remind_time: str = "", source: str = "manual",
                steps: Optional[List[Dict]] = None) -> FocusTask:
    task = FocusTask(
        uid=uid, title=(title or "未命名任务")[:200],
        description=(description or "")[:1000],
        tag=tag if tag in ("学习", "工作", "生活", "运动", "其他") else "学习",
        est_minutes=max(1, min(int(est_minutes or 25), 600)),
        start_date=start_date or datetime.now().strftime("%Y-%m-%d"),
        due_date=due_date or "",
        remind_time=remind_time or "",
        source=source,
    )
    db.add(task)
    db.flush()
    if steps:
        for i, s in enumerate(steps[:20], 1):
            db.add(FocusStep(task_id=task.id, uid=uid, step_index=i,
                             content=str(s.get("content", ""))[:500],
                             est_minutes=max(1, min(int(s.get("minutes") or 5), 60))))
        task.total_steps = min(len(steps), 20)
    else:
        task.total_steps = 0
    db.commit()
    db.refresh(task)

    if task.remind_time and is_remind_on(db, uid):
        _upsert_daily_remind(db, uid, task)
    return task


def _upsert_daily_remind(db: Session, uid: int, task: FocusTask):
    """为任务建立「当日 HH:MM」提醒（已存在同任务当日提醒则跳过）"""
    today = datetime.now().strftime("%Y-%m-%d")
    remind_at = f"{today} {task.remind_time[:5]}"
    exists = db.query(FocusRemind).filter(
        FocusRemind.uid == uid, FocusRemind.task_id == task.id,
        FocusRemind.remind_at == remind_at).first()
    if not exists:
        db.add(FocusRemind(uid=uid, task_id=task.id, remind_at=remind_at,
                           text=f"该做「{task.title[:40]}」啦"))
        db.commit()


def get_board(db: Session, uid: int, date: str = "") -> Dict:
    """今日待办看板：当日任务 + 进度。上午/下午分组由前端按 remind_time/时段判断"""
    date = date or datetime.now().strftime("%Y-%m-%d")
    tasks = db.query(FocusTask).filter(
        FocusTask.uid == uid, FocusTask.is_deleted == 0,
        or_(FocusTask.start_date == date, FocusTask.status == 1),
    ).order_by(FocusTask.id.desc()).all()

    out = []
    total = finished = 0
    for t in tasks:
        d = t.to_dict()
        steps = db.query(FocusStep).filter(
            FocusStep.task_id == t.id).order_by(FocusStep.step_index.asc()).all()
        d["steps"] = [{
            "id": s.id, "step_index": s.step_index, "content": s.content,
            "est_minutes": s.est_minutes, "is_finished": bool(s.is_finished),
            "finish_time": s.finish_time.strftime("%Y-%m-%d %H:%M:%S") if s.finish_time else "",
        } for s in steps]
        d["progress"] = round((d["finished_steps"] / d["total_steps"]) * 100) if d["total_steps"] else 0
        out.append(d)
        total += max(d["total_steps"], 1)
        finished += d["finished_steps"] if d["total_steps"] else (1 if d["status"] == 2 else 0)
    return {
        "date": date,
        "list": out,
        "progress": {"finished": finished, "total": total,
                     "percent": round(finished / total * 100) if total else 0},
    }


def update_task_status(db: Session, uid: int, task_id: int, status: int) -> Dict:
    t = db.query(FocusTask).filter(FocusTask.id == task_id, FocusTask.uid == uid,
                                   FocusTask.is_deleted == 0).first()
    if not t:
        return {"__error__": "任务不存在", "__code__": 404}
    t.status = max(0, min(int(status), 2))
    if t.status == 2:
        db.query(FocusStep).filter(FocusStep.task_id == t.id).update(
            {"is_finished": 1, "finish_time": datetime.now()}, synchronize_session=False)
        t.finished_steps = t.total_steps
    db.commit()
    return {"id": t.id, "status": t.status}


def finish_step(db: Session, uid: int, step_id: int, role_id: str = "companion") -> Dict:
    """完成当前步骤 → 推进到下一步，返回 AI 鼓励台词"""
    s = db.query(FocusStep).filter(FocusStep.id == step_id, FocusStep.uid == uid).first()
    if not s:
        return {"__error__": "步骤不存在", "__code__": 404}
    task = db.query(FocusTask).filter(FocusTask.id == s.task_id).first()
    if not s.is_finished:
        s.is_finished = 1
        s.finish_time = datetime.now()
        if task:
            task.finished_steps = (task.finished_steps or 0) + 1
            if task.finished_steps >= task.total_steps and task.total_steps > 0:
                task.status = 2
            elif task.status == 0:
                task.status = 1
    db.commit()

    nxt = db.query(FocusStep).filter(
        FocusStep.task_id == s.task_id, FocusStep.is_finished == 0
    ).order_by(FocusStep.step_index.asc()).first()
    return {
        "step_id": s.id,
        "task_done": bool(task and task.status == 2),
        "next_step": {"id": nxt.id, "step_index": nxt.step_index,
                      "content": nxt.content, "est_minutes": nxt.est_minutes} if nxt else None,
        "cheer": focus_ai.encourage_line(role_id, "step_done", nxt.content if nxt else ""),
    }


def delete_task(db: Session, uid: int, task_id: int) -> Dict:
    """删除任务 → 级联清除子步骤、提醒、会话记录"""
    t = db.query(FocusTask).filter(FocusTask.id == task_id, FocusTask.uid == uid,
                                   FocusTask.is_deleted == 0).first()
    if not t:
        return {"__error__": "任务不存在", "__code__": 404}
    t.is_deleted = 1
    db.query(FocusStep).filter(FocusStep.task_id == task_id).delete(synchronize_session=False)
    db.query(FocusRemind).filter(FocusRemind.task_id == task_id).delete(synchronize_session=False)
    db.query(FocusSession).filter(FocusSession.task_id == task_id).delete(synchronize_session=False)
    db.commit()
    return {"id": task_id}


# ============================================================
# 备考计划
# ============================================================
def publish_plan(db: Session, uid: int, exam_type: str, exam_date: str,
                 weakness: str, daily_minutes: int,
                 remind_time: str = "") -> Dict:
    """生成计划并批量落成任务 + 提醒。返回 {phases, tasks, source}"""
    days_left = 30
    try:
        if exam_date:
            days_left = max(7, (datetime.strptime(exam_date[:10], "%Y-%m-%d") - datetime.now()).days)
    except Exception:
        pass

    plan = focus_ai.generate_plan(exam_type, exam_date, weakness, daily_minutes, days_left)
    created = []
    for p in plan["phases"]:
        phase_name = p["name"]
        for d in p["days"]:
            task = create_task(
                db, uid, title=f"[{phase_name}] {d['title']}",
                description=f"考试：{exam_type} 日期：{exam_date} 薄弱：{weakness}",
                tag=d.get("tag", "学习"), est_minutes=d.get("minutes", 45),
                due_date=exam_date[:10] if exam_date else "",
                remind_time=remind_time if is_remind_on(db, uid) else "",
                source="ai_plan",
            )
            created.append(task.to_dict())
    return {"phases": plan["phases"], "source": plan["source"],
            "task_count": len(created), "tasks": created}


# ============================================================
# 分步引导
# ============================================================
def start_guide(db: Session, uid: int, prompt: str, mode: str = "simple") -> Dict:
    """输入大任务（文字/语音转写），AI 切成极小单步，返回第一步 + 保存引导记录"""
    prompt = (prompt or "").strip()[:500]
    if not prompt:
        return {"__error__": "请先说说你想做什么", "__code__": 400}
    result = focus_ai.split_big_task(prompt, mode)
    steps = result["steps"]

    rec = FocusRecord(
        uid=uid, origin_prompt=prompt, mode=mode,
        full_step_list=json.dumps(steps, ensure_ascii=False),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "record_id": rec.id,
        "mode": mode,
        "steps": steps,
        "current_index": 1,
        "cheer": focus_ai.encourage_line("companion", "focus_on", prompt),
        "source": result["source"],
    }


def save_guide_progress(db: Session, uid: int, record_id: int,
                        current_index: int, duration_seconds: int = 0,
                        finished_content: str = "") -> Dict:
    """引导推进时回写：更新记录的步骤列表与全程计时，最终导出文本即时生成"""
    rec = db.query(FocusRecord).filter(FocusRecord.id == record_id,
                                       FocusRecord.uid == uid,
                                       FocusRecord.is_deleted == 0).first()
    if not rec:
        return {"__error__": "记录不存在", "__code__": 404}
    rec.duration_seconds = max(0, int(duration_seconds or 0))
    rec.export_text = _render_record_text(rec)
    db.commit()
    return {"record_id": rec.id, "duration_seconds": rec.duration_seconds}


def _render_record_text(rec: FocusRecord) -> str:
    try:
        steps = json.loads(rec.full_step_list or "[]")
    except Exception:
        steps = []
    lines = [f"引导记录 · {rec.create_time.strftime('%Y-%m-%d %H:%M') if rec.create_time else ''}",
             f"任务：{rec.origin_prompt}",
             f"模式：{'简单' if rec.mode == 'simple' else '心流'}　总时长：{rec.duration_seconds // 60} 分 {rec.duration_seconds % 60} 秒",
             "-" * 30]
    for i, s in enumerate(steps, 1):
        lines.append(f"{i}. {s.get('content', '')}（约 {s.get('minutes', 5)} 分钟）")
    lines.append("-" * 30)
    lines.append("每一次「我做到了」，都是对自己的兑现。")
    return "\n".join(lines)


def get_records(db: Session, uid: int, keyword: str = "") -> List[Dict]:
    """引导记录列表（支持关键字搜索 origin_prompt）"""
    q = db.query(FocusRecord).filter(FocusRecord.uid == uid, FocusRecord.is_deleted == 0)
    if keyword:
        q = q.filter(FocusRecord.origin_prompt.like(f"%{keyword[:50]}%"))
    rows = q.order_by(FocusRecord.id.desc()).limit(100).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "origin_prompt": r.origin_prompt,
            "mode": r.mode,
            "step_count": len(json.loads(r.full_step_list or "[]")),
            "duration_seconds": r.duration_seconds,
            "create_time": r.create_time.strftime("%Y-%m-%d %H:%M") if r.create_time else "",
        })
    return out


def get_record_detail(db: Session, uid: int, record_id: int) -> Dict:
    rec = db.query(FocusRecord).filter(FocusRecord.id == record_id,
                                       FocusRecord.uid == uid,
                                       FocusRecord.is_deleted == 0).first()
    if not rec:
        return {"__error__": "记录不存在", "__code__": 404}
    if not rec.export_text:
        rec.export_text = _render_record_text(rec)
        db.commit()
    return {
        "id": rec.id, "origin_prompt": rec.origin_prompt, "mode": rec.mode,
        "steps": json.loads(rec.full_step_list or "[]"),
        "export_text": rec.export_text,
        "duration_seconds": rec.duration_seconds,
        "create_time": rec.create_time.strftime("%Y-%m-%d %H:%M") if rec.create_time else "",
    }


def delete_record(db: Session, uid: int, record_id: int) -> Dict:
    rec = db.query(FocusRecord).filter(FocusRecord.id == record_id,
                                       FocusRecord.uid == uid).first()
    if not rec:
        return {"__error__": "记录不存在", "__code__": 404}
    rec.is_deleted = 1
    db.commit()
    return {"id": record_id}


# ============================================================
# 专注会话
# ============================================================
def start_session(db: Session, uid: int, task_id: int, role_id: str,
                  mode: str, tag: str) -> Dict:
    """开启专注会话（计时由前端驱动，后端只登记起点）"""
    s = FocusSession(uid=uid, task_id=max(0, int(task_id or 0)),
                     role_id=role_id if role_id in focus_ai.ROLE_IDS else "companion",
                     mode=mode if mode in ("simple", "flow") else "simple",
                     start_time=datetime.now(), tag=tag or "学习")
    db.add(s)
    db.commit()
    db.refresh(s)
    return {
        "session_id": s.id,
        "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "cheer_lines": [
            focus_ai.encourage_line(s.role_id, "focus_on", f"{i}") for i in range(3)
        ],
    }


def session_interrupt(db: Session, uid: int, session_id: int,
                      count: int = 1) -> Dict:
    """跳出专注时回报（原生 App 拦截 / 小程序 H5 离开检测）"""
    s = db.query(FocusSession).filter(FocusSession.id == session_id,
                                      FocusSession.uid == uid).first()
    if not s:
        return {"__error__": "会话不存在", "__code__": 404}
    s.is_interrupted = 1
    s.blacklist_trigger_count += max(1, int(count or 1))
    db.commit()
    return {"session_id": s.id, "blacklist_trigger_count": s.blacklist_trigger_count}


def finish_session(db: Session, uid: int, session_id: int,
                   duration: int, interrupted: bool = False) -> Dict:
    """结束专注 → 落库时长 + 生成专注记录摘要"""
    s = db.query(FocusSession).filter(FocusSession.id == session_id,
                                      FocusSession.uid == uid).first()
    if not s:
        return {"__error__": "会话不存在", "__code__": 404}
    s.end_time = datetime.now()
    s.duration = max(0, int(duration or 0))
    if interrupted:
        s.is_interrupted = 1
    db.commit()
    mins = s.duration // 60
    return {
        "session_id": s.id,
        "duration_seconds": s.duration,
        "summary": f"本次专注 {mins} 分钟（{s.tag}）" + ("，中途离开过，下次会更稳。" if s.is_interrupted else "，全程在线，干得漂亮。"),
        "cheer": focus_ai.encourage_line(s.role_id, "step_done"),
    }


# ============================================================
# 统计报表
# ============================================================
def get_stat(db: Session, uid: int, period: str = "day",
             start_date: str = "", end_date: str = "") -> Dict:
    """专注统计：总时长/日均/最早开始/发起次数/标签饼图/时段热力/角色排行"""
    now = datetime.now()
    # 【修复】MySQL DATETIME 会对小数秒四舍五入，刚结束的会话可能比 now 大不到 1 秒
    # 而被 start_time < d1 排除，导致「刚练完立刻看统计」显示 0；上限放宽 1 秒
    upper = now + timedelta(seconds=1)
    if period == "day":
        d0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
        d1 = upper
    elif period == "week":
        d0 = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        d1 = upper
    elif period == "month":
        d0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        d1 = upper
    else:  # custom
        try:
            d0 = datetime.strptime(start_date[:10], "%Y-%m-%d")
            d1 = datetime.strptime(end_date[:10], "%Y-%m-%d") + timedelta(days=1)
        except Exception:
            d0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
            d1 = upper

    rows = db.query(FocusSession).filter(
        FocusSession.uid == uid,
        FocusSession.start_time >= d0, FocusSession.start_time < d1,
    ).all()

    total = sum(r.duration for r in rows)
    # day/week/month 都是含今天的自然区间，需 +1；custom 已是闭区间+1天，保持原值
    if period == "custom":
        days = max(1, (d1 - d0).days)
    else:
        days = max(1, (d1 - d0).days + 1)
    tag_map: Dict[str, int] = {}
    hour_map = {h: 0 for h in range(24)}
    role_map: Dict[str, int] = {}
    earliest = ""
    for r in rows:
        tag_map[r.tag] = tag_map.get(r.tag, 0) + r.duration
        if r.start_time:
            hour_map[r.start_time.hour] += r.duration
            if not earliest or r.start_time.strftime("%H:%M") < earliest:
                earliest = r.start_time.strftime("%H:%M")
        role_map[r.role_id] = role_map.get(r.role_id, 0) + r.duration

    from .persona import ROLE_META
    role_rank = [{"role_id": k, "name": ROLE_META.get(k, {}).get("name", k),
                  "minutes": v // 60}
                 for k, v in sorted(role_map.items(), key=lambda x: -x[1])]
    return {
        "period": period, "start": d0.strftime("%Y-%m-%d"), "end": d1.strftime("%Y-%m-%d"),
        "total_minutes": total // 60,
        "daily_avg_minutes": (total // 60) // days,
        # 【修复】发起次数只统计真正产生时长（duration>0）的会话，
        # 点了开始就退出、duration=0 的中断会话不再计入
        "session_count": sum(1 for r in rows if (r.duration or 0) > 0),
        "earliest_start": earliest,
        "interrupted_count": sum(1 for r in rows if r.is_interrupted),
        "tag_pie": [{"tag": k, "minutes": v // 60} for k, v in
                    sorted(tag_map.items(), key=lambda x: -x[1])],
        "hour_heat": [{"hour": h, "seconds": v} for h, v in hour_map.items()],
        "role_rank": role_rank,
    }


# ============================================================
# 提醒
# ============================================================
def is_remind_on(db: Session, uid: int) -> bool:
    return bool(get_or_create_setting(db, uid).allow_remind)


def create_remind(db: Session, uid: int, task_id: int, remind_at: str,
                  text: str = "") -> Dict:
    if not is_remind_on(db, uid):
        return {"__error__": "你已关闭专注提醒，请先到设置中开启", "__code__": 400}
    r = FocusRemind(uid=uid, task_id=max(0, int(task_id or 0)),
                    remind_at=(remind_at or "")[:20], text=(text or "")[:200])
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "remind_at": r.remind_at, "text": r.text}


def list_reminds(db: Session, uid: int) -> List[Dict]:
    rows = db.query(FocusRemind).filter(
        FocusRemind.uid == uid, FocusRemind.is_triggered == 0
    ).order_by(FocusRemind.remind_at.asc()).limit(100).all()
    return [{"id": r.id, "task_id": r.task_id, "remind_at": r.remind_at,
             "text": r.text} for r in rows]


def trigger_remind(db: Session, uid: int, remind_id: int) -> Dict:
    db.query(FocusRemind).filter(FocusRemind.id == remind_id,
                                 FocusRemind.uid == uid).update(
        {"is_triggered": 1}, synchronize_session=False)
    db.commit()
    return {"id": remind_id}


def delete_remind(db: Session, uid: int, remind_id: int) -> Dict:
    db.query(FocusRemind).filter(FocusRemind.id == remind_id,
                                 FocusRemind.uid == uid).delete()
    db.commit()
    return {"id": remind_id}


def chat_command_to_task(db: Session, uid: int, cmd: Dict) -> Optional[Dict]:
    """createRemindFromChat：把陪伴聊天解析出的指令落成 待办 + 提醒"""
    title = (cmd.get("title") or "").strip()
    if not title:
        return None
    task = create_task(db, uid, title=title, tag=cmd.get("tag", "学习"),
                       source="chat", est_minutes=25)
    remind_at = (cmd.get("remind_at") or "").strip()
    if remind_at and is_remind_on(db, uid):
        r = FocusRemind(uid=uid, task_id=task.id, remind_at=remind_at[:20],
                        text=f"提醒：{title[:40]}")
        db.add(r)
        db.commit()
    return {"task": task.to_dict(), "remind_at": remind_at}


# ============================================================
# 陪伴聊天（监督人设）
# ============================================================
def companion_chat(db: Session, uid: int, text: str,
                   history: Optional[List[Dict]] = None) -> Dict:
    text = (text or "").strip()[:500]
    if not text:
        return {"__error__": "消息不能为空", "__code__": 400}
    result = focus_ai.companion_reply("companion", text, history)
    created = None
    if result.get("cmd"):
        created = chat_command_to_task(db, uid, result["cmd"])
    return {"reply": result["reply"], "arrangement": created}


# ============================================================
# 专注动态（严禁公开广场：只查 自己 + 互关好友）
# ============================================================
def publish_dynamic(db: Session, uid: int, content: str, image: str,
                    visible_type: str) -> Dict:
    if not get_or_create_setting(db, uid).allow_dynamic:
        return {"__error__": "你已关闭专注动态发布", "__code__": 400}
    content = (content or "").strip()
    if not content and not image:
        return {"__error__": "写点什么再发布吧", "__code__": 400}
    ok, reason = audit_text(content)
    if not ok:
        return {"__error__": reason, "__code__": 400}
    d = FocusDynamic(uid=uid, content=content[:1000],
                     image=(image or ""), 
                     visible_type="follow" if visible_type == "follow" else "self")
    db.add(d)
    db.commit()
    db.refresh(d)
    # AI 角色自动鼓励留言（失败静默，不打扰发布）
    try:
        line = focus_ai.encourage_line("gentle", "step_done", content)
        db.add(FocusDynamicComment(dynamic_id=d.id, uid=0, role_id="gentle",
                                   content=line, is_ai=1))
        db.commit()
    except Exception:
        pass
    return _dynamic_dict(db, d, uid)


def _dynamic_dict(db: Session, d: FocusDynamic, viewer: int) -> Dict:
    u = db.query(User).filter(User.id == d.uid).first()
    likes = db.query(FocusDynamicLike).filter(FocusDynamicLike.dynamic_id == d.id).all()
    comments = db.query(FocusDynamicComment).filter(
        FocusDynamicComment.dynamic_id == d.id).order_by(FocusDynamicComment.id.asc()).all()
    cm_out = []
    for c in comments:
        cu = db.query(User).filter(User.id == c.uid).first() if c.uid else None
        cm_out.append({
            "id": c.id, "uid": c.uid,
            "nickname": "专注伙伴" if c.is_ai else ((cu.nickname if cu and cu.nickname else "用户") if cu else "用户"),
            "content": c.content, "is_ai": bool(c.is_ai),
            "create_time": c.create_time.strftime("%m-%d %H:%M") if c.create_time else "",
        })
    return {
        "id": d.id, "uid": d.uid,
        "nickname": (u.nickname if u and u.nickname else "用户") if u else "用户",
        "avatar": (u.avatar if u else "") or "",
        "content": d.content, "image": d.image,
        "visible_type": d.visible_type,
        "like_count": len(likes),
        "liked": any(l.from_uid == viewer for l in likes),
        "comments": cm_out,
        "create_time": d.create_time.strftime("%Y-%m-%d %H:%M") if d.create_time else "",
    }


def get_dynamics(db: Session, uid: int) -> List[Dict]:
    """仅返回：我发布的 + 互关好友发布的（follow 可见）。没有任何公开列表。"""
    friend_ids = my_friend_ids(db, uid)
    rows = db.query(FocusDynamic).filter(
        FocusDynamic.is_deleted == 0,
        or_(FocusDynamic.uid == uid,
            and_(FocusDynamic.uid.in_(friend_ids or [0]), FocusDynamic.visible_type == "follow")),
    ).order_by(FocusDynamic.id.desc()).limit(50).all()
    return [_dynamic_dict(db, r, uid) for r in rows]


def react_dynamic(db: Session, uid: int, dynamic_id: int) -> Dict:
    """点赞 / 取消点赞（幂等）"""
    d = db.query(FocusDynamic).filter(FocusDynamic.id == dynamic_id,
                                      FocusDynamic.is_deleted == 0).first()
    if not d:
        return {"__error__": "动态不存在", "__code__": 404}
    friend_ids = my_friend_ids(db, uid)
    if d.uid != uid and d.uid not in friend_ids:
        return {"__error__": "无权访问该动态", "__code__": 403}
    exists = db.query(FocusDynamicLike).filter(
        FocusDynamicLike.dynamic_id == dynamic_id,
        FocusDynamicLike.from_uid == uid).first()
    if exists:
        db.delete(exists)
        db.commit()
        return {"liked": False}
    db.add(FocusDynamicLike(dynamic_id=dynamic_id, from_uid=uid))
    db.commit()
    return {"liked": True}


def delete_dynamic(db: Session, uid: int, dynamic_id: int) -> Dict:
    d = db.query(FocusDynamic).filter(FocusDynamic.id == dynamic_id,
                                      FocusDynamic.uid == uid).first()
    if not d:
        return {"__error__": "动态不存在", "__code__": 404}
    d.is_deleted = 1
    db.query(FocusDynamicComment).filter(
        FocusDynamicComment.dynamic_id == dynamic_id).delete(synchronize_session=False)
    db.query(FocusDynamicLike).filter(
        FocusDynamicLike.dynamic_id == dynamic_id).delete(synchronize_session=False)
    db.commit()
    return {"id": dynamic_id}


# ============================================================
# 语音输入
# ============================================================
def transcribe_audio(audio_path: str) -> Dict:
    """复用现有 ASRService 转写通道；未配置/失败时返回明确错误，不再降级假文本"""
    from app.services.voice_service import ASRService, ASRError
    try:
        text = ASRService.transcribe(audio_path, language="zh")
    except ASRError as e:
        return {"__error__": e.message, "__code__": e.code}
    except Exception as e:
        return {"__error__": f"语音识别失败：{e}", "__code__": 502}
    return {
        "text": (text or "").strip(),
        "provider": ASRService.provider_name(),
        "mock": ASRService.provider_name() == "mock",
    }
