# -*- coding: utf-8 -*-
"""
世界世界观核心服务（模块1 + 模块4）
封装 AI 笔记、AI 互评、角色关系、打卡联动等可复用逻辑，
路由层(app.api.v1.world)与打卡联动(habit checkin)统一调用本服务，
保证"一处实现、处处一致"，且联动逻辑便于 try/except 隔离。

约定：本服务中 member_id 均指 world_roles.id（世界成员ID），
自设角色与AI角色统一用它标识；WorldRole.role_id 才是 ai_roles 真实ID。
"""
import random
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.chat import AIRole
from app.models.world import (
    World, WorldRole, WorldNote, WorldNoteComment,
    WorldPlot, WorldPlotUnlock, WorldRelation,
)


# ============================== 成员管理 ==============================
def get_member(db: Session, world_id: int, member_id: int) -> Optional[WorldRole]:
    return db.query(WorldRole).filter(
        WorldRole.id == member_id, WorldRole.world_id == world_id,
        WorldRole.is_active == 1,
    ).first()


# AI角色类型 → 头像emoji
ROLE_TYPE_EMOJI = {
    "cute": "🐰", "gentle": "🌷", "serious": "📖",
    "energetic": "⚡", "companion": "💜", "mentor": "🧭", "friend": "🍀",
}


