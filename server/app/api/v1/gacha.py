# -*- coding: utf-8 -*-
"""
互动扭蛋机 API（模块3）
端点：
  GET  /gacha/wallet          我的扭蛋币钱包（首次自动建，送20欢迎币）
  GET  /gacha/list            剧本列表 tab=recommend/hot/favorite/mine，可按分类筛
  POST /gacha/favorite/{id}   收藏/取消收藏
  POST /gacha/create          用户创建自定义剧本
  POST /gacha/draw            消耗扭蛋币抽取剧本（扣币/计数/生成会话）
  POST /gacha/answer          剧本问答（AI回应 + 对话写入聊天历史，末题结束）
  GET  /gacha/records         我的抽取记录
"""
import json
import random
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.gacha import (
    GachaTemplate, UserGachaWallet, UserGachaRecord, UserGachaFavorite
)
from app.models.chat import ChatSession, ChatMessage
from app.schemas.common import ResponseBase
from app.schemas.gacha import (
    GachaTemplateCreate, GachaDrawRequest, GachaAnswerRequest
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/gacha", tags=["互动扭蛋"])

DRAW_COST = 10           # 每抽一次 10 扭蛋币
WELCOME_COIN = 20        # 新用户欢迎币


def _get_or_create_wallet(db: Session, user_id: int) -> UserGachaWallet:
    w = db.query(UserGachaWallet).filter(UserGachaWallet.user_id == user_id).first()
    if not w:
        w = UserGachaWallet(
            user_id=user_id, coin_balance=WELCOME_COIN, total_earned=WELCOME_COIN
        )
        db.add(w)
        db.commit()
        db.refresh(w)
    return w


def _serialize_template(t: GachaTemplate, favored: bool) -> dict:
    return {
        "id": t.id,
        "creator_id": t.creator_id,
        "title": t.title,
        "description": t.description,
        "category": t.category,
        "opening_text": t.opening_text,
        "is_official": t.is_official,
        "use_count": t.use_count,
        "favorite_count": t.favorite_count,
        "favored": favored,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
    }


def _ai_reply(category: str, question: dict, answer: str, is_last: bool) -> str:
    """
    Mock AI 回应（AI_MODEL=mock 环境）：
    根据用户回答 + 题目提示 + 剧本分类生成贴合陪伴定位的回应。
    接入真实大模型时，把本函数替换为 LLM 调用即可，调用处无需改动。
    """
    hint = question.get("hint", "")
    if category == "companion":
        text = f"收到~你选了「{answer}」。{hint} 每一步认真对待自己的样子，我都看在眼里。"
        if is_last:
            text += " 今天的打卡仪式就到这里，带着这份稳稳的节奏继续走吧，我陪着你。"
    elif category == "emotion":
        text = f"嗯，「{answer}」——谢谢你愿意告诉我。{hint} 你的感受在这里是安全的。"
        if is_last:
            text += " 说完之后有没有轻一点？任何时候需要，我都在。"
    else:  # chat
        text = f"哈哈，「{answer}」这个选择很有你的风格！{hint}"
        if is_last:
            text += " 这场脑洞小剧场圆满结束~下次想玩什么随时来找我。"
    return text


# ============ 1. 我的钱包 ============
@router.get("/wallet")
def get_wallet(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    w = _get_or_create_wallet(db, user_id)
    return ResponseBase.success({
        "coin_balance": w.coin_balance,
        "total_earned": w.total_earned,
        "total_cost": w.total_cost,
    })


# ============ 2. 剧本列表（推荐/最热/收藏/我创建的 + 分类筛选） ============
@router.get("/list")
def list_templates(tab: str = Query("recommend"),
                   category: str = Query(""),
                   user_id: int = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    fav_ids = {f.template_id for f in db.query(UserGachaFavorite).filter(
        UserGachaFavorite.user_id == user_id
    ).all()}

    q = db.query(GachaTemplate).filter(GachaTemplate.status == 1)
    if category:
        q = q.filter(GachaTemplate.category == category)

    if tab == "mine":
        q = q.filter(GachaTemplate.creator_id == user_id)
        q = q.order_by(GachaTemplate.created_at.desc())
    elif tab == "favorite":
        q = q.filter(GachaTemplate.id.in_(fav_ids or [-1]))
        q = q.order_by(GachaTemplate.created_at.desc())
    elif tab == "hot":
        q = q.order_by(GachaTemplate.use_count.desc())
    else:  # recommend：官方优先，再按热度
        q = q.order_by(GachaTemplate.is_official.desc(), GachaTemplate.use_count.desc())

    rows = q.limit(50).all()
    return ResponseBase.success([_serialize_template(t, t.id in fav_ids) for t in rows])


# ============ 3. 收藏 / 取消收藏 ============
@router.post("/favorite/{template_id}")
def toggle_favorite(template_id: int,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    t = db.query(GachaTemplate).filter(
        GachaTemplate.id == template_id, GachaTemplate.status == 1
    ).first()
    if not t:
        return ResponseBase.error("剧本不存在", 404)

    fav = db.query(UserGachaFavorite).filter(
        UserGachaFavorite.user_id == user_id,
        UserGachaFavorite.template_id == template_id,
    ).first()
    if fav:
        db.delete(fav)
        t.favorite_count = max(0, t.favorite_count - 1)
        favored = False
    else:
        db.add(UserGachaFavorite(user_id=user_id, template_id=template_id))
        t.favorite_count += 1
        favored = True
    db.commit()
    return ResponseBase.success({"favored": favored, "favorite_count": t.favorite_count})


# ============ 4. 用户创建剧本 ============
@router.post("/create")
def create_template(payload: GachaTemplateCreate,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if payload.category not in ("companion", "emotion", "chat"):
        return ResponseBase.error("分类只能是 companion/emotion/chat", 400)

    # ↓↓↓ 安全合规批次：剧本内容前置安全校验（标题/描述/开场白/题目与选项） ↓↓↓
    from app.utils.content_security import ContentSecurity
    _texts = [payload.title or "", payload.description or "", payload.opening_text or ""]
    for _q in payload.questions:
        _texts.append(_q.question or "")
        _texts.extend(_q.options or [])
        _texts.append(_q.hint or "")
    for _text in _texts:
        _sec = ContentSecurity.check_user_text(_text)
        if not _sec["ok"]:
            return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    questions = [q.model_dump() for q in payload.questions]
    t = GachaTemplate(
        creator_id=user_id, title=payload.title, description=payload.description,
        category=payload.category, opening_text=payload.opening_text,
        questions=json.dumps(questions, ensure_ascii=False),
        is_official=0, status=1,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return ResponseBase.success(_serialize_template(t, False))


# ============ 5. 扭蛋抽取 ============
@router.post("/draw")
def draw_template(payload: GachaDrawRequest,
                  user_id: int = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    wallet = _get_or_create_wallet(db, user_id)
    if wallet.coin_balance < DRAW_COST:
        return ResponseBase.error(
            f"扭蛋币不足（每次{DRAW_COST}），完成今日打卡即可赚取", 400
        )

    q = db.query(GachaTemplate).filter(GachaTemplate.status == 1)
    if payload.category:
        q = q.filter(GachaTemplate.category == payload.category)
    candidates = q.all()
    if not candidates:
        return ResponseBase.error("暂无可抽取的剧本", 400)

    # 简单随机（可平滑升级为按权重：use_count 高的略微加权）
    tpl = random.choice(candidates)

    # 扣币 + 记录 + 计数
    wallet.coin_balance -= DRAW_COST
    wallet.total_cost += DRAW_COST
    tpl.use_count += 1
    record = UserGachaRecord(
        user_id=user_id, template_id=tpl.id, cost=DRAW_COST, status="drawn"
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 创建本场剧本会话（标题编码 record_id，便于问答时定位）
    session = ChatSession(
        user_id=user_id, role_type="gentle",
        title=f"【扭蛋】#{record.id} {tpl.title}",
        session_type="chat", status=1, message_count=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # AI 开场白写入聊天历史
    opening = ChatMessage(
        session_id=session.id, user_id=user_id, role="assistant",
        content=tpl.opening_text or "剧本开始啦~",
    )
    session.message_count = 1
    session.last_message_time = datetime.now()
    db.add(opening)
    db.commit()

    questions = json.loads(tpl.questions) if tpl.questions else []
    return ResponseBase.success({
        "record_id": record.id,
        "session_id": session.id,
        "template": _serialize_template(tpl, False),
        "questions": questions,
        "coin_balance": wallet.coin_balance,
    })


# ============ 6. 剧本问答（对话写入聊天历史） ============
@router.post("/answer")
def answer_question(payload: GachaAnswerRequest,
                    user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    record = db.query(UserGachaRecord).filter(
        UserGachaRecord.id == payload.record_id,
        UserGachaRecord.user_id == user_id,
    ).first()
    if not record:
        return ResponseBase.error("抽取记录不存在", 404)
    if record.status == "finished":
        return ResponseBase.error("本场剧本已结束", 400)

    # ↓↓↓ 安全合规批次：回答内容前置安全校验 ↓↓↓
    from app.utils.content_security import ContentSecurity
    _sec = ContentSecurity.check_user_text(payload.answer or "", max_length=500)
    if not _sec["ok"]:
        return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    tpl = db.query(GachaTemplate).filter(GachaTemplate.id == record.template_id).first()
    questions = json.loads(tpl.questions) if tpl.questions else []
    idx = payload.question_index
    if idx < 0 or idx >= len(questions):
        return ResponseBase.error("题目序号无效", 400)

    # 定位抽取时创建的会话
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.title == f"【扭蛋】#{record.id} {tpl.title}",
    ).first()
    if not session:
        return ResponseBase.error("剧本会话丢失", 500)

    is_last = idx == len(questions) - 1
    # 用户回答 + AI 回应均写入聊天历史（数据互通：chat 页可见）
    user_msg = ChatMessage(
        session_id=session.id, user_id=user_id, role="user",
        content=payload.answer or questions[idx]["question"],
    )
    reply_text = _ai_reply(
        tpl.category, questions[idx], payload.answer or "", is_last
    )
    ai_msg = ChatMessage(
        session_id=session.id, user_id=user_id, role="assistant",
        content=reply_text,
    )
    db.add_all([user_msg, ai_msg])
    session.message_count += 2
    session.last_message_time = datetime.now()

    finished = False
    if is_last:
        record.status = "finished"
        record.finished_at = datetime.now()
        finished = True
    db.commit()

    return ResponseBase.success({
        "reply": reply_text,
        "next_question_index": None if is_last else idx + 1,
        "finished": finished,
    })


# ============ 7. 我的抽取记录 ============
@router.get("/records")
def my_records(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(UserGachaRecord).filter(
        UserGachaRecord.user_id == user_id
    ).order_by(UserGachaRecord.created_at.desc()).limit(50).all()

    result = []
    for r in records:
        t = db.query(GachaTemplate).filter(GachaTemplate.id == r.template_id).first()
        result.append({
            "record_id": r.id,
            "template_id": r.template_id,
            "title": t.title if t else "(已下架)",
            "category": t.category if t else "",
            "cost": r.cost,
            "status": r.status,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        })
    return ResponseBase.success(result)
