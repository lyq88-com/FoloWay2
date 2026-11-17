# -*- coding: utf-8 -*-
"""
全局配置管理 - 基于 pydantic-settings 从环境变量/.env 读取
"""
import socket
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def _detect_lan_ip() -> str:
    """
    探测本机当前局域网 IPv4。
    用 UDP connect 到外部地址即可拿到出网网卡的 IP（不会真的发包），拿不到就返回空串。
    用途：开发期自动把本机 IP 补进 CORS 白名单，避免换 WiFi 后真机请求被跨域拦截。
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0] or ""
        finally:
            s.close()
    except Exception:
        return ""


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        # .env 只放非敏感默认值（可以安全分享）；
        # .env.local 放本机/部署的真实密钥，已被 .gitignore 忽略，且优先级更高。
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_name: str = "AI习惯伙伴"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # MySQL
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "ai_habit_partner"

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # 支付
    # 【2026-11-15】支付渠道抽象上线：当前只有 mock（模拟收银台，订单真实落库）。
    # 接入真实渠道时实现 PayProvider 并设置 PAY_PROVIDER=wechat/alipay 即可。
    pay_provider: str = "mock"
    pay_mock_secret: str = ""

    # JWT
    # 【2026-11-15】Flask 鉴权后端已下线，全站只由 FastAPI 签发/校验 token。
    # 生产环境请务必用环境变量 JWT_SECRET 覆盖默认值。
    jwt_secret: str = "ai-habit-partner-v2-secret-2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7
    jwt_admin_expire_hours: int = 2

    # 短信
    sms_code_length: int = 6
    sms_code_expire_minutes: int = 5
    sms_daily_limit: int = 10
    sms_provider: str = "mock"

    # AI
    ai_model: str = "mock"
    ai_api_key: str = ""
    ai_api_base: str = "https://api.openai.com/v1"
    ai_model_name: str = "gpt-4o-mini"
    ai_max_tokens: int = 300
    ai_temperature: float = 0.8

    # OCR
    ocr_provider: str = "mock"
    ocr_api_key: str = ""

    # TTS
    tts_provider: str = "mock"
    tts_api_key: str = ""

    # ASR 语音识别
    asr_provider: str = "mock"
    asr_api_key: str = ""
    asr_api_base: str = "https://api.openai.com/v1"
    asr_model: str = "whisper-1"

    # RTC 实时音视频（当前支持声网 Agora AccessToken2）
    # 【2026-11-15】未填 AGORA_APP_ID / AGORA_APP_CERTIFICATE 时 /rtc/* 返回 503，
    # 前端据此显示「演示模式 · 未接入实时通话」，不会假装接通。
    rtc_provider: str = "none"          # none | agora
    rtc_token_ttl: int = 3600           # token 有效期（秒），建议 600~3600
    agora_app_id: str = ""
    agora_app_certificate: str = ""

    # 翻译
    translate_provider: str = "mock"
    translate_api_key: str = ""

    # 数据加密(AES-GCM, 32字节hex密钥)
    encrypt_key: str = ""

    # 限流
    rate_limit_enabled: bool = True
    rate_limit_login_max: int = 5
    rate_limit_window_minutes: int = 15
    # 仅当部署在可信反向代理（nginx 等）之后时开启；直连时开启会让人伪造
    # X-Forwarded-For 绕过登录限流。
    trust_proxy_headers: bool = False

    # 文件上传
    upload_dir: str = "uploads"
    upload_max_size: int = 10485760

    # 微信
    wx_appid: str = ""
    wx_secret: str = ""

    # 跨域
    # ↓↓↓ 修复 ↓↓↓ 去掉写死的 172.20.10.3（换 WiFi 即失效）；
    # 开发环境下 cors_origin_list 会自动补上本机当前局域网 IP，见该方法。
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:8080,http://localhost:3000"

    # 文件存储
    storage_type: str = "local"  # local | cos
    # ↓↓↓ 修复 ↓↓↓ 原来硬编码 http://172.20.10.3:8000，换 WiFi / 换机器后这个 IP 就废了，
    # 前端拿到的图片 URL 全部打不开。
    # 现在默认为空 = 「返回相对路径 /uploads/...」，由前端按运行环境自行拼前缀：
    #   - H5  走 vite proxy → /uploads/avatar/x.png（不经局域网，永不出错）
    #   - App 由 frontend/common/env.js 里的 LAN_HOST 拼（换 WiFi 时跑 tools 下的脚本一键更新）
    # 需要绝对 URL 时，在 .env 里配 STATIC_BASE_URL=http://<你的局域网IP>:8000 即可。
    static_base_url: str = ""
    # COS 占位字段
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_bucket: str = ""
    cos_region: str = "ap-guangzhou"

    # 【newfunc 增量】个推离线推送配置（未填则自动降级 local 本地通知通道）
    getui_enabled: bool = False
    getui_app_id: str = ""
    getui_app_key: str = ""
    getui_app_secret: str = ""

    @property
    def database_url(self) -> str:
        """MySQL 连接串"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        """Redis 连接串"""
        pwd = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{pwd}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origin_list(self) -> List[str]:
        """跨域白名单列表"""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # ↓↓↓ 修复 ↓↓↓ 白名单里原来写死了 http://172.20.10.3:8080，换 WiFi 后手机/真机
        # 直接用新 IP 访问后端会被 CORS 拦掉。开发环境下自动把本机当前局域网 IP 补进去。
        if self.app_env == "development":
            ip = _detect_lan_ip()
            if ip:
                for port in ("8080", "5173", "5174", "3000"):
                    origin = f"http://{ip}:{port}"
                    if origin not in origins:
                        origins.append(origin)
                origins.append(f"http://{ip}")
        return origins


# 全局单例
settings = Settings()
