# -*- coding: utf-8 -*-
"""
「专注」模块角色层
======================

沿用现有 App 角色体系（ai_service.ROLE_PROMPTS 的 7 个角色 ID），
不新增独立角色库；这里只补充每个角色在「监督陪伴」语境下的
话术风格与本地鼓励台词（离线可用，专注页轮播零延迟）。
"""

# 与 app/services/ai_service.py 的 ROLE_PROMPTS key 完全对齐
ROLE_IDS = ["cute", "gentle", "serious", "energetic", "companion", "mentor", "friend"]

ROLE_META = {
    "cute":      {"name": "林夕", "style": "元气小太阳，夸夸不停"},
    "gentle":    {"name": "温柔", "style": "轻声细语，稳稳陪着你"},
    "serious":   {"name": "认真", "style": "严谨自律，监督执行"},
    "energetic": {"name": "元气", "style": "热情加油官，点燃干劲"},
    "companion": {"name": "林夕", "style": "温柔陪伴，愿意倾听"},
    "mentor":    {"name": "明理", "style": "理性引导，拆解思路"},
    "friend":    {"name": "阿澈", "style": "老朋友，松弛不施压"},
}

# 每个角色的监督/鼓励话术风格（本地模板，按场景取用）
_ROLE_LINES = {
    "cute": {
        "step_done": ["哇，这一步完成啦！你真的很棒哦～", "完成！这就是小小的胜利，继续冲！"],
        "focus_on": ["我会一直在这儿陪着你专注～", "深呼吸，此刻只做眼前这一件事。", "你专注的样子最闪亮啦！"],
        "idle": "要不要从「收拾桌面 3 分钟」开始？动起来就会有状态！",
    },
    "gentle": {
        "step_done": ["很好，慢慢来，你已经往前走了。", "完成得不错，给自己一点温柔的时间。"],
        "focus_on": ["不着急，一步一步来，我陪着。", "累了就歇一下，回来就好。", "此刻的安静很珍贵。"],
        "idle": "不知道做什么的话，先喝口水，我们挑一件最小的事开始。",
    },
    "serious": {
        "step_done": ["按计划完成，很好。下一步继续。", "执行到位。保持这个节奏。"],
        "focus_on": ["专注当下，不要分心。", "进度在推进，继续。", "把手机放下，眼前的任务最重要。"],
        "idle": "先列出今天必做的一件事，然后立刻开始前 5 分钟。",
    },
    "energetic": {
        "step_done": ["完成！！太棒了，这个势头保持住！", "漂亮！下一关继续冲！"],
        "focus_on": ["燃烧起来！就现在！", "你可以的，全神贯注！", "这波专注稳稳的！"],
        "idle": "来！先做 3 分钟热热身，状态马上就来了！",
    },
    "companion": {
        "step_done": ["完成了，我看到了你的努力。", "很好，一步一步，我们慢慢推进。"],
        "focus_on": ["我在这里陪你，安心专注。", "有什么卡住的地方随时告诉我。", "慢慢来，专注眼前。"],
        "idle": "如果暂时不想动，也可以先聊聊今天的状态。",
    },
    "mentor": {
        "step_done": ["这一步完成，逻辑链推进了一格。", "不错，拆解有效。继续下一步。"],
        "focus_on": ["保持节奏，注意方法。", "卡住的话换个角度试试。", "专注效率最高的时段。"],
        "idle": "先从最简单的子问题入手，降低启动成本。",
    },
    "friend": {
        "step_done": ["稳了兄弟，这步搞定。", "不错啊，继续继续。"],
        "focus_on": ["我在这儿，你只管专注。", "别磨蹭啦，就这一小步。", "状态不错，保持住。"],
        "idle": "随便挑一件小事先做起来，比如收拾下桌子。",
    },
}


def get_persona_prompt(role_id: str) -> str:
    """角色补充人设（叠加在监督陪伴 system prompt 之后）"""
    meta = ROLE_META.get(role_id, ROLE_META["companion"])
    return f"你的角色名是「{meta['name']}」，风格：{meta['style']}。"


def encouragement(role_id: str, scene: str, task_hint: str = "") -> str:
    """取一条本地鼓励/监督台词（离线可用）"""
    lines = _ROLE_LINES.get(role_id, _ROLE_LINES["companion"]).get(scene)
    if scene == "idle":
        return lines if isinstance(lines, str) else "先从最小的一步开始吧。"
    if not lines:
        lines = ["继续，做得很好。"]
    text = lines[hash(task_hint) % len(lines)] if task_hint else lines[0]
    return text
