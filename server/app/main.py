# -*- coding: utf-8 -*-
"""
AI习惯伙伴 - FastAPI 应用入口
模块A: 完整路由注册 + CORS + 异常处理 + 请求日志
"""
import time
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.ai_service import AIService  # ↓↓↓ 连接池优雅关闭 ↓↓↓
from app.services.bond_service import BondService  # ↓↓↓ 羁绊碎片自动建表 ↓↓↓
from app.api.v1.auth import router as auth_router
from app.api.v1.user import router as user_router
from app.api.v1.habit import router as habit_router
from app.api.v1.emotion import router as emotion_router
from app.api.v1.mindfulness import router as mindfulness_router
from app.api.v1.chat import router as chat_router
from app.api.v1.stats import router as stats_router
from app.api.v1.archive import router as archive_router
from app.api.v1.habit_ai import router as habit_ai_router
# 【2026-11-15 下线】语音日记 API（/voice-diary/*）前端从未接入，路由不再挂载；
# app/api/v1/voice_diary.py 与 services/voice_service.py 保留，
# 后者仍被「专注」模块的语音转写复用（modules/focus），不能删。
from app.api.v1.companion import router as companion_router
from app.api.v1.badge import router as badge_router
from app.api.v1.moment import router as moment_router
# 【四大新增模块】日程提醒 / 互动扭蛋 / 虚拟世界
from app.api.v1.schedule import router as schedule_router
from app.api.v1.gacha import router as gacha_router
from app.api.v1.world import router as world_router
# 【性格测评上云】
from app.api.v1.personality import router as personality_router
# 【虚拟经济上云】
from app.api.v1.economy import router as economy_router
# 【活动模块：每日签到 / 活跃任务】
from app.api.v1.activity import router as activity_router
# 【陪伴感增强 v3：长效记忆 / 角色人设 / 主动陪伴】
from app.api.v1.memory import router as memory_router
from app.api.v1.persona import router as persona_router
from app.api.v1.proactive import router as proactive_router
from app.api.v1.bond import router as bond_router  # ↓↓↓ 羁绊碎片（纯新增） ↓↓↓
# 【小想法 · 共鸣匹配】独立模块（additive：不改动任何既有路由）
from app.modules.idea.router import router as idea_router
# 【专注 · AI陪伴监督】独立模块（additive：不改动任何既有路由）
from app.modules.focus.router import router as focus_router
# 【newfunc 增量功能：离线推送/情绪日记日历/多AI伙伴隔离记忆】独立模块（additive）
from app.modules.newfunc.router import router as newfunc_router
from app.modules.newfunc.scheduler import start_scheduler, stop_scheduler
# 【纯本地玩法上云：盲盒/碎片/明信片/时光胶囊/商城下单】独立模块（additive）
from app.modules.play.router import router as play_router
from app.modules.play.init_tables import init_tables as init_play_tables
# 【管理后台】独立模块（additive：只新增 admin_logs / admin_reviews 两张表）
from app.modules.admin.router import router as admin_router
from app.modules.admin.init_tables import init_admin_tables
# 【支付】渠道抽象 + 订单/会员（只新增 pay_orders / user_vip 两张表）
from app.modules.pay.router import router as pay_router
from app.modules.pay.init_tables import init_pay_tables
# 【实时通话】声网 Agora 频道鉴权（无表结构；未配置时接口显式返回 503）
from app.modules.rtc.router import router as rtc_router
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期: 启动/关闭"""
    print(f"[{settings.app_name}] 启动中... 环境: {settings.app_env}")
    print(f"  数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    print(f"  Redis:  {settings.redis_host}:{settings.redis_port}")
    print(f"  AI模型: {settings.ai_model}")
    print(f"  CORS:   {settings.cors_origin_list}")
    # 【newfunc】启动独立推送定时任务（只读旧表，写入仅限新表）
    start_scheduler()
    # 羁绊碎片：首次启动自动建表（CREATE TABLE IF NOT EXISTS 幂等，不影响已有数据）
    BondService._auto_init()
    # 玩法上云：3 张新表自动补齐（checkfirst，已存在则跳过）
    init_play_tables()
    # 管理后台：日志 / 审核结果 两张新表
    init_admin_tables()
    # 支付：订单 / VIP 会员两张新表
    init_pay_tables()
    yield
    # 【newfunc】停调度
    stop_scheduler()
    # 【性能优化 + 安全加固】优雅关闭 httpx 连接池，释放 TLS 连接
    # 加 5s 总超时，避免活跃 SSE 连接导致应用关闭卡住
    try:
        await asyncio.wait_for(AIService.close_client(), timeout=5.0)
    except asyncio.TimeoutError:
        print("[main] AIService.close_client 超时，跳过")
    except Exception:
        pass
    print(f"[{settings.app_name}] 已关闭")


app = FastAPI(
    title=settings.app_name,
    description="AI虚拟角色情绪伙伴 - 后端API (情绪打卡/AI对话/正念练习/成长档案)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


# ---------- 全局异常处理 ----------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常拦截"""
    import traceback
    error_detail = traceback.format_exc() if settings.app_debug else str(exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {error_detail}" if settings.app_debug else "服务器内部错误",
            "data": None,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"code": 404, "message": "接口不存在", "data": None},
    )


