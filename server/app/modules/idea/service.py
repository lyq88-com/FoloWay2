# -*- coding: utf-8 -*-
"""
「小想法 · 共鸣匹配」核心服务
==============================

这里放所有业务规则，router 只做参数/鉴权/序列化外壳：

- publish_idea     发布 → 语义匹配 → 写入双向共鸣记录
- get_my_resonance 取推送给我的共鸣
- light_idea       点亮 → 单向只发匿名微弱通知；双向则开会话 + 双方通知
- quick_react      轻互动（好棒/同意/击掌/摸摸头）
- get_my_idea_list 我的已发布想法 + 收到的点亮数
- delete_idea      删除想法（级联清共鸣、点亮）

隐私红线：
- 没有全局列表接口（不存在「刷全部想法」的入口）
- 只有 source_uid 本人能读到推送给自己的共鸣
- 双向点亮之前，对方的昵称/头像对匿名想法一律不返回
- 对外永不返回点赞/点亮数量
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.storage_service import get_storage

from . import semantic
from .models import (
    Idea, IdeaResonance, IdeaLike,
    IdeaSetting, IdeaBlock, IdeaConversation, IdeaMessage, IdeaNotification,
)

# ---------------- 可调参数 ----------------
RECENT_DAYS = 60          # 只在最近 N 天的想法里匹配（优先近期）
CANDIDATE_LIMIT = 300     # 单次匹配最多扫描多少条候选
MATCH_MIN = 3             # 期望匹配数下限（不足不强行填充）
MATCH_MAX = 5             # 返回上限
MATCH_THRESHOLD = 0.12    # 相似度阈值（低于它不返回，宁缺毋滥）
RESONANCE_LIST_LIMIT = 60 # 共鸣列表返回上限

REACT_TYPES = {"good", "agree", "highfive", "pat"}
REACT_TEXT = {"good": "好棒", "agree": "同意", "highfive": "击掌", "pat": "摸摸头"}


# ============================================================
# 基础工具
# ============================================================
def _rel_to_url(rel: str) -> str:
    """相对路径 → 可访问 URL（与朋友圈一致，走统一 storage）"""
    if not rel:
        return ""
    return get_storage().get_url(rel)


def _url_to_rel(url: str) -> str:
    """前端回传的 URL → 入库相对路径"""
    if not url:
        return ""
    if "/uploads/" in url:
        return url.split("/uploads/", 1)[1]
    return url


def _profile(db: Session, uid: int, is_anonymous: int, matched: bool) -> Dict:
    """
    对方资料。匿名 + 未双向 → 只给占位，不泄露身份。
    """
    if is_anonymous and not matched:
        return {"id": 0, "nickname": "匿名的想法", "avatar": ""}
    u = db.query(User).filter(User.id == uid).first()
    return {
        "id": uid,
        "nickname": (u.nickname if u and u.nickname else "用户") if u else "用户",
        "avatar": (u.avatar if u else "") or "",
    }


def get_or_create_setting(db: Session, uid: int) -> IdeaSetting:
    row = db.query(IdeaSetting).filter(IdeaSetting.user_id == uid).first()
    if not row:
        row = IdeaSetting(user_id=uid, accept_resonance=1)
        db.add(row)
        db.flush()
    return row


def is_accepting(db: Session, uid: int) -> bool:
    row = db.query(IdeaSetting).filter(IdeaSetting.user_id == uid).first()
    return True if row is None else bool(row.accept_resonance)


def _blocked_set(db: Session, uid: int) -> Set[int]:
    """与我存在拉黑关系（我拉黑 or 被拉黑）的所有用户 ID"""
    rows = db.query(IdeaBlock).filter(
        or_(IdeaBlock.user_id == uid, IdeaBlock.blocked_uid == uid)
    ).all()
    s: Set[int] = set()
    for r in rows:
        s.add(r.blocked_uid if r.user_id == uid else r.user_id)
    return s


def _notify(db: Session, user_id: int, ntype: str, title: str, content: str, ref_id: int = 0):
    db.add(IdeaNotification(
        user_id=user_id, ntype=ntype, title=title, content=content, ref_id=ref_id,
    ))


def _lit_exists(db: Session, idea_id: int, from_uid: int, to_uid: int) -> bool:
    return db.query(IdeaLike).filter(
        IdeaLike.idea_id == idea_id,
        IdeaLike.from_uid == from_uid,
        IdeaLike.to_uid == to_uid,
        IdeaLike.action_type == "light",
    ).first() is not None


def _get_conversation(db: Session, uid1: int, uid2: int) -> Optional[IdeaConversation]:
    a, b = (uid1, uid2) if uid1 < uid2 else (uid2, uid1)
    return db.query(IdeaConversation).filter(
        IdeaConversation.user_a == a, IdeaConversation.user_b == b
    ).first()


def _ensure_conversation(db: Session, uid1: int, uid2: int,
                         idea1: int, idea2: int) -> IdeaConversation:
    """建立（或复用）真人私聊会话。idea 入参语义：idea1 属于 uid1，idea2 属于 uid2。"""
    a, b = (uid1, uid2) if uid1 < uid2 else (uid2, uid1)
    conv = _get_conversation(db, uid1, uid2)
    if conv:
        return conv
    # 保证 idea_a 对应 user_a
    if uid1 < uid2:
        idea_a, idea_b = idea1, idea2
    else:
        idea_a, idea_b = idea2, idea1
    conv = IdeaConversation(user_a=a, user_b=b, idea_a=idea_a, idea_b=idea_b,
                            last_message="", last_time=datetime.now(),
                            unread_a=0, unread_b=0)
    db.add(conv)
    db.flush()
    return conv


# ============================================================
# 发布 + 匹配
# ============================================================
def _match_candidates(db: Session, uid: int, content: str) -> List[Tuple[Idea, int]]:
    """返回 [(候选想法, 与查询文本的相似度排序后)]，已过滤自身/拉黑/关闭匹配/过期删除"""
    since = datetime.now() - timedelta(days=RECENT_DAYS)
    blocked = _blocked_set(db, uid)

    rows = db.query(Idea).filter(
        Idea.is_deleted == 0,
        Idea.uid != uid,
        Idea.create_time >= since,
    ).order_by(Idea.create_time.desc()).limit(CANDIDATE_LIMIT).all()

    # 过滤拉黑
    if blocked:
        rows = [r for r in rows if r.uid not in blocked]
    if not rows:
        return []

    # 过滤「关闭了接受共鸣匹配」的用户
    owner_ids = list({r.uid for r in rows})
    off_ids = {
        s.user_id
        for s in db.query(IdeaSetting).filter(
            IdeaSetting.user_id.in_(owner_ids),
            IdeaSetting.accept_resonance == 0,
        ).all()
    }
    rows = [r for r in rows if r.uid not in off_ids]
    if not rows:
        return []

    # 语义向量相似度（一次算查询向量，逐条比对）
    qvec = semantic.embed(content)
    scored = []
    for r in rows:
        sim = semantic.similarity(qvec, semantic.embed(r.content or ""))
        if sim >= MATCH_THRESHOLD:
            scored.append((r, semantic.to_score(sim)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:MATCH_MAX]


def publish_and_match(db: Session, uid: int, content: str, image: str,
                      is_anonymous: bool) -> Tuple[Idea, List[Dict]]:
    """发布想法并做语义匹配，返回 (新想法, 我方共鸣卡片列表)"""
    idea = Idea(uid=uid, content=content, image=_url_to_rel(image),
                is_anonymous=1 if is_anonymous else 0)
    db.add(idea)
    db.commit()
    db.refresh(idea)

    # 若用户关闭了「接受共鸣匹配」，则发布但不推送共鸣
    if not is_accepting(db, uid):
        return idea, []

    matched = _match_candidates(db, uid, content)
    cards: List[Dict] = []
    for target, score in matched:
        # 我方记录：我的想法 ←→ 对方想法
        exist_mine = db.query(IdeaResonance).filter(
            IdeaResonance.idea_id == idea.id,
            IdeaResonance.target_idea_id == target.id,
        ).first()
        if not exist_mine:
            db.add(IdeaResonance(
                idea_id=idea.id, target_idea_id=target.id,
                source_uid=uid, target_uid=target.uid, resonance_score=score,
            ))
        # 反向记录：让对方也能看到我这条想法并回点亮（双向点亮的必要前提）
        exist_rev = db.query(IdeaResonance).filter(
            IdeaResonance.idea_id == target.id,
            IdeaResonance.target_idea_id == idea.id,
        ).first()
        if not exist_rev:
            db.add(IdeaResonance(
                idea_id=target.id, target_idea_id=idea.id,
                source_uid=target.uid, target_uid=uid, resonance_score=score,
            ))
    db.commit()

    # 组织我方卡片
    mine = db.query(IdeaResonance).filter(
        IdeaResonance.idea_id == idea.id
    ).order_by(IdeaResonance.resonance_score.desc()).all()
    for res in mine:
        cards.append(serialize_resonance(db, res, uid))
    return idea, cards


# ============================================================
# 共鸣卡片序列化
# ============================================================
def _is_matched(db: Session, my_idea_id: int, target_idea_id: int,
                me: int, other: int) -> bool:
    """双向点亮：我点亮了对方这条 且 对方点亮了我这条"""
    return (_lit_exists(db, target_idea_id, me, other)
            and _lit_exists(db, my_idea_id, other, me))


def serialize_resonance(db: Session, res: IdeaResonance, viewer: int) -> Dict:
    target = db.query(Idea).filter(Idea.id == res.target_idea_id).first()
    if not target or target.is_deleted:
        return {}
    matched = _is_matched(db, res.idea_id, res.target_idea_id, viewer, res.target_uid)
    lit = _lit_exists(db, res.target_idea_id, viewer, res.target_uid)
    other_lit_me = _lit_exists(db, res.idea_id, res.target_uid, viewer)

    # 我发出的轻互动
    reacts = {}
    for a in REACT_TYPES:
        reacts[a] = db.query(IdeaLike).filter(
            IdeaLike.idea_id == res.target_idea_id,
            IdeaLike.from_uid == viewer,
            IdeaLike.action_type == a,
        ).first() is not None

    conv = _get_conversation(db, viewer, res.target_uid) if matched else None
    return {
        "resonance_id": res.id,
        "idea": {
            "id": target.id,
            "content": target.content or "",
            "image": _rel_to_url(target.image),
            "is_anonymous": target.is_anonymous or 0,
            "create_time": target.create_time.strftime("%Y-%m-%d %H:%M:%S") if target.create_time else "",
        },
        "author": _profile(db, res.target_uid, target.is_anonymous or 0, matched),
        "score": res.resonance_score,
        "lit": lit,
        "other_lit_me": other_lit_me,
        "matched": matched,
        "conversation_id": conv.id if conv else 0,
        "reacts": reacts,
        "viewed": bool(res.is_viewed),
    }


# ============================================================
# 读取 / 操作
# ============================================================
def get_my_resonance(db: Session, uid: int) -> List[Dict]:
    rows = db.query(IdeaResonance).filter(
        IdeaResonance.source_uid == uid
    ).order_by(IdeaResonance.create_time.desc()).limit(RESONANCE_LIST_LIMIT).all()

    blocked = _blocked_set(db, uid)
    cards: List[Dict] = []
    for r in rows:
        if r.target_uid in blocked:
            continue
        card = serialize_resonance(db, r, uid)
        if not card:
            continue
        cards.append(card)
        if not r.is_viewed:
            r.is_viewed = 1
    db.commit()
    return cards


def light_idea(db: Session, uid: int, resonance_id: int) -> Dict:
    """点亮共鸣卡片 → 判定双向点亮"""
    res = db.query(IdeaResonance).filter(IdeaResonance.id == resonance_id).first()
    if not res:
        return {"__error__": "共鸣不存在", "__code__": 404}
    if res.source_uid != uid:
        return {"__error__": "无权操作他人共鸣", "__code__": 403}

    target = db.query(Idea).filter(Idea.id == res.target_idea_id).first()
    if not target or target.is_deleted:
        return {"__error__": "该想法已被删除", "__code": 404}
    if res.target_uid in _blocked_set(db, uid):
        return {"__error__": "无法对该用户操作", "__code": 403}

    me, other = uid, res.target_uid

    # 幂等写入点亮
    if not _lit_exists(db, res.target_idea_id, me, other):
        db.add(IdeaLike(idea_id=res.target_idea_id, from_uid=me,
                        to_uid=other, action_type="light"))
        # 单向微弱通知：不含身份
        _notify(db, other, "light", "有人点亮了你的想法",
                "有人点亮了你的小想法，但还没告诉你他是谁。", res.target_idea_id)

    # 判定双向：对方是否点亮的正是我这条想法
    matched = _lit_exists(db, res.idea_id, other, me)
    conversation_id = 0
    if matched:
        conv = _ensure_conversation(db, me, other, res.idea_id, res.target_idea_id)
        conversation_id = conv.id
        # 双方通知（幂等：仅首次建立时提示）
        _notify(db, me, "matched", "你们找到了共鸣",
                "你们找到了共鸣，可以开始聊天啦。", conv.id)
        _notify(db, other, "matched", "你们找到了共鸣",
                "你们找到了共鸣，可以开始聊天啦。", conv.id)

    db.commit()
    return {"lit": True, "matched": matched, "conversation_id": conversation_id}


def quick_react(db: Session, uid: int, idea_id: int, action_type: str) -> Dict:
    if action_type not in REACT_TYPES:
        return {"__error__": "不支持的互动类型", "__code__": 400}

    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.is_deleted == 0).first()
    if not idea:
        return {"__error__": "想法不存在或已删除", "__code__": 404}
    if idea.uid == uid:
        return {"__error__": "不能给自己的想法互动", "__code__": 400}
    if idea.uid in _blocked_set(db, uid):
        return {"__error__": "无法对该用户操作", "__code__": 403}

    # 只有能看见（存在共鸣关系）才允许互动
    can_see = db.query(IdeaResonance).filter(
        IdeaResonance.source_uid == uid,
        IdeaResonance.target_idea_id == idea_id,
    ).first()
    if not can_see:
        return {"__error__": "无权互动该想法", "__code__": 403}

    exists = db.query(IdeaLike).filter(
        IdeaLike.idea_id == idea_id, IdeaLike.from_uid == uid,
        IdeaLike.action_type == action_type,
    ).first()
    if not exists:
        db.add(IdeaLike(idea_id=idea_id, from_uid=uid,
                        to_uid=idea.uid, action_type=action_type))
        # 轻互动通知：同样在双向点亮前不暴露身份
        matched = _is_matched(db, can_see.idea_id, idea_id, uid, idea.uid)
        who = "" if not matched else ""
        _notify(db, idea.uid, "react", "有人回应了你的想法",
                f"有人对你的想法「{REACT_TEXT[action_type]}」，{who}".strip(), idea_id)
    db.commit()
    return {"action_type": action_type, "done": True}


def get_my_idea_list(db: Session, uid: int) -> List[Dict]:
    ideas = db.query(Idea).filter(
        Idea.uid == uid, Idea.is_deleted == 0
    ).order_by(Idea.create_time.desc()).all()

    out = []
    for it in ideas:
        light_cnt = db.query(IdeaLike).filter(
            IdeaLike.idea_id == it.id, IdeaLike.action_type == "light"
        ).count()
        react_cnt = db.query(IdeaLike).filter(
            IdeaLike.idea_id == it.id, IdeaLike.action_type.in_(list(REACT_TYPES))
        ).count()
        # 是否已产生双向匹配
        matched_cnt = 0
        for r in db.query(IdeaResonance).filter(IdeaResonance.idea_id == it.id).all():
            if _lit_exists(db, it.id, r.target_uid, uid):
                matched_cnt += 1
        out.append({
            "id": it.id,
            "content": it.content or "",
            "image": _rel_to_url(it.image),
            "is_anonymous": it.is_anonymous or 0,
            "create_time": it.create_time.strftime("%Y-%m-%d %H:%M:%S") if it.create_time else "",
            "light_count": light_cnt,       # ⚠️ 仅本人可见，不对外展示
            "react_count": react_cnt,
            "matched_count": matched_cnt,
        })
    return out


def delete_idea(db: Session, uid: int, idea_id: int) -> Dict:
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.is_deleted == 0).first()
    if not idea:
        return {"__error__": "想法不存在", "__code__": 404}
    if idea.uid != uid:
        return {"__error__": "无权删除他人想法", "__code__": 403}

    idea.is_deleted = 1
    # 级联清除：共鸣（双向）+ 点亮 / 轻互动
    db.query(IdeaResonance).filter(
        or_(IdeaResonance.idea_id == idea_id,
            IdeaResonance.target_idea_id == idea_id)
    ).delete(synchronize_session=False)
    db.query(IdeaLike).filter(IdeaLike.idea_id == idea_id).delete(synchronize_session=False)
    db.commit()
    return {"idea_id": idea_id}


# ============================================================
# 私聊（真人）
# ============================================================
def get_conversations(db: Session, uid: int) -> List[Dict]:
    rows = db.query(IdeaConversation).filter(
        or_(IdeaConversation.user_a == uid, IdeaConversation.user_b == uid)
    ).order_by(IdeaConversation.last_time.desc()).all()

    # 我拉黑的人：会话不再出现在列表里
    blocked = {
        r.blocked_uid
        for r in db.query(IdeaBlock).filter(IdeaBlock.user_id == uid).all()
    }

    out = []
    for c in rows:
        other = c.user_b if c.user_a == uid else c.user_a
        if other in blocked:
            continue
        u = db.query(User).filter(User.id == other).first()
        unread = c.unread_b if c.user_b == uid else c.unread_a
        out.append({
            "conversation_id": c.id,
            "other": {
                "id": other,
                "nickname": (u.nickname if u and u.nickname else "用户") if u else "用户",
                "avatar": (u.avatar if u else "") or "",
            },
            "last_message": c.last_message or "",
            "last_time": c.last_time.strftime("%Y-%m-%d %H:%M:%S") if c.last_time else "",
            "unread": unread or 0,
        })
    return out


def _in_conversation(db: Session, uid: int, conv_id: int) -> Optional[IdeaConversation]:
    c = db.query(IdeaConversation).filter(IdeaConversation.id == conv_id).first()
    if not c or uid not in (c.user_a, c.user_b):
        return None
    return c


def block_user(db: Session, uid: int, blocked_uid: int) -> Dict:
    """拉黑（幂等）：写入 idea_block，历史会话保留但列表隐藏"""
    row = db.query(IdeaBlock).filter(
        IdeaBlock.user_id == uid, IdeaBlock.blocked_uid == blocked_uid
    ).first()
    if not row:
        db.add(IdeaBlock(user_id=uid, blocked_uid=blocked_uid))
        db.commit()
    return {"blocked_uid": blocked_uid}


def unblock_user(db: Session, uid: int, blocked_uid: int) -> Dict:
    db.query(IdeaBlock).filter(
        IdeaBlock.user_id == uid, IdeaBlock.blocked_uid == blocked_uid
    ).delete(synchronize_session=False)
    db.commit()
    return {"blocked_uid": blocked_uid}


def get_messages(db: Session, uid: int, conv_id: int) -> Dict:
    c = _in_conversation(db, uid, conv_id)
    if not c:
        return {"__error__": "会话不存在或无权访问", "__code__": 403}
    # 清未读
    if c.user_a == uid:
        c.unread_a = 0
    else:
        c.unread_b = 0
    db.commit()

    msgs = db.query(IdeaMessage).filter(
        IdeaMessage.conversation_id == conv_id
    ).order_by(IdeaMessage.id.asc()).limit(200).all()
    other = c.user_b if c.user_a == uid else c.user_a
    u = db.query(User).filter(User.id == other).first()
    # 你们共鸣的那句话：取对方当初发布的那条想法
    other_idea_id = c.idea_b if c.user_a == uid else c.idea_a
    other_idea = db.query(Idea).filter(Idea.id == other_idea_id).first() if other_idea_id else None
    return {
        "conversation_id": conv_id,
        "other": {
            "id": other,
            "nickname": (u.nickname if u and u.nickname else "用户") if u else "用户",
            "avatar": (u.avatar if u else "") or "",
        },
        "resonance_text": (other_idea.content if other_idea else "") or "",
        "list": [{
            "id": m.id,
            "from_uid": m.from_uid,
            "content": m.content,
            "msg_type": m.msg_type,
            "mine": m.from_uid == uid,
            "create_time": m.create_time.strftime("%Y-%m-%d %H:%M:%S") if m.create_time else "",
        } for m in msgs],
    }


def send_message(db: Session, uid: int, conv_id: int, content: str) -> Dict:
    c = _in_conversation(db, uid, conv_id)
    if not c:
        return {"__error__": "会话不存在或无权访问", "__code__": 403}
    content = (content or "").strip()
    if not content:
        return {"__error__": "消息不能为空", "__code__": 400}
    if len(content) > 500:
        return {"__error__": "消息过长", "__code__": 400}

    other = c.user_b if c.user_a == uid else c.user_a
    # 任一方拉黑后，双方都不能再发消息
    blocked = db.query(IdeaBlock).filter(or_(
        and_(IdeaBlock.user_id == uid, IdeaBlock.blocked_uid == other),
        and_(IdeaBlock.user_id == other, IdeaBlock.blocked_uid == uid),
    )).first()
    if blocked:
        return {"__error__": "你们已无法继续聊天", "__code__": 403}
    msg = IdeaMessage(conversation_id=conv_id, from_uid=uid, to_uid=other, content=content)
    db.add(msg)
    c.last_message = content[:100]
    c.last_time = datetime.now()
    if c.user_b == other:
        c.unread_b = (c.unread_b or 0) + 1
    else:
        c.unread_a = (c.unread_a or 0) + 1
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "from_uid": uid,
        "content": content,
        "mine": True,
        "create_time": msg.create_time.strftime("%Y-%m-%d %H:%M:%S") if msg.create_time else "",
    }


# ============================================================
# 通知 & 未读汇总（供消息小红点使用）
# ============================================================
def get_notifications(db: Session, uid: int) -> Dict:
    rows = db.query(IdeaNotification).filter(
        IdeaNotification.user_id == uid
    ).order_by(IdeaNotification.create_time.desc()).limit(50).all()
    unread = db.query(IdeaNotification).filter(
        IdeaNotification.user_id == uid, IdeaNotification.is_read == 0
    ).count()
    return {
        "unread": unread,
        "list": [{
            "id": n.id,
            "type": n.ntype,
            "title": n.title,
            "content": n.content,
            "ref_id": n.ref_id,
            "is_read": n.is_read,
            "create_time": n.create_time.strftime("%Y-%m-%d %H:%M:%S") if n.create_time else "",
        } for n in rows],
    }


def read_notifications(db: Session, uid: int, notification_id: int = 0) -> Dict:
    q = db.query(IdeaNotification).filter(
        IdeaNotification.user_id == uid, IdeaNotification.is_read == 0
    )
    if notification_id:
        q = q.filter(IdeaNotification.id == notification_id)
    q.update({"is_read": 1}, synchronize_session=False)
    db.commit()
    return {"done": True}


def unread_badge(db: Session, uid: int) -> Dict:
    """消息入口小红点：私聊未读 + 通知未读"""
    convs = db.query(IdeaConversation).filter(
        or_(IdeaConversation.user_a == uid, IdeaConversation.user_b == uid)
    ).all()
    conv_unread = 0
    for c in convs:
        conv_unread += (c.unread_b if c.user_b == uid else c.unread_a) or 0
    notif_unread = db.query(IdeaNotification).filter(
        IdeaNotification.user_id == uid, IdeaNotification.is_read == 0
    ).count()
    return {"conversation_unread": conv_unread, "notification_unread": notif_unread,
            "total": conv_unread + notif_unread}
