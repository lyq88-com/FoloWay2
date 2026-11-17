# -*- coding: utf-8 -*-
"""
「专注」模块 AI 能力层
======================

全部通过现有 AIService.chat_non_stream 通道调用大模型（复用，不改原通道），
AI 不可用 / 返回不合法时一律降级为本地规则兜底，保证核心链路永远可用。

能力清单：
  generate_plan      备考/目标计划生成（分阶段 → 每日任务）
  split_big_task     大任务 → 极小可立即动手的单步列表
  companion_reply    监督陪伴人设聊天（含日程指令解析 createRemindFromChat）
  encourage_line     鼓励台词（完成步骤 / 专注页轮播）
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.services.ai_service import AIService

from .persona import (
    ROLE_IDS, get_persona_prompt, encouragement,
)

# AI 单次调用超时（秒）——备考计划较长，放宽一些
AI_TIMEOUT_HINT = "请严格只输出 JSON，不要输出任何解释文字。"


def _call_ai(system: str, user_content: str) -> Optional[str]:
    """同步调用现有 AI 通道；任何异常返回 None（调用方自行降级）"""
    try:
        messages = AIService.build_context_messages([], system, user_content, max_rounds=2)
        import asyncio
        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # FastAPI 同步路由里通常拿不到 running loop；用新线程跑
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(asyncio.run, AIService.chat_non_stream(messages))
                    return fut.result(timeout=60)
        except RuntimeError:
            pass
        return asyncio.run(AIService.chat_non_stream(messages))
    except Exception:
        return None


def _extract_json(text: str):
    """从模型输出里抠出 JSON（容忍 ```json 包裹 / 前后杂文字）"""
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        try:
            return json.loads(m.group(0).replace("，", ",").replace("：", ":"))
        except Exception:
            return None


# ============================================================
# 1. 备考 / 目标计划生成
# ============================================================
PLAN_SYSTEM = (
    "你是备考规划专家。根据用户的考试信息生成分阶段备考计划。\n"
    "输出 JSON：{\"phases\":[{\"name\":\"阶段名\",\"days\":[{\"title\":\"当日任务\",\"minutes\":45,\"tag\":\"学习\"}]}]}\n"
    "要求：2~4 个阶段；每阶段 5~10 个每日任务；minutes 为该日建议学习分钟数(15~180)；"
    "tag 只能是 学习/工作/生活/运动/其他 之一；任务要具体可执行。\n"
    + AI_TIMEOUT_HINT
)


def generate_plan(exam_type: str, exam_date: str, weakness: str,
                  daily_minutes: int, days_left: int = 30) -> Dict:
    """
    生成备考计划。返回：
      { "phases": [...], "source": "ai"|"fallback" }
    phases[].days[] 会被 service 层逐日落成 focus_task + focus_step + focus_remind。
    """
    days_left = max(7, min(int(days_left or 30), 365))
    user_content = (
        f"考试类型：{exam_type}\n考试日期：{exam_date}（距今约 {days_left} 天）\n"
        f"薄弱点：{weakness or '无特别说明'}\n每天可用时长：{daily_minutes} 分钟\n"
        f"请给出到考试前的分阶段计划，每阶段 {max(3, days_left // 7)} 个左右的每日任务。"
    )
    raw = _call_ai(PLAN_SYSTEM, user_content)
    data = _extract_json(raw) if raw else None
    if not data or not isinstance(data.get("phases"), list) or not data["phases"]:
        return {"phases": _fallback_plan(exam_type, days_left, daily_minutes), "source": "fallback"}
    # 清洗：保证每个 phase.days 都是合法列表
    phases = []
    for p in data["phases"][:4]:
        if not isinstance(p, dict):
            continue
        days = []
        for d in (p.get("days") or [])[:14]:
            if isinstance(d, dict) and d.get("title"):
                try:
                    minutes = int(d.get("minutes") or daily_minutes)
                except Exception:
                    minutes = daily_minutes
                days.append({
                    "title": str(d["title"])[:80],
                    "minutes": max(10, min(minutes, 180)),
                    "tag": d.get("tag") if d.get("tag") in ("学习", "工作", "生活", "运动", "其他") else "学习",
                })
        if days:
            phases.append({"name": str(p.get("name") or "阶段")[:30], "days": days})
    if not phases:
        return {"phases": _fallback_plan(exam_type, days_left, daily_minutes), "source": "fallback"}
    return {"phases": phases, "source": "ai"}


def _fallback_plan(exam_type: str, days_left: int, daily_minutes: int) -> List[Dict]:
    """AI 不可用时的本地兜底模板：三阶段通用备考节奏"""
    m = daily_minutes or 45
    return [{
        "name": "基础巩固（第1周）",
        "days": [
            {"title": f"{exam_type}：梳理考纲，列出知识清单", "minutes": m, "tag": "学习"},
            {"title": f"{exam_type}：过一遍核心概念，标记不熟点", "minutes": m, "tag": "学习"},
            {"title": "错题本建立：整理近期练习错题", "minutes": max(15, m // 2), "tag": "学习"},
            {"title": "基础题专项：做一组基础题并核对", "minutes": m, "tag": "学习"},
            {"title": "周复盘：回顾本周掌握情况", "minutes": max(15, m // 2), "tag": "学习"},
        ],
    }, {
        "name": "专项突破（第2周起）",
        "days": [
            {"title": "薄弱点专项练习（第1组）", "minutes": m, "tag": "学习"},
            {"title": "薄弱点专项练习（第2组）", "minutes": m, "tag": "学习"},
            {"title": "真题限时演练一套（分半完成）", "minutes": min(120, m * 2), "tag": "学习"},
            {"title": "真题错题分析并归纳套路", "minutes": m, "tag": "学习"},
            {"title": "背诵记忆类内容一轮", "minutes": max(20, m // 2), "tag": "学习"},
        ],
    }, {
        "name": "冲刺模考（考前）",
        "days": [
            {"title": "全真模拟考试一次", "minutes": min(120, m * 2), "tag": "学习"},
            {"title": "模拟卷复盘：错题逐题过", "minutes": m, "tag": "学习"},
            {"title": "高频考点快速串讲复习", "minutes": max(20, m // 2), "tag": "学习"},
            {"title": "调整作息，轻量复习保持手感", "minutes": max(15, m // 3), "tag": "学习"},
        ],
    }]


# ============================================================
# 2. 大任务拆解（分步引导核心）
# ============================================================
SPLIT_SYSTEM = (
    "你是启动困难拯救者。把用户的大任务切成 5~8 个极小、可以立刻动手的单步。"
    "每步必须具体到不需要任何决策就能开始（例如不是「复习数学」而是「打开课本第3章，抄写2个公式」）。\n"
    "输出 JSON：{\"steps\":[{\"content\":\"...\",\"minutes\":5}]}\n"
    "minutes 为该步建议分钟数(2~30)。\n" + AI_TIMEOUT_HINT
)


def split_big_task(task_text: str, mode: str = "simple") -> Dict:
    """大任务 → 单步列表。返回 {steps:[{content,minutes}], source}"""
    style = (
        "简单模式：每步 5 分钟以内，门槛极低。\n"
        if mode == "simple" else
        "心流模式：允许 10~30 分钟的连续步骤，节奏更紧凑。\n"
    )
    raw = _call_ai(SPLIT_SYSTEM, style + f"任务：{task_text}")
    data = _extract_json(raw) if raw else None
    steps = []
    if data and isinstance(data.get("steps"), list):
        for s in data["steps"][:8]:
            if isinstance(s, dict) and s.get("content"):
                try:
                    minutes = int(s.get("minutes") or 5)
                except Exception:
                    minutes = 5
                cap = 30 if mode != "simple" else 8
                steps.append({"content": str(s["content"])[:120],
                              "minutes": max(2, min(minutes, cap))})
    if not steps:
        steps = _fallback_steps(task_text, mode)
    return {"steps": steps, "source": "ai" if data else "fallback"}


def _fallback_steps(task_text: str, mode: str) -> List[Dict]:
    """本地兜底：通用启动模板"""
    base = mode == "simple" and 4 or 12
    return [
        {"content": f"收拾出一块干净的区域，准备好「{task_text[:20]}」需要的东西", "minutes": 3},
        {"content": f"花 2 分钟写下关于「{task_text[:20]}」现在想到的 3 件事", "minutes": 2},
        {"content": f"从最容易的一小处开始动手做 5 分钟", "minutes": 5},
        {"content": "回顾刚才做的，写下下一步最想推进的一点", "minutes": 3},
        {"content": f"再投入 {base} 分钟继续推进", "minutes": base},
    ]


# ============================================================
# 3. 监督陪伴聊天（含日程指令解析）
# ============================================================
COMPANION_SYSTEM_PREFIX = (
    "你现在是用户的「监督陪伴人」。特点：温和但说到做到，会帮用户把想法变成可执行安排。\n"
    "你可以执行两类指令：创建待办任务、设置提醒。当用户消息里包含明确安排意图时"
    "（例如「提醒我九点四十五收拾房间」「明天下午三点写作业」「每天晚上背30个单词」），"
    "除了正常回复，还要在末尾追加一行指令 JSON：\n"
    "<<<CMD>>>{\"title\":\"收拾房间\",\"remind\":\"HH:MM\",\"remind_at\":\"YYYY-MM-DD HH:MM 或空\",\"tag\":\"学习\"}\n"
    "解析规则：只提取一件最明确的事；相对时间（今晚八点）按当前时间换算为具体日期时刻；"
    "没有明确时刻则 remind_at 留空、remind 填每日 HH:MM（若无每日意图也留空）。\n"
    "当前时间：{now}。回复保持简短自然（不超过 80 字），先回应情绪与内容，再确认安排。"
)


def companion_reply(role_id: str, user_text: str,
                    history: Optional[List[Dict]] = None) -> Dict:
    """
    监督陪伴人设回复。
    返回 { reply, cmd: {title, remind, remind_at, tag} | None, source }
    """
    system = COMPANION_SYSTEM_PREFIX.replace("{now}", datetime.now().strftime("%Y-%m-%d %H:%M %A")) \
        + "\n" + get_persona_prompt(role_id)
    msgs = AIService.build_context_messages(history or [], system, user_text, max_rounds=10)
    raw = None
    try:
        import asyncio
        raw = asyncio.run(AIService.chat_non_stream(msgs))
    except Exception:
        raw = None
    reply = (raw or "").strip()
    cmd = None
    m = re.search(r"<<<CMD>>>\s*(\{[\s\S]*?\})", reply)
    if m:
        try:
            c = json.loads(m.group(1))
            cmd = {
                "title": str(c.get("title") or "")[:80],
                "remind": str(c.get("remind") or ""),
                "remind_at": str(c.get("remind_at") or ""),
                "tag": c.get("tag") if c.get("tag") in ("学习", "工作", "生活", "运动", "其他") else "学习",
            }
            reply = reply[:m.start()].strip()
        except Exception:
            cmd = None
    if not reply:
        reply = f"收到，{encouragement(role_id, 'idle')}"
    return {"reply": reply, "cmd": cmd, "source": "ai" if raw else "fallback"}


# ============================================================
# 4. 鼓励台词（本地生成，不依赖远端，专注页轮播零延迟）
# ============================================================
def encourage_line(role_id: str, scene: str = "step_done",
                   task_hint: str = "") -> str:
    """scene: step_done(完成一步) / focus_on(专注中轮播) / idle(空态推荐)"""
    return encouragement(role_id, scene, task_hint)


def recommend_small_tasks() -> List[Dict]:
    """空态推荐：不知道做什么时给的小任务候选"""
    return [
        {"title": "收拾桌面 3 分钟", "minutes": 3, "tag": "生活"},
        {"title": "复习一小段知识点（任选）", "minutes": 5, "tag": "学习"},
        {"title": "起身接杯水 + 拉伸 1 分钟", "minutes": 2, "tag": "运动"},
        {"title": "写 3 行今日待办", "minutes": 3, "tag": "生活"},
        {"title": "背 5 个单词", "minutes": 5, "tag": "学习"},
    ]
