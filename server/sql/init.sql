-- =============================================================================
-- AI习惯伙伴 (ai-habit-partner-v2) 数据库初始化脚本
-- 数据库: MySQL 8.0+  字符集: utf8mb4
-- 说明: 可直接执行，包含建库、建表、索引、初始数据
-- =============================================================================

CREATE DATABASE IF NOT EXISTS ai_habit_partner
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_habit_partner;

-- 关闭外键检查，便于重建
SET FOREIGN_KEY_CHECKS = 0;

-- 旧表清理（按依赖倒序）
DROP TABLE IF EXISTS crisis_intervention_logs;
DROP TABLE IF EXISTS checkin_diaries;
DROP TABLE IF EXISTS growth_archives;
DROP TABLE IF EXISTS emotion_reports;
DROP TABLE IF EXISTS audio_resources;
DROP TABLE IF EXISTS mindfulness_plans;
DROP TABLE IF EXISTS mindfulness_sessions;
DROP TABLE IF EXISTS emotion_records;
DROP TABLE IF EXISTS file_uploads;
DROP TABLE IF EXISTS app_configs;
DROP TABLE IF EXISTS operation_logs;
DROP TABLE IF EXISTS sms_codes;
DROP TABLE IF EXISTS daily_reports;
DROP TABLE IF EXISTS push_records;
DROP TABLE IF EXISTS push_tasks;
DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS ai_role_assets;
DROP TABLE IF EXISTS ai_roles;
DROP TABLE IF EXISTS difficulty_logs;
DROP TABLE IF EXISTS checkin_items;
DROP TABLE IF EXISTS checkins;
DROP TABLE IF EXISTS task_templates;
DROP TABLE IF EXISTS habits;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;


