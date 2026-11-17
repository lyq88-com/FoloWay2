# -*- coding: utf-8 -*-
"""
朋友圈 API - 列表/发布/点赞/评论
设计要点:
1. 两步发布流程: 先调用 /upload 逐张上传图片获取URL, 再调用 /publish 用 URL 数组创建动态
   (原因: uni-app 的 uni.uploadFile 单文件上传, 不支持多文件 multipart)
2. 删除动态时联动清理 uploads 物理图片文件
3. 列表/详情查询过滤 status == 1 (已软删除的记录不返回)
4. 图片URL输出时拼上 /uploads 前缀
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.user import User
from app.models.moment import Moment, MomentLike, MomentComment
from app.schemas.common import ResponseBase
from app.schemas.moment import MomentCreateRequest, MomentCommentCreate
from app.services.storage_service import get_storage
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/moment", tags=["朋友圈"])


def _serialize_moment(moment: Moment, db: Session, current_user_id: int) -> dict:
    """序列化动态(带点赞状态和用户信息)"""
    # 发布者信息
    author = db.query(User).filter(User.id == moment.user_id).first()
    # 当前用户是否已点赞
    liked = db.query(MomentLike).filter(
        MomentLike.moment_id == moment.id,
        MomentLike.user_id == current_user_id,
    ).first() is not None
    # 图片URL拼接 /uploads 前缀
    images_raw = json.loads(moment.images) if moment.images else []
    storage = get_storage()
    images = [storage.get_url(img) for img in images_raw]
    return {
        "id": moment.id,
        "user_id": moment.user_id,
        "content": moment.content or "",
        "images": images,
        "location": moment.location or "",
        "like_count": moment.like_count,
        "comment_count": moment.comment_count,
        "liked": liked,
        "author": {
            "id": author.id if author else 0,
            "nickname": author.nickname if author else "",
            "avatar": author.avatar if author else "",
        },
        "created_at": moment.created_at.strftime("%Y-%m-%d %H:%M:%S") if moment.created_at else "",
    }


def _serialize_comment(comment: MomentComment, db: Session) -> dict:
    """序列化评论"""
    user = db.query(User).filter(User.id == comment.user_id).first()
    return {
        "id": comment.id,
        "moment_id": comment.moment_id,
        "content": comment.content,
        "reply_to_id": comment.reply_to_id,
        "user": {
            "id": user.id if user else 0,
            "nickname": user.nickname if user else "",
            "avatar": user.avatar if user else "",
        },
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S") if comment.created_at else "",
    }


# ============ 1. 上传图片(两步发布第一步) ============
@router.post("/upload")
async def upload_moment_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """
    上传朋友圈图片(单张)
    返回: { url: "http://host/uploads/moment/xxx.jpg", path: "moment/xxx.jpg" }
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        return ResponseBase.error("仅支持图片格式", 400)

    file_bytes = await file.read()
    storage = get_storage()
    relative_path = storage.save(file_bytes, file.filename or "moment.jpg", subdir="moment")
    full_url = storage.get_url(relative_path)
    return ResponseBase.success({"url": full_url, "path": relative_path})


