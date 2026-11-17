-- =============================================================================
-- 阶段J迁移脚本: 习惯-AI全链路融合 数据库扩展
-- 执行方式: 在已初始化的 ai_habit_partner 数据库上执行
-- =============================================================================

USE ai_habit_partner;

-- =============================================================================
-- 1. 扩展 habits 表 (新增4个AI联动字段)
-- =============================================================================
ALTER TABLE habits
  ADD COLUMN IF NOT EXISTS emotion_status VARCHAR(20) NOT NULL DEFAULT 'neutral' COMMENT '最近情绪状态 happy/excited/calm/sad/angry/tired/neutral' AFTER status,
  ADD COLUMN IF NOT EXISTS continuous_day INT NOT NULL DEFAULT 0 COMMENT '连续打卡天数' AFTER emotion_status,
  ADD COLUMN IF NOT EXISTS custom_remind_text VARCHAR(255) NOT NULL DEFAULT '' COMMENT '用户自定义AI提醒话术' AFTER continuous_day,
  ADD COLUMN IF NOT EXISTS habit_type VARCHAR(20) NOT NULL DEFAULT 'other' COMMENT '习惯分类标签 study/sport/sleep/read/health/meditation/work/other' AFTER custom_remind_text,
  ADD COLUMN IF NOT EXISTS ai_style VARCHAR(20) NOT NULL DEFAULT 'gentle' COMMENT '该习惯绑定的AI对话风格 gentle/analytical/humorous/calm' AFTER habit_type;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_habits_type ON habits(habit_type);
CREATE INDEX IF NOT EXISTS idx_habits_continuous ON habits(continuous_day);


-- =============================================================================
-- 2. 扩展 chat_sessions 表 (新增习惯/情绪关联+会话类型)
-- =============================================================================
ALTER TABLE chat_sessions
  ADD COLUMN IF NOT EXISTS habit_id BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联习惯ID(0=纯聊天会话)' AFTER status,
  ADD COLUMN IF NOT EXISTS emotion_id BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联情绪记录ID' AFTER habit_id,
  ADD COLUMN IF NOT EXISTS session_type VARCHAR(20) NOT NULL DEFAULT 'chat' COMMENT '会话类型 chat/checkin_trigger/emotion_guide/mindfulness' AFTER emotion_id,
  ADD COLUMN IF NOT EXISTS dialogue_style VARCHAR(20) NOT NULL DEFAULT 'gentle' COMMENT '当前对话风格 gentle/analytical/humorous/calm' AFTER session_type,
  ADD COLUMN IF NOT EXISTS context_summary TEXT NULL COMMENT '超过30轮后的早期对话压缩摘要' AFTER dialogue_style;

CREATE INDEX IF NOT EXISTS idx_sessions_type ON chat_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_habit ON chat_sessions(habit_id);


-- =============================================================================
-- 3. 扩展 chat_messages 表 (新增习惯/情绪关联+消息类型+关键记忆)
-- =============================================================================
ALTER TABLE chat_messages
  ADD COLUMN IF NOT EXISTS habit_id BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联习惯ID' AFTER tokens,
  ADD COLUMN IF NOT EXISTS emotion_id BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联情绪记录ID' AFTER habit_id,
  ADD COLUMN IF NOT EXISTS message_type VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '消息类型 normal/checkin_link/emotion_guide/achievement/crisis' AFTER emotion_id,
  ADD COLUMN IF NOT EXISTS emotion_intensity TINYINT NOT NULL DEFAULT 0 COMMENT '情绪强度分数 0-10' AFTER message_type,
  ADD COLUMN IF NOT EXISTS is_key_memory TINYINT NOT NULL DEFAULT 0 COMMENT '是否为关键记忆 0否 1是' AFTER emotion_intensity;

CREATE INDEX IF NOT EXISTS idx_messages_type ON chat_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_key_memory ON chat_messages(is_key_memory);


-- =============================================================================
-- 4. 新建: AI用户长期记忆表 (ai_user_memories)
--    存储所有打卡/情绪/对话关键信息供AI上下文调用
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_user_memories (
  id             BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记忆ID',
  user_id        BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id       BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联习惯ID',
  emotion_id     BIGINT       UNSIGNED NOT NULL DEFAULT 0 COMMENT '关联情绪记录ID',
  memory_type    VARCHAR(20)           NOT NULL COMMENT '记忆类型 checkin/emotion/chat/achievement/crisis/plan',
  memory_content TEXT                  NOT NULL COMMENT '记忆内容摘要',
  emotion_score  TINYINT               NOT NULL DEFAULT 5 COMMENT '情绪分数 0-10',
  habit_status   VARCHAR(20)           NOT NULL DEFAULT '' COMMENT '完成状态 completed/failed/partial',
  context_data   JSON                  NULL COMMENT '附加上下文数据',
  is_long_term   TINYINT               NOT NULL DEFAULT 0 COMMENT '是否长期保留 0否 1是',
  created_at     DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_memory_user (user_id),
  KEY idx_memory_user_type (user_id, memory_type),
  KEY idx_memory_habit (habit_id),
  KEY idx_memory_long_term (user_id, is_long_term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI用户长期记忆表';


-- =============================================================================
-- 5. 新建: 习惯连续打卡成就表 (habit_achievements)
--    7/15/30/60/100天五档成就, 每档独立AI专属剧情
-- =============================================================================
CREATE TABLE IF NOT EXISTS habit_achievements (
  id              BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '成就记录ID',
  user_id         BIGINT       UNSIGNED NOT NULL COMMENT '用户ID',
  habit_id        BIGINT       UNSIGNED NOT NULL COMMENT '习惯ID',
  milestone       INT                   NOT NULL COMMENT '成就阈值 7/15/30/60/100',
  character_id    VARCHAR(50)           NOT NULL DEFAULT 'linxi' COMMENT '触发时的AI角色ID',
  dialogue_style  VARCHAR(20)           NOT NULL DEFAULT 'gentle' COMMENT '对话风格',
  ai_dialogue     TEXT                  NULL COMMENT 'AI专属剧情台词',
  comic_image_url VARCHAR(500)          NOT NULL DEFAULT '' COMMENT 'AI漫画日记图片URL',
  diary_content   TEXT                  NULL COMMENT 'AI生成的日记内容',
  is_unlocked     TINYINT               NOT NULL DEFAULT 0 COMMENT '是否已解锁 0否 1是',
  unlocked_at     DATETIME              NULL COMMENT '解锁时间',
  created_at      DATETIME              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_habit_milestone (user_id, habit_id, milestone),
  KEY idx_achievement_user (user_id),
  KEY idx_achievement_unlocked (user_id, is_unlocked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='习惯连续打卡成就表';
