# -*- coding: utf-8 -*-
"""
语音日记 API - 录音上传/SSE转写/CRUD/分类/翻译/统计/备份
"""
import os
import json
import asyncio
from datetime import date

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.voice_diary import VoiceDiary, VoiceDiaryCategory
from app.schemas.common import ResponseBase
from app.schemas.voice_diary import (
    VoiceDiaryCreate, VoiceDiaryUpdate, TranscribeRequest,
    TranslateRequest, CategoryCreate, CategoryUpdate,
)
from app.services.voice_service import ASRService, ASRError, TranslateService, VoiceDiaryService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/voice-diary", tags=["语音日记"])


# ---------- 上传与转写 ----------

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    """上传音频文件, 返回 file_id(后续转写/创建日记引用)"""
    content = await file.read()
    if len(content) > settings.upload_max_size:
        return ResponseBase.error("文件过大(超过10MB)", 400)
    saved = VoiceDiaryService.save_upload(content, file.filename or "")
    return ResponseBase.success({
        "file_id": saved["file_id"],
        "url": saved["url"],
        "size": saved["size"],
        "filename": file.filename,
    })


@router.get("/asr-status")
def asr_status(user_id: int = Depends(get_current_user)):
    """语音识别渠道状态（前端录音前检测；未配置时提示，而不是插入假文本）"""
    return ResponseBase.success(ASRService.status())


@router.post("/transcribe")
async def transcribe_audio(req: TranscribeRequest, user_id: int = Depends(get_current_user)):
    """语音转文字(SSE流式返回转写片段)"""
    # SSE 一旦开流就无法再改 HTTP 状态码，因此先做渠道预检
    try:
        ASRService.preflight()
    except ASRError as e:
        return ResponseBase.error(e.message, e.code)

    upload_dir = settings.upload_dir
    # 根据 file_id 查找已上传文件
    file_path = None
    for fn in os.listdir(upload_dir) if os.path.isdir(upload_dir) else []:
        if req.file_id in fn:
            file_path = os.path.join(upload_dir, fn)
            break
    if not file_path:
        return ResponseBase.error("音频文件不存在, 请先上传", 404)

    async def event_stream():
        try:
            # 真实转写是同步 HTTP 调用，放进线程池，避免阻塞事件循环（尤其真实渠道 60s 超时）
            full_text = await run_in_threadpool(ASRService.transcribe, file_path, req.language)
            for seg in ASRService.split_phrases(full_text):
                await asyncio.sleep(0.05)  # 模拟转写延迟
                yield f"data: {json.dumps({'content': seg, 'done': False}, ensure_ascii=False)}\n\n"
            final = {"content": "", "done": True, "full_text": full_text}
            final.update(ASRService.result_meta())
            yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
        except ASRError as e:
            # 真实渠道中途失败：明确告知前端，绝不返回伪造文本
            payload = {"content": "", "done": True, "error": e.message, "code": e.code}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except Exception as e:
            print(f"[voice-diary] 转写流异常: {e}")
            payload = {"content": "", "done": True, "error": "语音识别中断，请重试", "code": 502}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/translate")
def translate_text(req: TranslateRequest, user_id: int = Depends(get_current_user)):
    """文本多语言翻译"""
    if not req.text.strip():
        return ResponseBase.error("翻译内容不能为空", 400)
    result = TranslateService.translate(req.text, req.target_lang)
    return ResponseBase.success(result)


# ---------- 日记 CRUD ----------

