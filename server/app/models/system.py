# -*- coding: utf-8 -*-
"""
系统模型 - 推送/报告/验证码/日志/配置/文件
"""
from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DECIMAL, DATE, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


class PushTask(Base):
    """推送任务(定时提醒)"""
    __tablename__ = "push_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    habit_id = Column(BigInteger, nullable=False, default=0, comment="关联习惯ID(0为通用)")
    push_type = Column(VARCHAR(20), nullable=False, comment="类型 daily_remind/checkin_encourage/weekly_report/custom")
    title = Column(VARCHAR(100), nullable=False, default="", comment="推送标题")
    content = Column(TEXT, nullable=True, comment="推送内容")
    scheduled_time = Column(DATETIME, nullable=True, comment="计划推送时间")
    repeat_type = Column(VARCHAR(20), nullable=False, default="none", comment="重复类型 none/daily/weekly")
    repeat_cron = Column(VARCHAR(50), nullable=False, default="", comment="cron表达式")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1启用 0停用 2已完成")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PushRecord(Base):
    """推送发送记录"""
    __tablename__ = "push_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False, default=0, comment="推送任务ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    push_type = Column(VARCHAR(20), nullable=False, comment="推送类型")
    title = Column(VARCHAR(100), nullable=False, default="", comment="标题")
    content = Column(TEXT, nullable=True, comment="内容")
    channel = Column(VARCHAR(20), nullable=False, default="in_app", comment="渠道 in_app/wechat/sms")
    status = Column(VARCHAR(20), nullable=False, default="pending", comment="状态 pending/sent/failed/read")
    sent_time = Column(DATETIME, nullable=True, comment="发送时间")
    read_time = Column(DATETIME, nullable=True, comment="阅读时间")
    error_msg = Column(VARCHAR(255), nullable=False, default="", comment="错误信息")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class DailyReport(Base):
    """日报/周报数据"""
    __tablename__ = "daily_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    report_date = Column(DATE, nullable=False, comment="报告日期")
    report_type = Column(VARCHAR(10), nullable=False, comment="类型 daily/weekly/monthly")
    total_checkins = Column(INTEGER, nullable=False, default=0, comment="累计打卡数")
    completion_rate = Column(DECIMAL(5, 2), nullable=False, default=0, comment="完成率(%)")
    streak_days = Column(INTEGER, nullable=False, default=0, comment="连续天数")
    best_habit = Column(VARCHAR(50), nullable=False, default="", comment="最佳习惯")
    worst_habit = Column(VARCHAR(50), nullable=False, default="", comment="最差习惯")
    summary = Column(TEXT, nullable=True, comment="报告文案")
    extra_data = Column(JSON, nullable=True, comment="附加数据(趋势/柱状图数据)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class SmsCode(Base):
    """短信验证码"""
    __tablename__ = "sms_codes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(VARCHAR(20), nullable=False, comment="手机号")
    code = Column(VARCHAR(10), nullable=False, comment="验证码")
    purpose = Column(VARCHAR(20), nullable=False, default="login", comment="用途 login/register")
    sent_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="发送时间")
    expired_at = Column(DATETIME, nullable=False, comment="过期时间")
    used = Column(TINYINT, nullable=False, default=0, comment="是否已使用 0否 1是")
    ip = Column(VARCHAR(45), nullable=False, default="", comment="请求IP")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class OperationLog(Base):
    """操作审计日志"""
    __tablename__ = "operation_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    operator_type = Column(VARCHAR(10), nullable=False, default="user", comment="操作者类型 user/admin")
    operator_id = Column(BigInteger, nullable=False, default=0, comment="操作者ID")
    operator_name = Column(VARCHAR(50), nullable=False, default="", comment="操作者名称")
    module = Column(VARCHAR(30), nullable=False, default="", comment="模块")
    action = Column(VARCHAR(30), nullable=False, default="", comment="动作")
    method = Column(VARCHAR(10), nullable=False, default="", comment="HTTP方法")
    path = Column(VARCHAR(255), nullable=False, default="", comment="请求路径")
    params = Column(TEXT, nullable=True, comment="请求参数")
    result = Column(TEXT, nullable=True, comment="返回结果")
    ip = Column(VARCHAR(45), nullable=False, default="", comment="IP")
    user_agent = Column(VARCHAR(255), nullable=False, default="", comment="User-Agent")
    status = Column(INTEGER, nullable=False, default=200, comment="HTTP状态码")
    latency_ms = Column(INTEGER, nullable=False, default=0, comment="耗时(毫秒)")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class AppConfig(Base):
    """系统配置"""
    __tablename__ = "app_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(VARCHAR(50), nullable=False, unique=True, comment="配置键")
    config_value = Column(TEXT, nullable=True, comment="配置值")
    config_type = Column(VARCHAR(20), nullable=False, default="string", comment="值类型 string/number/boolean/json")
    description = Column(VARCHAR(255), nullable=False, default="", comment="说明")
    category = Column(VARCHAR(30), nullable=False, default="system", comment="分类")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class FileUpload(Base):
    """文件上传记录"""
    __tablename__ = "file_uploads"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, default=0, comment="上传用户ID")
    original_name = Column(VARCHAR(255), nullable=False, default="", comment="原始文件名")
    file_path = Column(VARCHAR(500), nullable=False, default="", comment="存储路径")
    file_url = Column(VARCHAR(500), nullable=False, default="", comment="访问URL")
    file_type = Column(VARCHAR(50), nullable=False, default="", comment="文件类型")
    file_size = Column(BigInteger, nullable=False, default=0, comment="文件大小(字节)")
    mime_type = Column(VARCHAR(100), nullable=False, default="", comment="MIME类型")
    purpose = Column(VARCHAR(30), nullable=False, default="", comment="用途 avatar/checkin/asset")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
