# -*- coding: utf-8 -*-
"""
虚拟世界 + AI角色互动笔记 API（模块1 + 模块4）
端点：
  POST   /world/create                 创建世界（公开/私人，可带AI角色与自设角色）
  GET    /world/list?tab=public|mine   公开世界列表 / 我的世界
  GET    /world/detail/{id}            世界详情(成员/剧情解锁/我的打卡数)
  POST   /world/join                   加入公开世界
  POST   /world/add-role/{id}          追加 AI 角色 / 自设角色
  POST   /world/leave/{id}             离开（创建者则删除世界）
  GET    /world/members/{id}           成员列表
  POST   /world/note/{id}              用户发布笔记（AI会跟评）
  GET    /world/notes/{id}             笔记流
  POST   /world/comment/{note_id}      用户评论（AI回复 + AI互评 + 关系变化）
  GET    /world/comments/{note_id}     评论列表
  GET    /world/relations/{id}         世界内 AI 角色关系
  GET    /world/ai-interactions/{id}   同世界 AI 互动消息（打卡反馈+AI互评）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.chat import AIRole
from app.models.world import (
    World, WorldRole, WorldNote, WorldNoteComment,
    WorldPlot, WorldPlotUnlock, WorldRelation,
)
from app.schemas.common import ResponseBase
from app.schemas.world import (
    WorldCreate, WorldUpdate, JoinWorldRequest,
    AddRoleRequest, NoteCreate, CommentCreate,
)
from app.middleware.auth import get_current_user
from app.services import world_service as svc
# 【习惯-伙伴融合】习惯经历 → 剧情碎片素材
from app.services.habit_companion_service import HabitCompanionService as HCS

router = APIRouter(prefix="/world", tags=["虚拟世界"])


# ---------- 访问权限：私人世界仅创建者/成员可见 ----------
def _can_view(db: Session, world: World, user_id: int) -> bool:
    if world.is_public == 1:
        return True
    if world.creator_id == user_id:
        return True
    return db.query(WorldRole).filter(
        WorldRole.world_id == world.id, WorldRole.user_id == user_id,
        WorldRole.join_type == "user", WorldRole.is_active == 1,
    ).first() is not None


def _world_brief(w: World) -> dict:
    return {
        "id": w.id, "name": w.name, "description": w.description,
        "cover": w.cover, "is_public": w.is_public,
        "member_count": w.member_count, "note_count": w.note_count,
        "checkin_target": w.checkin_target, "checkin_total": w.checkin_total,
        "creator_id": w.creator_id,
        "created_at": w.created_at.strftime("%Y-%m-%d %H:%M") if w.created_at else "",
    }


# ============ 0. 可入驻的AI角色列表(创建世界时选择) ============
@router.get("/ai-roles")
def list_ai_roles(user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    roles = db.query(AIRole).filter(AIRole.status == 1).all()
    return ResponseBase.success([{
        "id": r.id, "name": r.name,
        "avatar": svc.ROLE_TYPE_EMOJI.get(r.role_type, "🤖"),
        "description": r.description or r.personality or "",
    } for r in roles])


# ============ 1. 创建世界 ============
@router.post("/create")
def create_world(payload: WorldCreate,
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    # ↓↓↓ 安全合规批次：世界创建内容前置安全校验 ↓↓↓
    from app.utils.content_security import ContentSecurity
    for _field, _text in (("名称", payload.name or ""), ("简介", payload.description or ""),
                          ("规则", payload.rules or "")):
        _sec = ContentSecurity.check_user_text(_text)
        if not _sec["ok"]:
            return ResponseBase.error(f"世界{_field}{_sec['reason'].split('，')[-1]}", 400)
    # ↑↑↑ 新增结束 ↑↑↑

    world = World(
        creator_id=user_id, name=payload.name, description=payload.description,
        rules=payload.rules, is_public=payload.is_public,
        checkin_target=payload.checkin_target, member_count=1, status=1,
    )
    db.add(world)
    db.commit()
    db.refresh(world)

    # 创建者作为用户成员加入
    svc.add_user_member(db, world.id, user_id, user.nickname or user.username, "")
    # 加入选择的 AI 角色
    for rid in payload.role_ids:
        svc.add_ai_member(db, world.id, rid)
    # 加入自设角色
    for name in payload.custom_roles:
        name = name.strip()
        if name:
            svc.add_custom_member(db, world.id, name)
    # 生成默认剧情碎片
    svc.create_default_plots(db, world)

    # 更新成员数
    member_num = db.query(WorldRole).filter(
        WorldRole.world_id == world.id, WorldRole.is_active == 1
    ).count()
    world.member_count = member_num
    db.commit()
    return ResponseBase.success(_world_brief(world))


# ============ 2. 世界列表 ============
@router.get("/list")
def list_worlds(tab: str = "public",
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    if tab == "mine":
        # 我创建的 + 我加入的
        created = db.query(World).filter(
            World.creator_id == user_id, World.status == 1
        ).order_by(World.created_at.desc()).all()
        joined_ids = [m.world_id for m in db.query(WorldRole).filter(
            WorldRole.user_id == user_id, WorldRole.join_type == "user",
            WorldRole.is_active == 1,
        ).all()]
        joined = db.query(World).filter(
            World.id.in_(joined_ids or [-1]), World.creator_id != user_id,
            World.status == 1
        ).all()
        worlds = list(created) + list(joined)
    else:
        worlds = db.query(World).filter(
            World.is_public == 1, World.status == 1
        ).order_by(World.member_count.desc(), World.created_at.desc()).limit(50).all()
    return ResponseBase.success([_world_brief(w) for w in worlds])


# ============ 3. 世界详情 ============
@router.get("/detail/{world_id}")
def detail_world(world_id: int,
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world:
        return ResponseBase.error("世界不存在", 404)
    if not _can_view(db, world, user_id):
        return ResponseBase.error("这是私人世界，你无权访问", 403)

    members = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.is_active == 1
    ).all()
    unlocked_ids = {u.plot_id for u in db.query(WorldPlotUnlock).filter(
        WorldPlotUnlock.world_id == world_id, WorldPlotUnlock.user_id == user_id
    ).all()}
    plots = db.query(WorldPlot).filter(
        WorldPlot.world_id == world_id
    ).order_by(WorldPlot.sort_order.asc()).all()

    joined = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.user_id == user_id,
        WorldRole.join_type == "user", WorldRole.is_active == 1,
    ).first()

    return ResponseBase.success({
        "world": _world_brief(world),
        "rules": world.rules or "",
        "joined": joined is not None,
        "members": [{
            "id": m.id, "role_name": m.role_name, "role_avatar": m.role_avatar,
            "join_type": m.join_type, "user_id": m.user_id, "is_custom": m.is_custom,
        } for m in members],
        "my_checkin_count": svc.user_world_checkin_count(db, world_id, user_id),
        "plots": [{
            "id": p.id, "title": p.title, "content": p.content,
            "required_checkins": p.required_checkins,
            "unlocked": p.id in unlocked_ids,
        } for p in plots],
    })


# ============ 4. 加入公开世界 ============
@router.post("/join")
def join_world(payload: JoinWorldRequest,
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    world = db.query(World).filter(
        World.id == payload.world_id, World.status == 1
    ).first()
    if not world:
        return ResponseBase.error("世界不存在", 404)
    if world.is_public != 1:
        return ResponseBase.error("私人世界不可加入", 403)

    user = db.query(User).filter(User.id == user_id).first()
    svc.add_user_member(db, world.id, user_id, user.nickname or user.username, "")
    world.member_count = db.query(WorldRole).filter(
        WorldRole.world_id == world.id, WorldRole.is_active == 1
    ).count()
    db.commit()
    return ResponseBase.success({"id": world.id, "joined": True})


# ============ 5. 追加 AI / 自设角色（仅创建者） ============
@router.post("/add-role/{world_id}")
def add_role(world_id: int, payload: AddRoleRequest,
             user_id: int = Depends(get_current_user),
             db: Session = Depends(get_db)):
    world = db.query(World).filter(
        World.id == world_id, World.status == 1
    ).first()
    if not world or world.creator_id != user_id:
        return ResponseBase.error("仅世界创建者可以添加角色", 403)

    if payload.role_id:
        m = svc.add_ai_member(db, world_id, payload.role_id)
    elif payload.custom_name.strip():
        m = svc.add_custom_member(db, world_id, payload.custom_name.strip())
    else:
        return ResponseBase.error("请选择AI角色或填写自设角色名", 400)
    if not m:
        return ResponseBase.error("AI角色不存在", 400)

    world.member_count = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.is_active == 1
    ).count()
    db.commit()
    return ResponseBase.success({"id": m.id, "role_name": m.role_name})


# ============ 6. 离开 / 删除世界 ============
@router.post("/leave/{world_id}")
def leave_world(world_id: int,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    world = db.query(World).filter(
        World.id == world_id, World.status == 1
    ).first()
    if not world:
        return ResponseBase.error("世界不存在", 404)

    if world.creator_id == user_id:
        # 创建者离开 = 删除整个世界（软删除）
        world.status = 0
        db.commit()
        return ResponseBase.success({"deleted": True})

    mem = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.user_id == user_id,
        WorldRole.join_type == "user", WorldRole.is_active == 1,
    ).first()
    if not mem:
        return ResponseBase.error("你不在这个世界中", 400)
    mem.is_active = 0
    world.member_count = max(1, world.member_count - 1)
    db.commit()
    return ResponseBase.success({"left": True})


# ============ 7. 成员列表 ============
@router.get("/members/{world_id}")
def list_members(world_id: int,
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权访问", 403)
    members = db.query(WorldRole).filter(
        WorldRole.world_id == world_id, WorldRole.is_active == 1
    ).all()
    return ResponseBase.success([{
        "id": m.id, "role_name": m.role_name, "role_avatar": m.role_avatar,
        "join_type": m.join_type, "user_id": m.user_id, "is_custom": m.is_custom,
    } for m in members])


# ============ 8. 用户发布笔记 ============
@router.post("/note/{world_id}")
def publish_note(world_id: int, payload: NoteCreate,
                 user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    world = db.query(World).filter(
        World.id == world_id, World.status == 1
    ).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权在该世界发布", 403)

    # ↓↓↓ 安全合规批次：笔记内容前置安全校验 ↓↓↓
    from app.utils.content_security import ContentSecurity
    _sec = ContentSecurity.check_user_text(payload.content or "")
    if not _sec["ok"]:
        return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    user = db.query(User).filter(User.id == user_id).first()
    user_member = svc.add_user_member(
        db, world_id, user_id, user.nickname or user.username, ""
    )
    note = WorldNote(
        world_id=world_id, author_role_id=0, author_user_id=user_id,
        author_name=user_member.role_name, author_avatar=user_member.role_avatar,
        note_type=payload.note_type, content=payload.content, status=1,
    )
    db.add(note)
    world.note_count += 1
    db.commit()
    db.refresh(note)

    # 用户笔记 → 随机一位 AI 跟评欢迎（作者为空，不产生 AI 关系）
    ai_members = svc.list_ai_members(db, world_id)
    if ai_members:
        import random
        welcomer = random.choice(ai_members)
        c = WorldNoteComment(
            note_id=note.id, author_role_id=welcomer.id, author_user_id=0,
            author_name=welcomer.role_name, author_avatar=welcomer.role_avatar,
            content="欢迎你在世界里留下心情~我会一直在这里陪你。",
            reply_to_id=0, status=1,
        )
        db.add(c)
        note.comment_count += 1
        db.commit()
    return ResponseBase.success({"id": note.id})


# ============ 8.5 习惯经历 → 剧情碎片素材（P2-3） ============
@router.post("/fragment/from-habit")
def publish_habit_fragment(payload: dict,
                           user_id: int = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """
    把一段习惯经历写成世界里的剧情碎片（一条 note）

    body: { "world_id": 1, "habit_id": 2 }
    内容由 habit_companion_service 生成：只写共同经历，不写完成率、不排名。
    """
    world_id = int(payload.get("world_id") or 0)
    habit_id = int(payload.get("habit_id") or 0)
    if not world_id or not habit_id:
        return ResponseBase.error("缺少 world_id 或 habit_id", 400)

    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权在该世界发布", 403)

    frag = HCS.build_world_fragment(db, user_id, habit_id)
    if not frag:
        return ResponseBase.error("习惯不存在", 404)

    user = db.query(User).filter(User.id == user_id).first()
    member = svc.add_user_member(db, world_id, user_id, user.nickname or user.username, "")
    note = WorldNote(
        world_id=world_id, author_role_id=0, author_user_id=user_id,
        author_name=member.role_name, author_avatar=member.role_avatar,
        note_type="checkin",
        content=f"【{frag['title']}】{frag['content']}",
        related_user_id=user_id, related_habit_id=habit_id, status=1,
    )
    db.add(note)
    world.note_count += 1
    db.commit()
    db.refresh(note)

    return ResponseBase.success({
        "id": note.id,
        "habit_id": habit_id,
        "title": frag["title"],
        "content": frag["content"],
    })


# ============ 9. 笔记流 ============
@router.get("/notes/{world_id}")
def list_notes(world_id: int,
               user_id: int = Depends(get_current_user),
               db: Session = Depends(get_db)):
    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权访问", 403)
    notes = db.query(WorldNote).filter(
        WorldNote.world_id == world_id, WorldNote.status == 1
    ).order_by(WorldNote.created_at.desc()).limit(100).all()
    return ResponseBase.success([{
        "id": n.id, "note_type": n.note_type, "content": n.content,
        "author_name": n.author_name, "author_avatar": n.author_avatar,
        "author_role_id": n.author_role_id, "author_user_id": n.author_user_id,
        "related_user_id": n.related_user_id, "comment_count": n.comment_count,
        "created_at": n.created_at.strftime("%m-%d %H:%M") if n.created_at else "",
    } for n in notes])


# ============ 10. 用户评论（AI 回复 + AI 互评 + 关系变化） ============
@router.post("/comment/{note_id}")
def add_comment(note_id: int, payload: CommentCreate,
                user_id: int = Depends(get_current_user),
                db: Session = Depends(get_db)):
    note = db.query(WorldNote).filter(
        WorldNote.id == note_id, WorldNote.status == 1
    ).first()
    if not note:
        return ResponseBase.error("笔记不存在", 404)
    world = db.query(World).filter(World.id == note.world_id).first()
    if not _can_view(db, world, user_id):
        return ResponseBase.error("无权评论", 403)

    user = db.query(User).filter(User.id == user_id).first()
    user_member = svc.add_user_member(
        db, note.world_id, user_id, user.nickname or user.username, ""
    )
    created = svc.comment_and_trigger_ai(
        db, note, user_member, payload.content, payload.reply_to_id
    )
    return ResponseBase.success({
        "comments": [{
            "id": c.id, "author_name": c.author_name, "author_avatar": c.author_avatar,
            "author_role_id": c.author_role_id, "author_user_id": c.author_user_id,
            "content": c.content,
            "created_at": c.created_at.strftime("%m-%d %H:%M") if c.created_at else "",
        } for c in created],
        "comment_count": note.comment_count,
    })


# ============ 11. 评论列表 ============
@router.get("/comments/{note_id}")
def list_comments(note_id: int,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    note = db.query(WorldNote).filter(
        WorldNote.id == note_id, WorldNote.status == 1
    ).first()
    if not note:
        return ResponseBase.error("笔记不存在", 404)
    world = db.query(World).filter(World.id == note.world_id).first()
    if not _can_view(db, world, user_id):
        return ResponseBase.error("无权访问", 403)
    comments = db.query(WorldNoteComment).filter(
        WorldNoteComment.note_id == note_id, WorldNoteComment.status == 1
    ).order_by(WorldNoteComment.created_at.asc()).all()
    return ResponseBase.success([{
        "id": c.id, "author_name": c.author_name, "author_avatar": c.author_avatar,
        "author_role_id": c.author_role_id, "author_user_id": c.author_user_id,
        "content": c.content, "reply_to_id": c.reply_to_id,
        "created_at": c.created_at.strftime("%m-%d %H:%M") if c.created_at else "",
    } for c in comments])


# ============ 12. AI 角色关系 ============
@router.get("/relations/{world_id}")
def list_relations(world_id: int,
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权访问", 403)
    rels = db.query(WorldRelation).filter(
        WorldRelation.world_id == world_id
    ).order_by(WorldRelation.score.desc()).all()

    def member_name(mid: int) -> str:
        m = svc.get_member(db, world_id, mid)
        return m.role_name if m else "?"

    return ResponseBase.success([{
        "id": r.id, "score": r.score, "relation_label": r.relation_label,
        "role_a": member_name(r.role_a_id), "role_a_avatar": (
            svc.get_member(db, world_id, r.role_a_id).role_avatar
            if svc.get_member(db, world_id, r.role_a_id) else ""
        ),
        "role_b": member_name(r.role_b_id), "role_b_avatar": (
            svc.get_member(db, world_id, r.role_b_id).role_avatar
            if svc.get_member(db, world_id, r.role_b_id) else ""
        ),
    } for r in rels])


# ============ 13. 同世界 AI 互动消息（打卡反馈 + AI互评） ============
@router.get("/ai-interactions/{world_id}")
def ai_interactions(world_id: int,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    world = db.query(World).filter(World.id == world_id, World.status == 1).first()
    if not world or not _can_view(db, world, user_id):
        return ResponseBase.error("无权访问", 403)

    # AI 作者发布的笔记（含打卡反馈 feedback）
    ai_notes = db.query(WorldNote).filter(
        WorldNote.world_id == world_id,
        WorldNote.author_role_id != 0,
        WorldNote.status == 1,
    ).order_by(WorldNote.created_at.desc()).limit(30).all()

    # AI 发出的评论（互评）
    ai_comment_ids = [c.id for c in db.query(WorldNoteComment).filter(
        WorldNoteComment.author_role_id != 0,
        WorldNoteComment.status == 1,
    ).join(WorldNote, WorldNote.id == WorldNoteComment.note_id).filter(
        WorldNote.world_id == world_id
    ).order_by(WorldNoteComment.created_at.desc()).limit(30).all()]
    ai_comments = db.query(WorldNoteComment).filter(
        WorldNoteComment.id.in_(ai_comment_ids or [-1])
    ).all()

    return ResponseBase.success({
        "notes": [{
            "id": n.id, "author_name": n.author_name,
            "author_avatar": n.author_avatar, "content": n.content,
            "note_type": n.note_type,
            "created_at": n.created_at.strftime("%m-%d %H:%M") if n.created_at else "",
        } for n in ai_notes],
        "comments": [{
            "id": c.id, "note_id": c.note_id, "author_name": c.author_name,
            "author_avatar": c.author_avatar, "content": c.content,
            "created_at": c.created_at.strftime("%m-%d %H:%M") if c.created_at else "",
        } for c in ai_comments],
    })