# ---------- 中间件: 请求耗时记录 ----------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(
            status_code=500,
            content={"code": 500, "message": "请求处理异常", "data": None},
        )
    elapsed = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time"] = f"{elapsed}ms"
    return response


# ---------- 健康检查 ----------
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"code": 200, "message": "ok", "data": {"status": "healthy", "version": "2.0.0"}}


@app.get("/")
async def root():
    """根路径"""
    return {
        "code": 200,
        "message": f"欢迎使用{settings.app_name}API",
        "data": {
            "docs": "/docs",
            "endpoints": [
                "/api/v1/auth - 认证",
                "/api/v1/user - 用户",
                "/api/v1/habit - 习惯打卡",
                "/api/v1/emotion - 情绪记录",
                "/api/v1/mindfulness - 正念练习",
                "/api/v1/chat - AI对话",
                "/api/v1/stats - 统计分析",
                "/api/v1/archive - 成长档案",
                "/api/v1/habit-ai - 习惯AI联动",
                "/api/v1/companion - 陪伴模式",
                "/api/v1/moment - 朋友圈",
                "/api/v1/personality - 性格测评(云端)",
                "/api/v1/economy - 虚拟经济(云端)",
                "/api/v1/memory - 长效记忆(分层/角色隔离)",
                "/api/v1/persona - 角色人设(自捏/心情/扭蛋角色)",
                "/api/v1/proactive - 主动陪伴",
            ],
        },
    }


# ---------- 注册 API 路由 ----------
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(habit_router, prefix="/api/v1")
app.include_router(emotion_router, prefix="/api/v1")
app.include_router(mindfulness_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(archive_router, prefix="/api/v1")
app.include_router(habit_ai_router, prefix="/api/v1")
# voice_diary_router 已下线：无前端入口，保留源码以便后续接入真实 ASR 后再挂载
app.include_router(companion_router, prefix="/api/v1")
app.include_router(badge_router, prefix="/api/v1")
app.include_router(moment_router, prefix="/api/v1")
# 【四大新增模块】路由挂载
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(gacha_router, prefix="/api/v1")
app.include_router(world_router, prefix="/api/v1")
# 【性格测评上云】路由挂载
app.include_router(personality_router, prefix="/api/v1")
# 【虚拟经济上云】路由挂载
app.include_router(economy_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")
# 【陪伴感增强 v3】路由挂载
app.include_router(memory_router, prefix="/api/v1")
app.include_router(persona_router, prefix="/api/v1")
app.include_router(proactive_router, prefix="/api/v1")
app.include_router(bond_router, prefix="/api/v1")  # ↓↓↓ 羁绊碎片 ↓↓↓

# ↓↓↓ 模块4 新增：AI 多人群聊路由 ↓↓↓
from app.api.v1.group_chat import router as group_chat_router
app.include_router(group_chat_router, prefix="/api/v1")
# ↑↑↑ 模块4 新增结束 ↑↑↑
# 【小想法 · 共鸣匹配】路由挂载
app.include_router(idea_router, prefix="/api/v1")
# 【专注 · AI陪伴监督】路由挂载
app.include_router(focus_router, prefix="/api/v1")
# 【newfunc 增量功能】路由挂载（独立前缀，避免与旧接口冲突）
app.include_router(newfunc_router, prefix="/api/newfunc")
# 【纯本地玩法上云】路由挂载
app.include_router(play_router, prefix="/api/v1")
# 【管理后台】路由挂载（/api/v1/admin/*）
app.include_router(admin_router, prefix="/api/v1")
# 【支付】路由挂载（/api/v1/pay/*）
app.include_router(pay_router, prefix="/api/v1")
# 【实时通话】路由挂载（/api/v1/rtc/*）
app.include_router(rtc_router, prefix="/api/v1")


# ---------- 静态文件服务 ----------
_uploads_path = pathlib.Path("uploads")
_uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_path)), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
