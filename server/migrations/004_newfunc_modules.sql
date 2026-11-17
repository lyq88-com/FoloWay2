-- ==================================================================
-- 循途 FoloWay · 增量功能模块（newfunc）建表 SQL
-- 模块：离线消息推送 / 情绪日记日历联动 / 多 AI 伙伴人设与隔离记忆
-- 约束：全部为独立新表，不修改、不依赖改造任何旧表；
--       与旧业务数据（打卡/待办/情绪）仅为只读关联，无外键。
-- 前缀：/api/newfunc/ 的接口统一使用本文件中的 5 张表。
-- ==================================================================

-- 1. 推送记录表（消息通知中心数据源）
CREATE TABLE IF NOT EXISTS `push_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uid` BIGINT NOT NULL COMMENT '所属用户ID',
  `push_type` VARCHAR(20) NOT NULL DEFAULT 'ai_companion' COMMENT '推送类型 checkin_remind打卡未完成/todo_due待办到期/ai_companion AI陪伴/test测试',
  `title` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '通知标题',
  `content` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '通知内容',
  `ref_id` BIGINT NOT NULL DEFAULT 0 COMMENT '关联业务ID(习惯/日程/伙伴ID, 0=无)',
  `jump_page` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '点击通知跳转页面路径',
  `channel` VARCHAR(20) NOT NULL DEFAULT 'local' COMMENT '发送通道 getui个推/local本地轮询',
  `is_read` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读 0否 1是',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1正常 0删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '推送时间',
  PRIMARY KEY (`id`),
  KEY `idx_push_record_uid_time` (`uid`, `created_at`),
  KEY `idx_push_record_uid_type` (`uid`, `push_type`),
  KEY `idx_push_record_dedupe` (`uid`, `push_type`, `ref_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息推送记录(newfunc)';

-- 2. 推送设置表（每用户一行）
CREATE TABLE IF NOT EXISTS `push_setting` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uid` BIGINT NOT NULL COMMENT '用户ID',
  `push_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '总开关 0关 1开',
  `checkin_push_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '打卡未完成提醒 0关 1开',
  `checkin_push_time` VARCHAR(5) NOT NULL DEFAULT '21:30' COMMENT '打卡提醒时间 HH:MM',
  `todo_push_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '待办到期提醒 0关 1开',
  `ai_push_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT 'AI伙伴陪伴消息 0关 1开',
  `ai_frequency` VARCHAR(10) NOT NULL DEFAULT 'medium' COMMENT 'AI消息频率 low每天最多1条/medium最多3条/high最多6条',
  `quiet_enabled` TINYINT NOT NULL DEFAULT 0 COMMENT '免打扰 0关 1开',
  `quiet_start` VARCHAR(5) NOT NULL DEFAULT '23:00' COMMENT '免打扰开始 HH:MM',
  `quiet_end` VARCHAR(5) NOT NULL DEFAULT '08:00' COMMENT '免打扰结束 HH:MM',
  `diary_read_auth` TINYINT NOT NULL DEFAULT 0 COMMENT '是否授权AI伙伴读取全局情绪日历 0否 1是',
  `client_id` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '个推客户端CID(空=未绑定,走本地轮询通道)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_push_setting_uid` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送设置(newfunc)';

-- 3. 情绪日记日历表（按日期聚合：情绪标签/日记/当日总结；情绪明细只读旧表 emotion_records）
CREATE TABLE IF NOT EXISTS `user_diary_mood` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `uid` BIGINT NOT NULL COMMENT '用户ID',
  `diary_date` DATE NOT NULL COMMENT '归属日期',
  `mood_tags` JSON NULL COMMENT '情绪标签数组 如 ["calm","tired"]',
  `mood_score` TINYINT NOT NULL DEFAULT 5 COMMENT '当日心情分 0-10',
  `diary_text` TEXT NULL COMMENT '日记正文',
  `summary` VARCHAR(1000) NOT NULL DEFAULT '' COMMENT '当日总结(手动填写或AI生成)',
  `summary_source` VARCHAR(10) NOT NULL DEFAULT '' COMMENT '总结来源 manual手动/ai自动/空=无总结',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_diary_uid_date` (`uid`, `diary_date`),
  KEY `idx_diary_uid_month` (`uid`, `diary_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪日记日历(newfunc)';

-- 4. AI 伙伴信息表（用户自建人设）
CREATE TABLE IF NOT EXISTS `ai_bot_info` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键(即伙伴ID)',
  `uid` BIGINT NOT NULL COMMENT '所属用户ID',
  `name` VARCHAR(30) NOT NULL COMMENT '伙伴名称',
  `avatar` VARCHAR(20) NOT NULL DEFAULT '🌿' COMMENT '头像(emoji或图片key)',
  `personality` VARCHAR(300) NOT NULL DEFAULT '' COMMENT '性格描述(如 温柔坚定,偶尔毒舌)',
  `speak_style` VARCHAR(300) NOT NULL DEFAULT '' COMMENT '说话风格(如 口语化,爱用比喻,句尾带~)',
  `self_intro` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '自述(背景故事/身份设定)',
  `taboo` VARCHAR(300) NOT NULL DEFAULT '' COMMENT '禁忌(绝不做的事/绝不说的话)',
  `allow_push` TINYINT NOT NULL DEFAULT 1 COMMENT '是否允许该伙伴主动发陪伴消息 0否 1是',
  `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1正常 0已删除',
  `last_chat_at` DATETIME NULL COMMENT '最近一次对话时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_bot_uid` (`uid`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI伙伴人设(newfunc)';

-- 5. AI 伙伴记忆表（按 bot_id 强隔离：不同伙伴记忆互不互通）
CREATE TABLE IF NOT EXISTS `ai_bot_memory` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `bot_id` BIGINT NOT NULL COMMENT '伙伴ID(隔离边界,删除伙伴或重置只清本 bot_id)',
  `uid` BIGINT NOT NULL COMMENT '所属用户ID',
  `mem_type` VARCHAR(20) NOT NULL DEFAULT 'fact' COMMENT '记忆类型 fact事实/preference偏好/emotion情绪事件/dialogue关键对话',
  `content` VARCHAR(500) NOT NULL COMMENT '记忆内容',
  `importance` TINYINT NOT NULL DEFAULT 5 COMMENT '重要度 1-10(召回排序用)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记忆时间',
  PRIMARY KEY (`id`),
  KEY `idx_bot_memory_bot` (`bot_id`, `importance`),
  KEY `idx_bot_memory_uid` (`uid`, `bot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI伙伴隔离记忆(newfunc)';