def add_ai_member(db: Session, world_id: int, role_id: int) -> Optional[WorldRole]:
    """把一个系统 AI 角色加入世界（已在则直接返回该成员）"""
    existed = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.role_id == role_id,
        WorldRole.join_type == "ai", WorldRole.is_active == 1,
    ).first()
    if existed:
        return existed
    ai = db.query(AIRole).filter(AIRole.id == role_id, AIRole.status == 1).first()
    if not ai:
        return None
    m = WorldRole(
        world_id=world_id, role_id=ai.id, role_name=ai.name,
        role_avatar=ROLE_TYPE_EMOJI.get(ai.role_type, "🤖"),
        is_custom=0, join_type="ai", is_active=1,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def add_custom_member(db: Session, world_id: int, name: str) -> WorldRole:
    """加入自设角色（用 emoji 作头像）"""
    emojis = ["🐱", "🦊", "🐻", "🌟", "🌙", "🐰", "🐼", "🦉"]
    m = WorldRole(
        world_id=world_id, role_id=0, role_name=name,
        role_avatar=random.choice(emojis), is_custom=1,
        join_type="ai", is_active=1,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def add_user_member(db: Session, world_id: int, user_id: int,
                    name: str, avatar: str = "") -> WorldRole:
    """加入/返回用户成员"""
    existed = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.user_id == user_id,
        WorldRole.join_type == "user", WorldRole.is_active == 1,
    ).first()
    if existed:
        return existed
    m = WorldRole(
        world_id=world_id, role_id=0, role_name=name, role_avatar=avatar,
        is_custom=0, join_type="user", user_id=user_id, is_active=1,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def list_ai_members(db: Session, world_id: int) -> List[WorldRole]:
    return db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.join_type == "ai",
        WorldRole.is_active == 1,
    ).all()


# ============================== AI 笔记 ==============================
def create_ai_note(db: Session, world_id: int, member: WorldRole,
                   content: str, note_type: str = "normal",
                   related_user_id: int = 0,
                   related_habit_id: int = 0) -> WorldNote:
    note = WorldNote(
        world_id=world_id, author_role_id=member.id, author_user_id=0,
        author_name=member.role_name, author_avatar=member.role_avatar,
        note_type=note_type, content=content,
        related_user_id=related_user_id, related_habit_id=related_habit_id,
        status=1,
    )
    db.add(note)
    world = db.query(World).filter(World.id == world_id).first()
    if world:
        world.note_count += 1
    db.commit()
    db.refresh(note)
    return note


# ============================== 角色关系 ==============================
def _label_by_score(score: int) -> str:
    if score <= 0:
        return "初识"
    if score <= 3:
        return "点头之交"
    if score <= 7:
        return "相熟"
    if score <= 12:
        return "好友"
    return "挚友"


def bump_relation(db: Session, world_id: int, member_a_id: int, member_b_id: int):
    """同世界两个 AI 角色互动 → 关系升温"""
    if member_a_id == member_b_id:
        return
    a, b = sorted([member_a_id, member_b_id])
    rel = db.query(WorldRelation).filter(
        WorldRelation.world_id == world_id,
        WorldRelation.role_a_id == a, WorldRelation.role_b_id == b,
    ).first()
    if not rel:
        rel = WorldRelation(
            world_id=world_id, role_a_id=a, role_b_id=b,
            relation_label="初识", score=0,
        )
        db.add(rel)
    rel.score += 1
    rel.relation_label = _label_by_score(rel.score)
    db.commit()


# ============================== 用户评论 → AI 回复 + AI 互评 ==============================
# AI 作者回复用户评论的话术（Mock；接入LLM时替换）
_REPLY_TO_USER = [
    "谢谢你的留言呀，看到你的消息心情都变好了~",
    "嗯嗯，你说得对，我们在这个世界里一起慢慢走。",
    "被你这样一说，我也觉得很温暖呢。",
    "你的想法很特别，我记住啦，下次再聊~",
]
# 其他 AI 角色"路过"评论的话术（触发 AI 互评与关系变化）
_SIDE_COMMENTS = [
    "我刚好路过，也赞同这个说法~",
    "你们聊得好热闹，我也来插一句：今天也是值得的一天。",
    "这倒是提醒我了，彼此陪伴本来就是这个世界的规则呀。",
    "附议！希望大家都能被温柔以待。",
]


def comment_and_trigger_ai(db: Session, note: WorldNote,
                           user_member: WorldRole,
                           content: str, reply_to_id: int) -> List[WorldNoteComment]:
    """
    用户评论后：
    1) 落用户评论；
    2) 若笔记是 AI 发的 → AI 作者回复用户；
    3) 70% 概率另一位 AI 成员跟评 → 与作者关系升温（AI互评）；
       若笔记是用户发的，则随机一位 AI 直接跟评欢迎。
    返回新生成的评论列表（顺序：用户评论[, AI回复][, AI跟评]）
    """
    created = []
    user_comment = WorldNoteComment(
        note_id=note.id, author_role_id=0, author_user_id=user_member.user_id,
        author_name=user_member.role_name, author_avatar=user_member.role_avatar,
        content=content, reply_to_id=reply_to_id, status=1,
    )
    db.add(user_comment)
    created.append(user_comment)

    ai_members = list_ai_members(db, note.world_id)

    # —— AI 作者回复 ——
    author_member = None
    if note.author_role_id:
        author_member = get_member(db, note.world_id, note.author_role_id)
        if author_member:
            ai_reply = WorldNoteComment(
                note_id=note.id, author_role_id=author_member.id, author_user_id=0,
                author_name=author_member.role_name,
                author_avatar=author_member.role_avatar,
                content=random.choice(_REPLY_TO_USER),
                reply_to_id=0, status=1,
            )
            db.add(ai_reply)
            created.append(ai_reply)

    # —— AI 互评 / 欢迎跟评 ——
    trigger_side = (author_member is not None and random.random() < 0.7) \
        or (author_member is None)
    if trigger_side and ai_members:
        others = [m for m in ai_members if not author_member or m.id != author_member.id]
        if others:
            sider = random.choice(others)
            side = WorldNoteComment(
                note_id=note.id, author_role_id=sider.id, author_user_id=0,
                author_name=sider.role_name, author_avatar=sider.role_avatar,
                content=randomchoice_safe(),
                reply_to_id=0, status=1,
            )
            db.add(side)
            created.append(side)
            # 关系变化：AI 笔记则作者↔跟评者升温；用户笔记则不产生 AI 关系
            if author_member:
                bump_relation(db, note.world_id, author_member.id, sider.id)

    note.comment_count += len(created)
    db.commit()
    for c in created:
        db.refresh(c)
    return created


def randomchoice_safe() -> str:
    """抽取跟评话术（独立函数便于单测替换）"""
    return random.choice(_SIDE_COMMENTS)


# ============================== 剧情碎片 ==============================
def create_default_plots(db: Session, world: World):
    """创建世界时生成 3 段默认剧情，打卡数门槛为 target / 2target / 3target"""
    t = world.checkin_target
    presets = [
        ("初遇之章", f"在「{world.name}」里完成 {t} 次打卡后，世界向你展露第一缕光：伙伴们开始记住你的名字。"),
        ("相知之章", f"完成 {t * 2} 次打卡，世界的脉络逐渐清晰，隐藏的小路为你敞开。"),
        ("同行之章", f"完成 {t * 3} 次打卡，你已成为这个世界真正的同行者，所有伙伴为你点亮星河。"),
    ]
    for i, (title, content) in enumerate(presets):
        db.add(WorldPlot(
            world_id=world.id, title=title, content=content,
            required_checkins=t * (i + 1), sort_order=i,
        ))
    db.commit()


def user_world_checkin_count(db: Session, world_id: int, user_id: int) -> int:
    """用户在某个世界内的打卡次数（以 AI 打卡反馈笔记计数）"""
    return db.query(WorldNote).filter(
        WorldNote.world_id == world_id,
        WorldNote.note_type == "feedback",
        WorldNote.related_user_id == user_id,
        WorldNote.status == 1,
    ).count()


# ============================== 打卡联动（M5 调用入口） ==============================
_FEEDBACK_TEMPLATES = [
    "看到 {user} 今天完成了「{habit}」，真为TA开心——在这个世界里，每份坚持都在发光。",
    "{user} 又来打卡啦！「{habit}」达成，连世界的风都在为TA鼓掌。",
    "悄悄记一笔：{user} 今天也没有放弃「{habit}」，这样的人最耀眼了。",
    "{user} 完成「{habit}」的样子被我看到咯，这就是陪伴的意义呀。",
]


def handle_checkin(db: Session, user_id: int, habit_name: str,
                   user_name: str, habit_id: int = 0) -> dict:
    """
    打卡成功后联动（必须在 try/except 中调用，失败不影响打卡本身）：
    1) 遍历用户加入的所有世界，世界累计打卡 +1；
    2) 随机一位 AI 成员发布打卡反馈笔记（note_type=feedback）；
    3) 依据用户在该世界的打卡数解锁剧情碎片。
    返回联动摘要（仅用于日志/调试）。
    """
    # 用户作为成员所在世界
    memberships = db.query(WorldRole).filter(
        WorldRole.user_id == user_id, WorldRole.join_type == "user",
        WorldRole.is_active == 1,
    ).all()

    summary = {"worlds": [], "unlocked": []}
    for mem in memberships:
        world = db.query(World).filter(
            World.id == mem.world_id, World.status == 1
        ).first()
        if not world:
            continue
        world.checkin_total += 1

        ai_members = list_ai_members(db, world.id)
        if ai_members:
            speaker = random.choice(ai_members)
            content = random.choice(_FEEDBACK_TEMPLATES).format(
                user=user_name, habit=habit_name
            )
            create_ai_note(
                db, world.id, speaker, content,
                note_type="feedback", related_user_id=user_id,
                related_habit_id=habit_id,
            )

        # 剧情解锁检查
        count_after = user_world_checkin_count(db, world.id, user_id)
        plots = db.query(WorldPlot).filter(
            WorldPlot.world_id == world.id,
            WorldPlot.required_checkins <= count_after,
        ).order_by(WorldPlot.sort_order.asc()).all()
        unlocked_ids = {u.plot_id for u in db.query(WorldPlotUnlock).filter(
            WorldPlotUnlock.world_id == world.id,
            WorldPlotUnlock.user_id == user_id,
        ).all()}
        for p in plots:
            if p.id not in unlocked_ids:
                db.add(WorldPlotUnlock(
                    world_id=world.id, user_id=user_id, plot_id=p.id
                ))
                summary["unlocked"].append({"world_id": world.id, "plot_id": p.id})
        db.commit()
        summary["worlds"].append(world.id)

    return summary
