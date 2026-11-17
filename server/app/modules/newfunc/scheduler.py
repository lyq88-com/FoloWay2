# -*- coding: utf-8 -*-
"""
newfunc 独立定时任务调度器（APScheduler AsyncIOScheduler，进程内启动）
- checkin_remind：每日按用户设置的 checkin_push_time 扫描（每分钟校验）
- todo_due：每分钟扫描当日到期待办
- ai_companion：每 10 分钟扫描一次 AI 主动陪伴（频控在 job 内部）
所有 Job 只读旧表（habits/checkins/schedules/emotion_records），
写入仅限 push_record / push_setting，不触碰任何旧业务代码。
"""
import datetime as dt
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import SessionLocal

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def _run_job(name: str, coro_fn):
    db = SessionLocal()
    try:
        n = await coro_fn(db)
        if n:
            print(f"[newfunc][scheduler] {name} sent={n}")
    except Exception as e:
        print(f"[newfunc][scheduler] {name} failed: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        db.close()


async def _tick_minutely():
    from app.modules.newfunc import push_service
    await _run_job("todo_due", push_service.job_todo_due)
    await _run_job("checkin_remind", push_service.job_checkin_remind)


async def _tick_ai():
    from app.modules.newfunc import push_service
    await _run_job("ai_companion", push_service.job_ai_companion)


async def _tick_emotion():
    """模块3新增：每 30 分钟扫描一次情绪推送"""
    from app.modules.newfunc import push_service
    await _run_job("emotion_push", push_service.job_emotion_push)


def start_scheduler():
    now = dt.datetime.now()
    scheduler.add_job(_tick_minutely, "interval", minutes=1,
                      next_run_time=now, id="newfunc_minutely",
                      replace_existing=True, max_instances=1)
    scheduler.add_job(_tick_ai, "interval", minutes=10,
                      next_run_time=now, id="newfunc_ai",
                      replace_existing=True, max_instances=1)
    # ↓↓↓ 模块3新增 ↓↓↓
    scheduler.add_job(_tick_emotion, "interval", minutes=30,
                      next_run_time=now, id="newfunc_emotion",
                      replace_existing=True, max_instances=1)
    # ↑↑↑ 模块3结束 ↑↑↑
    scheduler.start()
    print("[newfunc] scheduler started (todo_due/checkin_remind每分钟, ai_companion每10分钟, emotion_push每30分钟)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