# ============ 2. 发布动态(两步发布第二步) ============
@router.post("/publish")
def publish_moment(
    payload: MomentCreateRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布新动态(images 为已上传得到的 URL 列表)"""
    # ↓↓↓ 安全合规批次：发布内容前置安全校验 ↓↓↓
    from app.utils.content_security import ContentSecurity
    _sec = ContentSecurity.check_user_text(payload.content or "")
    if not _sec["ok"]:
        return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    # 提取相对路径(去掉 host 前缀以便入库)
    storage = get_storage()
    relative_images = []
    for url in payload.images:
        # 拆掉 /uploads 前缀, 只存 moment/xxx.jpg
        if "/uploads/" in url:
            relative_images.append(url.split("/uploads/", 1)[1])
        else:
            relative_images.append(url)

    if not payload.content and not relative_images:
        return ResponseBase.error("内容不能为空", 400)

    moment = Moment(
        user_id=user_id,
        content=payload.content,
        images=json.dumps(relative_images, ensure_ascii=False),
        location=payload.location or "",
        like_count=0,
        comment_count=0,
        status=1,
    )
    db.add(moment)
    db.commit()
    db.refresh(moment)
    return ResponseBase.success(_serialize_moment(moment, db, user_id))


# ============ 3. 动态列表(按 created_at 倒序, 过滤软删) ============
@router.get("/list")
def get_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取朋友圈列表(按发布时间倒序)"""
    offset = (page - 1) * page_size
    moments = db.query(Moment).filter(
        Moment.status == 1
    ).order_by(
        desc(Moment.created_at)
    ).offset(offset).limit(page_size).all()

    total = db.query(Moment).filter(Moment.status == 1).count()
    list_data = [_serialize_moment(m, db, user_id) for m in moments]
    return ResponseBase.success({
        "list": list_data,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


# ============ 4. 动态详情 ============
@router.get("/detail/{moment_id}")
def get_moment_detail(
    moment_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条动态详情"""
    moment = db.query(Moment).filter(
        Moment.id == moment_id, Moment.status == 1
    ).first()
    if not moment:
        return ResponseBase.error("动态不存在或已删除", 404)
    return ResponseBase.success(_serialize_moment(moment, db, user_id))


# ============ 5. 删除动态(联动清理 uploads 图片) ============
@router.delete("/delete/{moment_id}")
def delete_moment(
    moment_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除自己的动态(软删除 + 联动清理图片文件)"""
    moment = db.query(Moment).filter(
        Moment.id == moment_id, Moment.status == 1
    ).first()
    if not moment:
        return ResponseBase.error("动态不存在", 404)
    if moment.user_id != user_id:
        return ResponseBase.error("无权删除他人动态", 403)

    # 1. 软删动态
    moment.status = 0
    # 2. 软删关联评论
    db.query(MomentComment).filter(MomentComment.moment_id == moment_id).update({"status": 0})
    # 3. 删除点赞记录
    db.query(MomentLike).filter(MomentLike.moment_id == moment_id).delete()
    # 4. 联动清理 uploads 物理图片文件
    storage = get_storage()
    images_raw = json.loads(moment.images) if moment.images else []
    for rel_path in images_raw:
        storage.delete(rel_path)

    db.commit()
    return ResponseBase.success({"moment_id": moment_id})


# ============ 6. 点赞 / 取消点赞(toggle) ============
@router.post("/like/{moment_id}")
def toggle_like(
    moment_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """切换点赞状态(已点赞则取消, 未点赞则点赞)"""
    moment = db.query(Moment).filter(
        Moment.id == moment_id, Moment.status == 1
    ).first()
    if not moment:
        return ResponseBase.error("动态不存在", 404)

    existing = db.query(MomentLike).filter(
        MomentLike.moment_id == moment_id,
        MomentLike.user_id == user_id,
    ).first()

    if existing:
        # 已点赞 -> 取消
        db.delete(existing)
        moment.like_count = max(0, moment.like_count - 1)
        liked = False
    else:
        # 未点赞 -> 点赞
        like = MomentLike(moment_id=moment_id, user_id=user_id)
        db.add(like)
        moment.like_count = moment.like_count + 1
        liked = True

    db.commit()
    db.refresh(moment)
    return ResponseBase.success({
        "liked": liked,
        "like_count": moment.like_count,
    })


# ============ 7. 点赞用户列表 ============
@router.get("/likers/{moment_id}")
def get_likers(
    moment_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某条动态的点赞用户列表"""
    likers = db.query(MomentLike).filter(
        MomentLike.moment_id == moment_id
    ).order_by(desc(MomentLike.created_at)).all()
    result = []
    for like in likers:
        u = db.query(User).filter(User.id == like.user_id).first()
        if u:
            result.append({
                "id": u.id, "nickname": u.nickname, "avatar": u.avatar,
            })
    return ResponseBase.success(result)


# ============ 8. 发表评论 ============
@router.post("/comment/{moment_id}")
def create_comment(
    moment_id: int,
    payload: MomentCommentCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对动态发表评论"""
    moment = db.query(Moment).filter(
        Moment.id == moment_id, Moment.status == 1
    ).first()
    if not moment:
        return ResponseBase.error("动态不存在", 404)

    # ↓↓↓ 安全合规批次：评论内容前置安全校验 ↓↓↓
    from app.utils.content_security import ContentSecurity
    _sec = ContentSecurity.check_user_text(payload.content or "", max_length=500)
    if not _sec["ok"]:
        return ResponseBase.error(_sec["reason"], 400)
    # ↑↑↑ 新增结束 ↑↑↑

    comment = MomentComment(
        moment_id=moment_id,
        user_id=user_id,
        content=payload.content,
        reply_to_id=payload.reply_to_id or 0,
        status=1,
    )
    db.add(comment)
    moment.comment_count = moment.comment_count + 1
    db.commit()
    db.refresh(comment)
    return ResponseBase.success(_serialize_comment(comment, db))


# ============ 9. 评论列表 ============
@router.get("/comments/{moment_id}")
def get_comments(
    moment_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某条动态的评论列表"""
    moment = db.query(Moment).filter(
        Moment.id == moment_id, Moment.status == 1
    ).first()
    if not moment:
        return ResponseBase.error("动态不存在", 404)
    comments = db.query(MomentComment).filter(
        MomentComment.moment_id == moment_id,
        MomentComment.status == 1,
    ).order_by(MomentComment.created_at.asc()).all()
    result = [_serialize_comment(c, db) for c in comments]
    return ResponseBase.success(result)
