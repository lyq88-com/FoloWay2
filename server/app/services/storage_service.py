# -*- coding: utf-8 -*-
"""
文件存储服务 - 抽象层 + 本地存储实现
设计: 优先本地磁盘存储, 后续可平滑替换为腾讯云 COS
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings


class StorageService:
    """存储服务抽象基类"""

    @staticmethod
    def save(file_bytes: bytes, original_name: str, subdir: str = "moment") -> str:
        """
        保存文件, 返回相对路径(用于拼接可访问URL)
        子类必须实现
        """
        raise NotImplementedError

    @staticmethod
    def delete(relative_path: str) -> bool:
        """删除文件, 返回是否成功"""
        raise NotImplementedError

    @staticmethod
    def get_url(relative_path: str) -> str:
        """根据相对路径获取完整可访问URL"""
        raise NotImplementedError


class LocalStorage(StorageService):
    """本地磁盘存储实现"""

    UPLOAD_ROOT = Path("uploads")

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save(file_bytes: bytes, original_name: str, subdir: str = "moment") -> str:
        """保存到 uploads/<subdir>/<uuid>.<ext>"""
        ext = Path(original_name).suffix.lower() or ".jpg"
        # 过滤扩展名, 防止恶意上传
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            ext = ".jpg"

        folder = LocalStorage.UPLOAD_ROOT / subdir
        LocalStorage._ensure_dir(folder)
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = folder / filename
        filepath.write_bytes(file_bytes)

        # 返回相对路径: moment/<filename>
        return f"{subdir}/{filename}"

    @staticmethod
    def delete(relative_path: str) -> bool:
        """删除相对路径对应的文件"""
        try:
            target = LocalStorage.UPLOAD_ROOT / relative_path
            if target.exists() and target.is_file():
                target.unlink()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def _base_url() -> str:
        """
        静态资源前缀。
        # ↓↓↓ 修复 ↓↓↓ 原来在类定义期就把硬编码的 172.20.10.3 固化成 BASE_URL，
        # 换 WiFi 后所有图片 URL 指向不存在的主机。
        # 现在按调用时读取 settings（可用 .env 的 STATIC_BASE_URL 覆盖）；
        # 未配置时返回空串 → get_url 直接产出相对路径 /uploads/xxx，
        # 由前端按运行环境拼前缀（H5 走代理，App 走 frontend/common/env.js 的 LAN_HOST）。
        """
        return (getattr(settings, "static_base_url", "") or "").rstrip("/")

    @staticmethod
    def get_url(relative_path: str) -> str:
        """拼接静态资源URL, 注意 /uploads 前缀"""
        if not relative_path:
            return ""
        if relative_path.startswith(("http://", "https://")):
            return relative_path
        base = LocalStorage._base_url()
        # relative_path 形如 "moment/abc.jpg"
        path = "/uploads/" + relative_path.lstrip("/")
        if not base:
            # 未配置绝对前缀 → 返回相对路径，前端自行拼（换网络也不会失效）
            return path
        return f"{base}{path}"


def get_storage() -> StorageService:
    """根据配置返回存储服务实例"""
    if settings.storage_type == "cos":
        # 预留: 未来实现 CosStorage
        # return CosStorage()
        pass
    return LocalStorage