-- =============================================================================
-- 1. 用户表 (users) —— C端注册用户
-- =============================================================================
CREATE TABLE users (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  phone           VARCHAR(20)           NOT NULL COMMENT '手机号',
  nickname        VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '昵称',
  avatar          VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '头像URL',
  password_hash   VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '密码哈希(微信登录用户为空)',
  wx_openid       VARCHAR(64)           NOT NULL DEFAULT '' COMMENT '微信OpenID',
  wx_unionid      VARCHAR(64)           NOT NULL DEFAULT '' COMMENT '微信UnionID',
  gender          TINYINT               NOT NULL DEFAULT 0 COMMENT '性别 0未知 1男 2女',
  status          TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1正常 0禁用',
  register_time   DATETIME              NOT NULL COMMENT '注册时间',
  last_login_time DATETIME              NOT NULL COMMENT '最后登录时间',
  last_login_ip   VARCHAR(45)           NOT NULL DEFAULT '' COMMENT '最后登录IP',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_phone (phone),
  UNIQUE KEY uk_wx_openid (wx_openid),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='C端用户表';


-- =============================================================================
-- 2. 管理员表 (admins) —— B端后台管理员
-- =============================================================================
CREATE TABLE admins (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '管理员ID',
  username        VARCHAR(50)           NOT NULL COMMENT '登录用户名',
  password_hash   VARCHAR(255)          NOT NULL COMMENT '密码哈希(bcrypt)',
  nickname        VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '昵称',
  avatar          VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '头像URL',
  role            VARCHAR(20)           NOT NULL DEFAULT 'admin' COMMENT '角色 super_admin/admin/operator',
  status          TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1正常 0禁用',
  last_login_time DATETIME              NOT NULL DEFAULT '1970-01-01 00:00:00' COMMENT '最后登录时间',
  last_login_ip   VARCHAR(45)           NOT NULL DEFAULT '' COMMENT '最后登录IP',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username),
  KEY idx_role_status (role, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='后台管理员表';


-- =============================================================================
-- 3. 任务模板表 (task_templates) —— 管理后台维护的预设习惯模板
-- =============================================================================
CREATE TABLE task_templates (
  id                BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  type              VARCHAR(20)           NOT NULL COMMENT '习惯类型 morning/sport/read等',
  name              VARCHAR(50)           NOT NULL COMMENT '习惯名称',
  icon              VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '图标emoji',
  description       VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '描述',
  default_target    VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '默认目标描述',
  breakdown         JSON                  NULL COMMENT '任务拆解步骤数组',
  difficulty_targets JSON                 NULL COMMENT '各难度目标 {"easy":"","medium":"","hard":""}',
  sort_order        INT                   NOT NULL DEFAULT 0 COMMENT '排序值',
  status            TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  created_by        BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '创建管理员ID',
  created_at        DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at        DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_type (type),
  KEY idx_status_sort (status, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务模板表';


-- =============================================================================
-- 4. 用户习惯配置表 (habits) —— 用户选择的1~3个习惯
-- =============================================================================
CREATE TABLE habits (
  id                   BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '习惯ID',
  user_id              BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  type                 VARCHAR(20)           NOT NULL COMMENT '习惯类型',
  name                 VARCHAR(50)           NOT NULL COMMENT '习惯名称',
  icon                 VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '图标emoji',
  target               VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '目标描述',
  difficulty           VARCHAR(10)           NOT NULL DEFAULT 'medium' COMMENT '难度 easy/medium/hard',
  difficulty_multiplier DECIMAL(3,2)         NOT NULL DEFAULT 1.00 COMMENT '难度倍率',
  last_change_date     DATE                  NULL COMMENT '难度最后变更日期',
  status               TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  created_at           DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at           DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_user_type (user_id, type),
  CONSTRAINT fk_habits_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户习惯配置表';


-- =============================================================================
-- 5. 每日打卡主表 (checkins) —— 每用户每天一条
-- =============================================================================
CREATE TABLE checkins (
  id               BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '打卡记录ID',
  user_id          BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  check_date       DATE                  NOT NULL COMMENT '打卡日期',
  total_count      INT                   NOT NULL DEFAULT 0 COMMENT '当日任务总数',
  completed_count  INT                   NOT NULL DEFAULT 0 COMMENT '当日完成数',
  completion_rate  DECIMAL(5,2)          NOT NULL DEFAULT 0.00 COMMENT '完成率(%)',
  created_at       DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at       DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_date (user_id, check_date),
  KEY idx_date (check_date),
  CONSTRAINT fk_checkins_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日打卡主表';


-- =============================================================================
-- 6. 打卡明细表 (checkin_items) —— 每个习惯的打卡详情
-- =============================================================================
CREATE TABLE checkin_items (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  checkin_id    BIGINT       UNSIGNED NOT NULL COMMENT '打卡主记录ID',
  user_id       BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id      BIGINT       UNSIGNED NOT NULL COMMENT '习惯ID',
  habit_type    VARCHAR(20)           NOT NULL COMMENT '习惯类型(冗余便于统计)',
  checked       TINYINT               NOT NULL DEFAULT 0 COMMENT '是否完成 0否 1是',
  content       TEXT                  NULL COMMENT '打卡文字记录',
  image_url     VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '打卡图片URL',
  checkin_time  DATETIME              NULL COMMENT '打卡时间',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_checkin_habit (checkin_id, habit_id),
  KEY idx_user_date (user_id, habit_type),
  CONSTRAINT fk_items_checkin FOREIGN KEY (checkin_id) REFERENCES checkins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='打卡明细表';


-- =============================================================================
-- 7. 难度变化日志表 (difficulty_logs)
-- =============================================================================
CREATE TABLE difficulty_logs (
  id             BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  user_id        BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id       BIGINT       UNSIGNED NOT NULL COMMENT '习惯ID',
  habit_name     VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '习惯名称',
  old_difficulty VARCHAR(10)           NOT NULL DEFAULT '' COMMENT '原难度',
  new_difficulty VARCHAR(10)           NOT NULL DEFAULT '' COMMENT '新难度',
  change_type    VARCHAR(10)           NOT NULL DEFAULT 'keep' COMMENT '变化类型 up/down/keep',
  old_target     VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '原目标',
  new_target     VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '新目标',
  recent_rate    INT                   NOT NULL DEFAULT 0 COMMENT '触发时7天完成率(%)',
  change_date    DATE                  NOT NULL COMMENT '变更日期',
  created_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_date (user_id, change_date),
  KEY idx_habit (habit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='难度变化日志表';


-- =============================================================================
-- 8. AI角色定义表 (ai_roles) —— 4种角色人格配置
-- =============================================================================
CREATE TABLE ai_roles (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  role_type     VARCHAR(20)           NOT NULL COMMENT '角色类型 cute/gentle/serious/energetic',
  name          VARCHAR(50)           NOT NULL COMMENT '角色名称',
  personality   VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '人格描述',
  description   VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '选择页描述',
  system_prompt TEXT                  NULL COMMENT '系统提示词模板',
  status        TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  sort_order    INT                   NOT NULL DEFAULT 0 COMMENT '排序值',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_type (role_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI角色定义表';


-- =============================================================================
-- 9. AI角色素材表 (ai_role_assets) —— 每角色×6状态的表情素材
-- =============================================================================
CREATE TABLE ai_role_assets (
  id             BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '素材ID',
  role_id        BIGINT       UNSIGNED NOT NULL COMMENT '角色ID',
  emotion_status VARCHAR(20)           NOT NULL COMMENT '情绪状态 normal/happy/sad/gentle/encourage/chat',
  asset_type     VARCHAR(20)           NOT NULL DEFAULT 'image' COMMENT '素材类型 image/animation',
  asset_url      VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '素材URL',
  bubble_text    VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '气泡文字',
  animation_type VARCHAR(20)           NOT NULL DEFAULT 'none' COMMENT '动画类型 bounce/shake/pulse/float/none',
  status         TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  created_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_emotion (role_id, emotion_status),
  KEY idx_role (role_id),
  CONSTRAINT fk_assets_role FOREIGN KEY (role_id) REFERENCES ai_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI角色素材表';


-- =============================================================================
-- 10. 对话会话表 (chat_sessions) —— 管理用户与AI的会话
-- =============================================================================
CREATE TABLE chat_sessions (
  id               BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  user_id          BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  role_type        VARCHAR(20)           NOT NULL DEFAULT 'cute' COMMENT '当前AI角色类型',
  title            VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '会话标题',
  message_count    INT                   NOT NULL DEFAULT 0 COMMENT '消息总数',
  last_message_time DATETIME             NULL COMMENT '最后消息时间',
  status           TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1活跃 0归档',
  created_at       DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at       DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_user_status (user_id, status),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';


-- =============================================================================
-- 11. 对话消息表 (chat_messages) —— 支持上下文记忆
-- =============================================================================
CREATE TABLE chat_messages (
  id           BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  session_id   BIGINT       UNSIGNED NOT NULL COMMENT '会话ID',
  user_id      BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  role         VARCHAR(20)           NOT NULL COMMENT '消息角色 user/assistant/system',
  content      TEXT                  NOT NULL COMMENT '消息内容',
  emotion      VARCHAR(20)           NOT NULL DEFAULT 'neutral' COMMENT '用户情绪 positive/negative/neutral',
  ai_status    VARCHAR(20)           NOT NULL DEFAULT 'chat' COMMENT 'AI状态',
  comfort_text VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '安抚话术(负面情绪时)',
  tokens       INT                   NOT NULL DEFAULT 0 COMMENT 'token消耗',
  created_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_session (session_id, id),
  KEY idx_user_time (user_id, created_at),
  CONSTRAINT fk_messages_session FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';


-- =============================================================================
-- 12. 徽章定义表 (badges)
-- =============================================================================
CREATE TABLE badges (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '徽章ID',
  code            VARCHAR(30)           NOT NULL COMMENT '徽章编码 streak_3/all_done等',
  name            VARCHAR(50)           NOT NULL COMMENT '徽章名称',
  description     VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '徽章描述',
  icon            VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '图标emoji',
  condition_type  VARCHAR(30)           NOT NULL COMMENT '触发类型 streak_days/all_done/checkin_count',
  condition_value INT                   NOT NULL DEFAULT 0 COMMENT '触发阈值',
  status          TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='徽章定义表';


-- =============================================================================
-- 13. 用户徽章记录表 (user_badges)
-- =============================================================================
CREATE TABLE user_badges (
  id         BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  user_id    BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  badge_id   BIGINT       UNSIGNED NOT NULL COMMENT '徽章ID',
  unlocked_at DATETIME             NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '解锁时间',
  created_at DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_badge (user_id, badge_id),
  KEY idx_badge (badge_id),
  CONSTRAINT fk_ub_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_ub_badge FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户徽章记录表';


-- =============================================================================
-- 14. 推送任务表 (push_tasks) —— 定时提醒配置
-- =============================================================================
CREATE TABLE push_tasks (
  id             BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  user_id        BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id       BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联习惯ID(0为通用)',
  push_type      VARCHAR(20)           NOT NULL COMMENT '类型 daily_remind/checkin_encourage/weekly_report/custom',
  title          VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '推送标题',
  content        TEXT                  NULL COMMENT '推送内容',
  scheduled_time DATETIME              NULL COMMENT '计划推送时间',
  repeat_type    VARCHAR(20)           NOT NULL DEFAULT 'none' COMMENT '重复类型 none/daily/weekly',
  repeat_cron    VARCHAR(50)           NOT NULL DEFAULT '' COMMENT 'cron表达式',
  status         TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用 2已完成',
  created_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_status_time (status, scheduled_time),
  CONSTRAINT fk_push_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送任务表';


-- =============================================================================
-- 15. 推送发送记录表 (push_records)
-- =============================================================================
CREATE TABLE push_records (
  id         BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  task_id    BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '推送任务ID',
  user_id    BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  push_type  VARCHAR(20)           NOT NULL COMMENT '推送类型',
  title      VARCHAR(100)          NOT NULL DEFAULT '' COMMENT '标题',
  content    TEXT                  NULL COMMENT '内容',
  channel    VARCHAR(20)           NOT NULL DEFAULT 'in_app' COMMENT '渠道 in_app/wechat/sms',
  status     VARCHAR(20)           NOT NULL DEFAULT 'pending' COMMENT '状态 pending/sent/failed/read',
  sent_time  DATETIME              NULL COMMENT '发送时间',
  read_time  DATETIME              NULL COMMENT '阅读时间',
  error_msg  VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '错误信息',
  created_at DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_task (task_id),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推送发送记录表';


-- =============================================================================
-- 16. 日报/周报数据表 (daily_reports) —— 自动生成统计数据
-- =============================================================================
CREATE TABLE daily_reports (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报告ID',
  user_id         BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  report_date     DATE                  NOT NULL COMMENT '报告日期',
  report_type     VARCHAR(10)           NOT NULL COMMENT '类型 daily/weekly/monthly',
  total_checkins  INT                   NOT NULL DEFAULT 0 COMMENT '累计打卡数',
  completion_rate DECIMAL(5,2)          NOT NULL DEFAULT 0.00 COMMENT '完成率(%)',
  streak_days     INT                   NOT NULL DEFAULT 0 COMMENT '连续天数',
  best_habit      VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '最佳习惯',
  worst_habit     VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '最差习惯',
  summary         TEXT                  NULL COMMENT '报告文案',
  extra_data      JSON                  NULL COMMENT '附加数据(趋势/柱状图数据)',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_date_type (user_id, report_date, report_type),
  KEY idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日报周报数据表';


-- =============================================================================
-- 17. 短信验证码表 (sms_codes)
-- =============================================================================
CREATE TABLE sms_codes (
  id         BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  phone      VARCHAR(20)           NOT NULL COMMENT '手机号',
  code       VARCHAR(10)           NOT NULL COMMENT '验证码',
  purpose    VARCHAR(20)           NOT NULL DEFAULT 'login' COMMENT '用途 login/register',
  sent_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
  expired_at DATETIME              NOT NULL COMMENT '过期时间',
  used       TINYINT               NOT NULL DEFAULT 0 COMMENT '是否已使用 0否 1是',
  ip         VARCHAR(45)           NOT NULL DEFAULT '' COMMENT '请求IP',
  created_at DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_phone_used (phone, used),
  KEY idx_expired (expired_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='短信验证码表';


-- =============================================================================
-- 18. 操作日志表 (operation_logs) —— 全局操作审计
-- =============================================================================
CREATE TABLE operation_logs (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  operator_type VARCHAR(10)           NOT NULL DEFAULT 'user' COMMENT '操作者类型 user/admin',
  operator_id   BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '操作者ID',
  operator_name VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '操作者名称',
  module        VARCHAR(30)           NOT NULL DEFAULT '' COMMENT '模块',
  action        VARCHAR(30)           NOT NULL DEFAULT '' COMMENT '动作',
  method        VARCHAR(10)           NOT NULL DEFAULT '' COMMENT 'HTTP方法',
  path          VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '请求路径',
  params        TEXT                  NULL COMMENT '请求参数',
  result        TEXT                  NULL COMMENT '返回结果',
  ip            VARCHAR(45)           NOT NULL DEFAULT '' COMMENT 'IP',
  user_agent    VARCHAR(255)          NOT NULL DEFAULT '' COMMENT 'User-Agent',
  status        INT                   NOT NULL DEFAULT 200 COMMENT 'HTTP状态码',
  latency_ms    INT                   NOT NULL DEFAULT 0 COMMENT '耗时(毫秒)',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_operator (operator_type, operator_id),
  KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';


-- =============================================================================
-- 19. 系统配置表 (app_configs)
-- =============================================================================
CREATE TABLE app_configs (
  id           BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  config_key   VARCHAR(50)           NOT NULL COMMENT '配置键',
  config_value TEXT                  NULL COMMENT '配置值',
  config_type  VARCHAR(20)           NOT NULL DEFAULT 'string' COMMENT '值类型 string/number/boolean/json',
  description  VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '说明',
  category     VARCHAR(30)           NOT NULL DEFAULT 'system' COMMENT '分类',
  created_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_key (config_key),
  KEY idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';


-- =============================================================================
-- 20. 文件上传记录表 (file_uploads)
-- =============================================================================
CREATE TABLE file_uploads (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文件ID',
  user_id       BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '上传用户ID',
  original_name VARCHAR(255)          NOT NULL DEFAULT '' COMMENT '原始文件名',
  file_path     VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '存储路径',
  file_url      VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '访问URL',
  file_type     VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '文件类型',
  file_size     BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小(字节)',
  mime_type     VARCHAR(100)          NOT NULL DEFAULT '' COMMENT 'MIME类型',
  purpose       VARCHAR(30)           NOT NULL DEFAULT '' COMMENT '用途 avatar/checkin/asset',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_purpose (purpose)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件上传记录表';


-- =============================================================================
-- 21. 情绪打卡记录表 (emotion_records) —— 与习惯打卡融合的情绪记录
-- =============================================================================
CREATE TABLE emotion_records (
  id           BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  user_id      BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id     BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联习惯ID(0=独立情绪记录)',
  emotion      VARCHAR(20)           NOT NULL COMMENT '情绪 happy/excited/calm/sad/angry/tired',
  intensity    TINYINT               NOT NULL DEFAULT 5 COMMENT '情绪强度 0-10',
  tags         JSON                  NULL COMMENT '触发标签 ["work","study","life","family","entertainment"]',
  description  VARCHAR(200)          NOT NULL DEFAULT '' COMMENT '情绪描述(200字内)',
  record_date  DATE                  NOT NULL COMMENT '记录日期(支持补录)',
  created_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_date (user_id, record_date),
  KEY idx_emotion (emotion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪打卡记录表';


-- =============================================================================
-- 22. 正念练习记录表 (mindfulness_sessions) —— 正念/冥想练习记录
-- =============================================================================
CREATE TABLE mindfulness_sessions (
  id               BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  user_id          BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  session_type     VARCHAR(30)           NOT NULL COMMENT '练习类型 breath/body_scan/meditation/anxiety',
  duration_min     INT                   NOT NULL DEFAULT 10 COMMENT '练习时长(分钟)',
  audio_id         BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '使用的音频ID',
  emotion_before   VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '练习前情绪',
  emotion_after    VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '练习后情绪',
  intensity_before TINYINT               NOT NULL DEFAULT 0 COMMENT '练习前强度 0-10',
  intensity_after  TINYINT               NOT NULL DEFAULT 0 COMMENT '练习后强度 0-10',
  completed        TINYINT               NOT NULL DEFAULT 1 COMMENT '是否完成 1是 0否',
  session_date     DATETIME              NOT NULL COMMENT '练习时间',
  created_at       DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_date (user_id, session_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='正念练习记录表';


-- =============================================================================
-- 23. 正念练习计划表 (mindfulness_plans) —— 用户自定义正念练习计划
-- =============================================================================
CREATE TABLE mindfulness_plans (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '计划ID',
  user_id       BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  plan_type     VARCHAR(30)           NOT NULL COMMENT '计划类型 daily/weekly',
  session_type  VARCHAR(30)           NOT NULL COMMENT '练习类型 breath/body_scan/meditation/anxiety',
  reminder_time VARCHAR(10)           NOT NULL DEFAULT '08:00' COMMENT '提醒时间 HH:MM',
  week_days     VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '周几(逗号分隔 1-7, 仅weekly)',
  active        TINYINT               NOT NULL DEFAULT 1 COMMENT '是否启用 1是 0否',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_active (user_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='正念练习计划表';


-- =============================================================================
-- 24. 音频资源表 (audio_resources) —— 正念引导音频资源库
-- =============================================================================
CREATE TABLE audio_resources (
  id          BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '音频ID',
  title       VARCHAR(100)          NOT NULL COMMENT '音频标题',
  audio_type  VARCHAR(30)           NOT NULL COMMENT '类型 breath/body_scan/meditation/anxiety',
  duration_min INT                  NOT NULL DEFAULT 10 COMMENT '时长(分钟)',
  audio_url   VARCHAR(500)          NOT NULL COMMENT '音频文件URL',
  cover_url   VARCHAR(500)          NOT NULL DEFAULT '' COMMENT '封面图URL',
  description TEXT                  NULL COMMENT '音频描述',
  narrator    VARCHAR(50)           NOT NULL DEFAULT '' COMMENT '旁白人',
  sort_order  INT                   NOT NULL DEFAULT 0 COMMENT '排序值',
  status      TINYINT               NOT NULL DEFAULT 1 COMMENT '状态 1启用 0停用',
  created_at  DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_type_status (audio_type, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='音频资源表';


-- =============================================================================
-- 25. 情绪报告表 (emotion_reports) —— 自动生成的情绪分析报告
-- =============================================================================
CREATE TABLE emotion_reports (
  id           BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报告ID',
  user_id      BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  period_type  VARCHAR(10)           NOT NULL COMMENT '周期 7d/30d/90d',
  start_date   DATE                  NOT NULL COMMENT '开始日期',
  end_date     DATE                  NOT NULL COMMENT '结束日期',
  report_data  JSON                  NULL COMMENT '报告数据(趋势/分布/关联分析)',
  pdf_url      VARCHAR(500)          NOT NULL DEFAULT '' COMMENT 'PDF文件URL',
  created_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_period (user_id, period_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪报告表';


-- =============================================================================
-- 26. 成长档案表 (growth_archives) —— 长期情绪成长追踪档案
-- =============================================================================
CREATE TABLE growth_archives (
  id            BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '档案ID',
  user_id       BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  period_type   VARCHAR(10)           NOT NULL COMMENT '周期 monthly/quarterly/yearly',
  period_start  DATE                  NOT NULL COMMENT '周期开始',
  period_end    DATE                  NOT NULL COMMENT '周期结束',
  summary       TEXT                  NULL COMMENT 'AI生成摘要',
  highlights    JSON                  NULL COMMENT '成长亮点',
  suggestions   JSON                  NULL COMMENT '改进建议',
  emotion_trend JSON                  NULL COMMENT '情绪变化趋势数据',
  archive_data  JSON                  NULL COMMENT '完整数据(加密存储)',
  created_at    DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_type (user_id, period_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成长档案表';


-- =============================================================================
-- 27. 打卡日记表 (checkin_diaries) —— 打卡成功后AI生成的日记
-- =============================================================================
CREATE TABLE checkin_diaries (
  id           BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日记ID',
  user_id      BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  checkin_id   BIGINT       UNSIGNED NOT NULL COMMENT '打卡记录ID',
  habit_id     BIGINT       UNSIGNED NOT NULL COMMENT '习惯ID',
  content      TEXT                  NULL COMMENT '日记内容',
  ai_comic_url VARCHAR(500)          NOT NULL DEFAULT '' COMMENT 'AI漫画图URL',
  emotion      VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '打卡时情绪',
  created_at   DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_checkin (user_id, checkin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='打卡日记表';


-- =============================================================================
-- 28. 危机干预记录表 (crisis_intervention_logs) —— 负面情绪危机干预
-- =============================================================================
CREATE TABLE crisis_intervention_logs (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  user_id         BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  trigger_message TEXT                  NULL COMMENT '触发消息内容',
  emotion_level   VARCHAR(10)           NOT NULL DEFAULT 'high' COMMENT '情绪级别 high/critical',
  intervention    TEXT                  NULL COMMENT '干预话术',
  resources       JSON                  NULL COMMENT '提供的紧急联系方式',
  resolved        TINYINT               NOT NULL DEFAULT 0 COMMENT '是否已处理 0否 1是',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='危机干预记录表';


-- =============================================================================
-- 初始数据
-- =============================================================================

-- 默认超级管理员 (用户名: admin  密码: admin123 的bcrypt哈希)
INSERT INTO admins (username, password_hash, nickname, role) VALUES
('admin', '$2b$12$1A09lMTE1jJEf7hu7WpTXeRo0Ra7MMa/OD/4Fg4DHOSnPcK1Yc34m', '超级管理员', 'super_admin');

-- 任务模板初始数据 (8种习惯)
INSERT INTO task_templates (type, name, icon, description, default_target, breakdown, difficulty_targets, sort_order, status) VALUES
('morning',  '早起',    '☀️', '每天早起，开启元气一天', '每天7点前起床',
  JSON_ARRAY('昨晚定好闹钟','闹钟响后立刻起床','喝一杯温水','简单拉伸5分钟'),
  JSON_OBJECT('easy','每天8点前起床','medium','每天7点前起床','hard','每天6点前起床'), 1, 1),
('sport',    '运动',    '🏃', '坚持运动，保持健康体魄', '运动30分钟',
  JSON_ARRAY('换上运动装备','选择运动方式','热身5分钟','按计划完成运动','拉伸放松'),
  JSON_OBJECT('easy','运动18分钟','medium','运动30分钟','hard','运动45分钟'), 2, 1),
('read',     '阅读',    '📚', '每日阅读，持续成长', '阅读20页',
  JSON_ARRAY('选好书籍','设定专注时间','做阅读笔记','回顾今日收获'),
  JSON_OBJECT('easy','阅读12页','medium','阅读20页','hard','阅读30页'), 3, 1),
('drink',    '喝水',    '💧', '科学饮水，保持身体水分', '喝水8杯',
  JSON_ARRAY('准备一杯水放在桌前','每小时喝一次','记录喝水杯数','睡前2小时减少'),
  JSON_OBJECT('easy','喝水5杯','medium','喝水8杯','hard','喝水12杯'), 4, 1),
('sleep',    '早睡',    '🌙', '规律作息，养护身体', '23点前入睡',
  JSON_ARRAY('提前1小时放下手机','调暗灯光','简单冥想放松','准时上床'),
  JSON_OBJECT('easy','24点前入睡','medium','23点前入睡','hard','22点前入睡'), 5, 1),
('meditate', '冥想',    '🧘', '每日冥想，平静内心', '冥想10分钟',
  JSON_ARRAY('找一个安静角落','设定10分钟','专注呼吸','缓慢结束'),
  JSON_OBJECT('easy','冥想6分钟','medium','冥想10分钟','hard','冥想15分钟'), 6, 1),
('write',    '写作',    '✍️', '每日写作，记录所思', '写100字',
  JSON_ARRAY('确定写作主题','写满目标字数','检查一遍','保存记录'),
  JSON_OBJECT('easy','写60字','medium','写100字','hard','写200字'), 7, 1),
('code',     '编程',    '💻', '坚持编码，提升技能', '编程60分钟',
  JSON_ARRAY('确定今日任务','搭建环境','专注编码','提交记录'),
  JSON_OBJECT('easy','编程36分钟','medium','编程60分钟','hard','编程90分钟'), 8, 1);

-- AI角色初始数据 (4种角色)
INSERT INTO ai_roles (role_type, name, personality, description, system_prompt, sort_order, status) VALUES
('cute',     '可爱型', '活泼元气、像小太阳一样', '活泼元气，像小太阳',
  '你是{name}，一个活泼元气、像小太阳一样的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 1, 1),
('gentle',   '温柔型', '温柔体贴、轻声细语', '细腻体贴，轻声陪伴',
  '你是{name}，一个温柔体贴、轻声细语的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 2, 1),
('serious',  '认真型', '认真负责、严谨自律', '严谨自律，督促你',
  '你是{name}，一个认真负责、严谨自律的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 3, 1),
('energetic', '活力型', '热情满满、充满干劲', '热情满满，一起冲',
  '你是{name}，一个热情满满、充满干劲的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 4, 1);

-- AI角色素材初始数据 (4角色 × 6状态 = 24条，先用占位路径)
INSERT INTO ai_role_assets (role_id, emotion_status, asset_type, asset_url, bubble_text, animation_type, status) VALUES
(1,'normal','image','/static/images/ai_cute_normal.png','今天也要加油哦~','none',1),
(1,'happy','image','/static/images/ai_cute_happy.png','太棒了！你真厉害！','bounce',1),
(1,'sad','image','/static/images/ai_cute_sad.png','别灰心，明天会更好','shake',1),
(1,'gentle','image','/static/images/ai_cute_gentle.png','慢慢来，我陪着你','none',1),
(1,'encourage','image','/static/images/ai_cute_encourage.png','你可以的！相信自己！','pulse',1),
(1,'chat','image','/static/images/ai_cute_chat.png','我在听呢~','float',1),
(2,'normal','image','/static/images/ai_gentle_normal.png','今天也要加油哦~','none',1),
(2,'happy','image','/static/images/ai_gentle_happy.png','太棒了！你真厉害！','bounce',1),
(2,'sad','image','/static/images/ai_gentle_sad.png','别灰心，明天会更好','shake',1),
(2,'gentle','image','/static/images/ai_gentle_gentle.png','慢慢来，我陪着你','none',1),
(2,'encourage','image','/static/images/ai_gentle_encourage.png','你可以的！相信自己！','pulse',1),
(2,'chat','image','/static/images/ai_gentle_chat.png','我在听呢~','float',1),
(3,'normal','image','/static/images/ai_serious_normal.png','今天也要加油哦~','none',1),
(3,'happy','image','/static/images/ai_serious_happy.png','太棒了！你真厉害！','bounce',1),
(3,'sad','image','/static/images/ai_serious_sad.png','别灰心，明天会更好','shake',1),
(3,'gentle','image','/static/images/ai_serious_gentle.png','慢慢来，我陪着你','none',1),
(3,'encourage','image','/static/images/ai_serious_encourage.png','你可以的！相信自己！','pulse',1),
(3,'chat','image','/static/images/ai_serious_chat.png','我在听呢~','float',1),
(4,'normal','image','/static/images/ai_energetic_normal.png','今天也要加油哦~','none',1),
(4,'happy','image','/static/images/ai_energetic_happy.png','太棒了！你真厉害！','bounce',1),
(4,'sad','image','/static/images/ai_energetic_sad.png','别灰心，明天会更好','shake',1),
(4,'gentle','image','/static/images/ai_energetic_gentle.png','慢慢来，我陪着你','none',1),
(4,'encourage','image','/static/images/ai_energetic_encourage.png','你可以的！相信自己！','pulse',1),
(4,'chat','image','/static/images/ai_energetic_chat.png','我在听呢~','float',1);

-- 徽章初始数据
INSERT INTO badges (code, name, description, icon, condition_type, condition_value, status) VALUES
('streak_3',  '初出茅庐', '连续打卡3天',   '🌱', 'streak_days',    3,  1),
('streak_7',  '坚持不懈', '连续打卡7天',   '🔥', 'streak_days',    7,  1),
('streak_30', '习惯大师', '连续打卡30天',  '👑', 'streak_days',    30, 1),
('all_done',  '完美一天', '完成今日全部习惯','⭐', 'all_done',       1,  1),
('checkin_100','百次打卡', '累计打卡100次', '💯', 'checkin_count', 100, 1);

-- 系统配置初始数据
INSERT INTO app_configs (config_key, config_value, config_type, description, category) VALUES
('jwt_secret', 'ai-habit-partner-v2-secret-2026', 'string', 'JWT签名密钥', 'security'),
('jwt_expire_days', '7', 'number', 'JWT过期天数', 'security'),
('sms_code_length', '6', 'number', '短信验证码长度', 'sms'),
('sms_code_expire_minutes', '5', 'number', '短信验证码过期分钟', 'sms'),
('ai_model', 'mock', 'string', 'AI模型 mock/openai/qwen', 'ai'),
('ai_max_tokens', '300', 'number', 'AI回复最大token', 'ai'),
('ai_temperature', '0.8', 'number', 'AI温度参数', 'ai'),
('difficulty_up_threshold', '80', 'number', '难度提升完成率阈值(%)', 'difficulty'),
('difficulty_down_threshold', '40', 'number', '难度降低完成率阈值(%)', 'difficulty'),
('upload_max_size', '10485760', 'number', '上传文件最大字节(10MB)', 'upload'),
('ocr_enabled', 'false', 'boolean', 'OCR识别开关', 'ai'),
('tts_enabled', 'false', 'boolean', 'TTS语音开关', 'ai');

-- 音频资源初始数据 (4种类型 x 3档时长 = 12条)
INSERT INTO audio_resources (title, audio_type, duration_min, audio_url, cover_url, description, narrator, sort_order, status) VALUES
('深呼吸入门',     'breath',      5,  '/static/audio/breath_5min.mp3',  '/static/audio/cover_breath.jpg',  '4-7-8呼吸法引导，适合初学者快速放松',       '温柔女声', 1, 1),
('深呼吸进阶',     'breath',      10, '/static/audio/breath_10min.mp3', '/static/audio/cover_breath.jpg',  '更长时间的呼吸调节，深度放松身心',           '温柔女声', 2, 1),
('深呼吸深度',     'breath',      15, '/static/audio/breath_15min.mp3', '/static/audio/cover_breath.jpg',  '深度呼吸练习，彻底释放压力',                 '温柔女声', 3, 1),
('身体扫描入门',   'body_scan',   5,  '/static/audio/scan_5min.mp3',    '/static/audio/cover_scan.jpg',    '从头部到脚趾的快速身体扫描',                 '沉稳男声', 4, 1),
('身体扫描进阶',   'body_scan',   10, '/static/audio/scan_10min.mp3',   '/static/audio/cover_scan.jpg',    '更细致的身体感知练习，感受每一处紧张',       '沉稳男声', 5, 1),
('身体扫描深度',   'body_scan',   20, '/static/audio/scan_20min.mp3',   '/static/audio/cover_scan.jpg',    '全身深度扫描，释放深层肌肉紧张',             '沉稳男声', 6, 1),
('正念冥想入门',   'meditation',  5,  '/static/audio/med_5min.mp3',     '/static/audio/cover_med.jpg',     '5分钟快速冥想，专注当下',                     '温柔女声', 7, 1),
('正念冥想进阶',   'meditation',  15, '/static/audio/med_15min.mp3',    '/static/audio/cover_med.jpg',     '15分钟深度冥想，培养觉察能力',               '温柔女声', 8, 1),
('正念冥想深度',   'meditation',  30, '/static/audio/med_30min.mp3',    '/static/audio/cover_med.jpg',     '30分钟深度冥想，体验内心宁静',               '温柔女声', 9, 1),
('焦虑缓解入门',   'anxiety',     5,  '/static/audio/anxiety_5min.mp3', '/static/audio/cover_anxiety.jpg', '5分钟快速缓解焦虑，安定情绪',                '沉稳男声', 10, 1),
('焦虑缓解进阶',   'anxiety',     15, '/static/audio/anxiety_15min.mp3','/static/audio/cover_anxiety.jpg', '15分钟焦虑释放，找回内心平静',               '沉稳男声', 11, 1),
('焦虑缓解深度',   'anxiety',     25, '/static/audio/anxiety_25min.mp3','/static/audio/cover_anxiety.jpg', '25分钟深度焦虑缓解，重建安全感',             '沉稳男声', 12, 1);

-- =============================================================================
-- 结束
-- =============================================================================
