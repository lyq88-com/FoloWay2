# -*- coding: utf-8 -*-
"""
「专注」模块 ORM 模型
======================

全部为独立新表，不与任何既有表产生外键耦合，保证隔离（禁止改动旧表）。

表清单：
  focus_task            AI 生成 / 手动创建的任务待办主表
  focus_step            分步引导子步骤
  focus_session         专注番茄计时会话
  focus_record          引导记录（可回放 / 导出）
  focus_dynamic         专注动态（仅自己 / 互关好友可见）
  focus_dynamic_comment 动态留言（含角色 AI 自动鼓励留言）
  focus_dynamic_like    动态点赞
  focus_remind          任务提醒（供本地通知 / 推送消费）
  focus_follow          互关好友（本模块独立的好友关系，实现「互关好友可见」）
  focus_setting         用户开关（专注动态发布 / 专注提醒）
"""
from sqlalchemy import Column, BigInteger, UniqueConstraint
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME, TEXT
from sqlalchemy.sql import func

from app.core.database import Base


# ============================================================
# 1. 任务 / 待办主表
# ============================================================
class FocusTask(Base):
    """一条待办任务：AI 拆解 / 备考计划生成 / 手动创建，均可落在同一张表"""
    __tablename__ = "focus_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    title = Column(VARCHAR(200), nullable=False, comment="任务标题")
    description = Column(VARCHAR(1000), nullable=False, default="", comment="任务描述/考试信息")
    total_steps = Column(INTEGER, nullable=False, default=0, comment="子步骤总数")
    finished_steps = Column(INTEGER, nullable=False, default=0, comment="已完成子步骤数")
    status = Column(TINYINT, nullable=False, default=0, comment="0待办 1进行中 2已完成")
    start_date = Column(VARCHAR(20), nullable=False, default="", comment="开始日期 YYYY-MM-DD")
    due_date = Column(VARCHAR(20), nullable=False, default="", comment="截止日期 YYYY-MM-DD")
    remind_time = Column(VARCHAR(20), nullable=False, default="", comment="每日提醒时间 HH:MM(空=不提醒)")
    tag = Column(VARCHAR(30), nullable=False, default="学习", comment="标签(学习/工作/生活/运动/其他)")
    source = Column(VARCHAR(20), nullable=False, default="manual", comment="来源 manual/ai_split/ai_plan/chat")
    est_minutes = Column(INTEGER, nullable=False, default=25, comment="预估时长(分钟)")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除 0正常 1已删除")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title or "",
            "description": self.description or "",
            "total_steps": self.total_steps or 0,
            "finished_steps": self.finished_steps or 0,
            "status": self.status or 0,
            "start_date": self.start_date or "",
            "due_date": self.due_date or "",
            "remind_time": self.remind_time or "",
            "tag": self.tag or "学习",
            "source": self.source or "manual",
            "est_minutes": self.est_minutes or 25,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else "",
        }


# ============================================================
# 2. 分步引导子步骤
# ============================================================
class FocusStep(Base):
    """大任务拆出的极小单步；界面一次只展示当前这一步"""
    __tablename__ = "focus_step"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False, comment="所属任务ID")
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    step_index = Column(INTEGER, nullable=False, default=0, comment="步骤序号(从1开始)")
    content = Column(VARCHAR(500), nullable=False, comment="这一步要做什么")
    est_minutes = Column(INTEGER, nullable=False, default=5, comment="本步预估分钟数")
    is_finished = Column(TINYINT, nullable=False, default=0, comment="0未完成 1已完成")
    finish_time = Column(DATETIME, nullable=True, comment="完成时间")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 3. 专注计时会话
# ============================================================
class FocusSession(Base):
    """一次番茄专注：开始/结束/时长/是否被打断/黑名单触发次数"""
    __tablename__ = "focus_session"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    task_id = Column(BigInteger, nullable=False, default=0, comment="关联任务ID(0=自由专注)")
    role_id = Column(VARCHAR(30), nullable=False, default="companion", comment="陪伴角色ID(沿用现有角色体系)")
    mode = Column(VARCHAR(20), nullable=False, default="simple", comment="引导模式 simple简单/flow心流")
    start_time = Column(DATETIME, nullable=True, comment="开始时间")
    end_time = Column(DATETIME, nullable=True, comment="结束时间")
    duration = Column(INTEGER, nullable=False, default=0, comment="专注时长(秒)")
    is_interrupted = Column(TINYINT, nullable=False, default=0, comment="是否中途跳出 0否 1是")
    blacklist_trigger_count = Column(INTEGER, nullable=False, default=0, comment="黑名单应用触发拦截次数")
    tag = Column(VARCHAR(30), nullable=False, default="学习", comment="专注标签")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 4. 引导记录（可搜索 / 回放 / 导出）
