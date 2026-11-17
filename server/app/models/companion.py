# -*- coding: utf-8 -*-
"""
陪伴模式模型 - 陪伴记录(companion_records)
对应前端 frontend/api/companion.js:
  POST /companion/start  开启陪伴(写入一条 status=1 的记录)
  POST /companion/end    结束陪伴(置 status=0, 计算 duration_min)
  GET  /companion/records 陪伴记录列表
"""
from sqlalchemy import Column, BigInteger, TEXT
from sqlalchemy.dialects.mysql import VARCHAR, TINYINT, INTEGER, DATETIME
from sqlalchemy.sql import func

from app.core.database import Base


class CompanionRecord(Base):
    """陪伴记录"""
    __tablename__ = "companion_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    role_id = Column(BigInteger, nullable=False, default=1, comment="陪伴AI角色ID(关联ai_roles.id)")
    # ↓↓↓ 新增：20 个具名角色的字符串标识（frontend/common/ai-characters.js 的 CHARACTERS[].id） ↓↓↓
    # 说明：陪伴模块改投 20 个具名角色后，真正决定「陪你的是谁」的是 role_key；
    #      role_id 保留不动，仅供世界模块与历史数据兼容，不再作为陪伴主角。
    role_key = Column(VARCHAR(64), nullable=False, default="", comment="陪伴角色标识(如 linxi，对应 ai-characters.js)")
    role_name = Column(VARCHAR(50), nullable=False, default="", comment="陪伴角色名快照(记录当时的显示名)")
    # ↑↑↑ 新增结束 ↑↑↑
    scene_type = Column(VARCHAR(20), nullable=False, default="custom", comment="场景类型 sleep/study/work/sport/eat/custom")
    scene_name = Column(VARCHAR(50), nullable=False, default="自定义", comment="场景名称(自定义场景的用户输入)")
    bg_img = Column(VARCHAR(500), nullable=False, default="", comment="背景图标识/URL")
    bg_sound = Column(VARCHAR(50), nullable=False, default="静音", comment="背景音 quiet/rain/fire/wave/forest/piano")
    start_time = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), comment="开始时间")
    end_time = Column(DATETIME, nullable=True, comment="结束时间")
    duration_min = Column(INTEGER, nullable=False, default=0, comment="陪伴时长(分钟)")
    message_count = Column(INTEGER, nullable=False, default=0, comment="陪伴期间聊天消息数")
    remark = Column(TEXT, nullable=True, comment="备注/陪伴小结")
    status = Column(TINYINT, nullable=False, default=1, comment="状态 1陪伴中 0已结束")
    created_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DATETIME, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def to_dict(self):
        """序列化(与前端 mock 字段对齐)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            # ↓↓↓ 新增 ↓↓↓
            "role_key": self.role_key or "",
            "role_name": self.role_name or "",
            # ↑↑↑ 新增结束 ↑↑↑
            "scene_type": self.scene_type,
            "scene_name": self.scene_name,
            "bg_img": self.bg_img,
            "bg_sound": self.bg_sound,
            "start_time": str(self.start_time) if self.start_time else "",
            "end_time": str(self.end_time) if self.end_time else None,
            "duration_min": self.duration_min,
            "message_count": self.message_count,
            "status": self.status,
        }