@router.post("/create")
def create_diary(req: VoiceDiaryCreate, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """创建语音日记(自动情感分析)"""
    if not req.content and not req.content_edit:
        return ResponseBase.error("日记内容不能为空", 400)
    diary = VoiceDiaryService.create_diary(db, user_id, req)
    return ResponseBase.success(VoiceDiaryService.to_dict(diary))


@router.get("/list")
def list_diaries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query("", description="分类筛选(空=全部)"),
    start_date: str = Query("", description="开始日期 YYYY-MM-DD"),
    end_date: str = Query("", description="结束日期 YYYY-MM-DD"),
    keyword: str = Query("", description="关键词搜索(标题/内容)"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """日记列表(分页+筛选+搜索)"""
    result = VoiceDiaryService.list_diaries(
        db, user_id, page, page_size, category, start_date, end_date, keyword
    )
    return ResponseBase.success(result)


@router.get("/detail/{diary_id}")
def get_diary_detail(diary_id: int, user_id: int = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """日记详情"""
    diary = db.query(VoiceDiary).filter(
        VoiceDiary.id == diary_id, VoiceDiary.user_id == user_id
    ).first()
    if not diary:
        return ResponseBase.error("日记不存在", 404)
    return ResponseBase.success(VoiceDiaryService.to_dict(diary))


@router.put("/update/{diary_id}")
def update_diary(diary_id: int, req: VoiceDiaryUpdate,
                 user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """编辑日记(文本/标题/分类/译文)"""
    diary = db.query(VoiceDiary).filter(
        VoiceDiary.id == diary_id, VoiceDiary.user_id == user_id
    ).first()
    if not diary:
        return ResponseBase.error("日记不存在", 404)

    changed_content = False
    if req.title is not None:
        diary.title = req.title
    if req.content_edit is not None:
        diary.content_edit = req.content_edit
        changed_content = True
    if req.category is not None:
        diary.category = req.category
    if req.mood is not None:
        diary.mood = req.mood
    if req.remind_time is not None:
        diary.remind_time = req.remind_time
    if req.translation is not None:
        diary.translation = req.translation
    if req.translate_lang is not None:
        diary.translate_lang = req.translate_lang

    # 内容变更后重新情感分析
    if changed_content:
        final_text = diary.content_edit if diary.content_edit else (diary.content or "")
        sentiment = VoiceDiaryService.sentiment_from_text(final_text)
        diary.sentiment_score = sentiment["sentiment_score"]
        diary.sentiment_label = sentiment["sentiment_label"]

    db.commit()
    db.refresh(diary)
    return ResponseBase.success(VoiceDiaryService.to_dict(diary))


@router.delete("/delete/{diary_id}")
def delete_diary(diary_id: int, user_id: int = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """删除日记(同时删除音频文件)"""
    diary = db.query(VoiceDiary).filter(
        VoiceDiary.id == diary_id, VoiceDiary.user_id == user_id
    ).first()
    if not diary:
        return ResponseBase.error("日记不存在", 404)
    # 删除音频文件
    if diary.audio_url:
        local_path = diary.audio_url.lstrip("/").replace("uploads/", settings.upload_dir + "/", 1)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except OSError:
                pass
    db.delete(diary)
    db.commit()
    return ResponseBase.success({"id": diary_id})


# ---------- 分类管理 ----------

@router.get("/categories")
def get_categories(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """分类列表(默认+自定义)"""
    return ResponseBase.success(VoiceDiaryService.get_categories(db, user_id))


@router.post("/category/create")
def create_category(req: CategoryCreate, user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """创建自定义分类"""
    # 同名检查
    exists = db.query(VoiceDiaryCategory).filter(
        VoiceDiaryCategory.user_id == user_id, VoiceDiaryCategory.name == req.name
    ).first()
    if exists:
        return ResponseBase.error("分类名称已存在", 409)
    cat = VoiceDiaryCategory(user_id=user_id, name=req.name, icon=req.icon, color=req.color)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ResponseBase.success({"id": cat.id, "name": cat.name, "icon": cat.icon, "color": cat.color})


@router.put("/category/update")
def update_category(req: CategoryUpdate, user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """更新自定义分类"""
    cat = db.query(VoiceDiaryCategory).filter(
        VoiceDiaryCategory.id == req.id, VoiceDiaryCategory.user_id == user_id
    ).first()
    if not cat:
        return ResponseBase.error("分类不存在", 404)
    if req.name is not None:
        cat.name = req.name
    if req.icon is not None:
        cat.icon = req.icon
    if req.color is not None:
        cat.color = req.color
    if req.sort is not None:
        cat.sort = req.sort
    db.commit()
    return ResponseBase.success({"id": cat.id})


@router.delete("/category/delete/{cat_id}")
def delete_category(cat_id: int, user_id: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """删除自定义分类(该分类下的日记移至 other)"""
    cat = db.query(VoiceDiaryCategory).filter(
        VoiceDiaryCategory.id == cat_id, VoiceDiaryCategory.user_id == user_id
    ).first()
    if not cat:
        return ResponseBase.error("分类不存在", 404)
    cat_key = f"custom_{cat_id}"
    db.query(VoiceDiary).filter(
        VoiceDiary.user_id == user_id, VoiceDiary.category == cat_key
    ).update({"category": "other"})
    db.delete(cat)
    db.commit()
    return ResponseBase.success({"id": cat_id})


# ---------- 统计与备份 ----------

@router.get("/stats")
def get_stats(period: str = Query("30d"), user_id: int = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """日记统计分析"""
    return ResponseBase.success(VoiceDiaryService.get_stats(db, user_id, period))


@router.get("/backup/export")
def backup_export(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """备份导出(全量JSON, 可保存到本地或云端)"""
    return ResponseBase.success(VoiceDiaryService.backup_export(db, user_id))