# ============================================================
class FocusRecord(Base):
    """一次分步引导的完整记录：原始指令 + 全部步骤 + 可导出文本"""
    __tablename__ = "focus_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    origin_prompt = Column(VARCHAR(500), nullable=False, default="", comment="用户的原始指令/任务")
    mode = Column(VARCHAR(20), nullable=False, default="simple", comment="引导模式 simple/flow")
    full_step_list = Column(TEXT, nullable=False, comment="完整步骤列表(JSON数组)")
    export_text = Column(TEXT, nullable=False, default="", comment="导出文本(生成于结束/导出时)")
    duration_seconds = Column(INTEGER, nullable=False, default=0, comment="全程计时(秒)")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 5. 专注动态（轻动态，非公开广场）
# ============================================================
class FocusDynamic(Base):
    """学习/生活碎碎念。visible_type: self=仅自己 / follow=互关好友可见。
    严禁公开全网信息流：查询接口只返回自己的 + 互关好友的。"""
    __tablename__ = "focus_dynamic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="发布者用户ID")
    content = Column(VARCHAR(1000), nullable=False, default="", comment="动态文字")
    image = Column(VARCHAR(500), nullable=False, default="", comment="配图相对路径(单图)")
    visible_type = Column(VARCHAR(10), nullable=False, default="self", comment="可见性 self/follow")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="软删除")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class FocusDynamicComment(Base):
    """动态留言：uid=0 表示 AI 角色自动鼓励留言"""
    __tablename__ = "focus_dynamic_comment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dynamic_id = Column(BigInteger, nullable=False, comment="动态ID")
    uid = Column(BigInteger, nullable=False, default=0, comment="留言者ID(0=AI角色)")
    role_id = Column(VARCHAR(30), nullable=False, default="", comment="AI留言所用角色ID")
    content = Column(VARCHAR(500), nullable=False, comment="留言内容")
    is_ai = Column(TINYINT, nullable=False, default=0, comment="是否AI留言")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


class FocusDynamicLike(Base):
    """动态点赞（同一用户对同一条动态只能点赞一次）"""
    __tablename__ = "focus_dynamic_like"
    __table_args__ = (
        UniqueConstraint("dynamic_id", "from_uid", name="uk_focus_dyn_like"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dynamic_id = Column(BigInteger, nullable=False, comment="动态ID")
    from_uid = Column(BigInteger, nullable=False, comment="点赞者ID")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 6. 任务提醒
# ============================================================
class FocusRemind(Base):
    """任务提醒。前端读取后用本地通知(uni.createPushMessage)调度；
    is_triggered 由客户端触发后回报。"""
    __tablename__ = "focus_remind"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(BigInteger, nullable=False, comment="所属用户ID")
    task_id = Column(BigInteger, nullable=False, default=0, comment="关联任务ID")
    remind_at = Column(VARCHAR(20), nullable=False, comment="提醒时间 YYYY-MM-DD HH:MM")
    text = Column(VARCHAR(200), nullable=False, default="", comment="提醒文案")
    is_triggered = Column(TINYINT, nullable=False, default=0, comment="0待触发 1已触发")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 7. 互关好友（本模块独立关系，仅用于专注动态可见性）
# ============================================================
class FocusFollow(Base):
    """互关 = 双向各一条记录。被任一方拉黑（idea 拉黑）则动态互不可见。"""
    __tablename__ = "focus_follow"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_uid", name="uk_focus_follow_pair"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="关注发起者")
    friend_uid = Column(BigInteger, nullable=False, comment="被关注者")
    create_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp())


# ============================================================
# 8. 用户开关
# ============================================================
class FocusSetting(Base):
    """专注模块开关：动态发布 / 提醒"""
    __tablename__ = "focus_setting"
    __table_args__ = (UniqueConstraint("user_id", name="uk_focus_setting_user"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID(唯一)")
    allow_dynamic = Column(TINYINT, nullable=False, default=1, comment="专注动态发布 1开 0关")
    allow_remind = Column(TINYINT, nullable=False, default=1, comment="专注提醒 1开 0关")
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
