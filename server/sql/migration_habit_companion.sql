-- ============================================================
-- 习惯-伙伴融合 迁移（幂等，可重复执行）
-- 数据库: ai_habit_partner (MySQL 8 / utf8mb4)
-- 对应 ORM:
--   server/app/models/habit.py            (habits 新增 5 个生命周期字段)
--   server/app/models/habit_companion.py  (user_companion_settings 新表)
-- 用法: mysql -u root -p ai_habit_partner < migration_habit_companion.sql
-- ============================================================

USE ai_habit_partner;

-- ---------- 1. habits 增加生命周期字段 ----------
-- is_paused: 暂停态。规则：不触发打卡校验、不推送习惯提醒、数据保留不删除
SET @db = 'ai_habit_partner';

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD COLUMN `is_paused` TINYINT NOT NULL DEFAULT 0 COMMENT ''是否暂停 0进行中 1已暂停(不触发打卡校验/不推送提醒/数据保留)''')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND COLUMN_NAME = 'is_paused'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD COLUMN `paused_at` DATETIME NULL COMMENT ''最近一次暂停时间''')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND COLUMN_NAME = 'paused_at'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD COLUMN `paused_reason` VARCHAR(100) NOT NULL DEFAULT '''' COMMENT ''暂停时的状态备注 如 太累了/先放一放''')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND COLUMN_NAME = 'paused_reason'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD COLUMN `resume_count` INT NOT NULL DEFAULT 0 COMMENT ''重启次数(暂停后重新开启累计)''')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND COLUMN_NAME = 'resume_count'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD COLUMN `last_resume_at` DATETIME NULL COMMENT ''最近一次重启时间''')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND COLUMN_NAME = 'last_resume_at'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

SET @sql = (
  SELECT IF(COUNT(*) > 0, 'SELECT 1',
    'ALTER TABLE `habits` ADD INDEX `idx_user_paused` (`user_id`, `is_paused`)')
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'habits' AND INDEX_NAME = 'idx_user_paused'
);
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- ---------- 2. 用户伙伴偏好设置（总开关持久化） ----------
CREATE TABLE IF NOT EXISTS `user_companion_settings` (
  `id`                            BIGINT    NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id`                       BIGINT    NOT NULL COMMENT '用户ID',
  `allow_habit_topic`             TINYINT   NOT NULL DEFAULT 1 COMMENT '【允许伙伴和我聊习惯相关的事】1是 0否',
  `habit_proactive_muted_until`   DATETIME  NULL COMMENT '习惯类主动消息降频截止时刻(负面情绪多时自动设置)',
  `habit_topic_off_at`            DATETIME  NULL COMMENT '最近一次关闭习惯话题的时间',
  `note`                          TEXT      NULL COMMENT '备注',
  `created_at`                    DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`                    DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户与伙伴相处偏好（习惯话题总开关等）';

-- ---------- 3. 徽章种子：重启 / 自我接纳 ----------
INSERT IGNORE INTO `badges` (`code`, `name`, `description`, `icon`, `condition_type`, `condition_value`, `status`)
VALUES
  ('habit_restart',   '重新出发', '停下来之后又把它捡起来了，重新开始同样值得被记住。', '🔄', 'habit_event', 1, 1),
  ('self_acceptance', '自我接纳', '在撑不住的时候选择先照顾自己，而不是硬扛。',         '🫂', 'habit_event', 1, 1);

-- ============================================================
-- 回滚（如需）
-- ALTER TABLE `habits` DROP INDEX `idx_user_paused`;
-- ALTER TABLE `habits` DROP COLUMN `is_paused`,
--                       DROP COLUMN `paused_at`,
--                       DROP COLUMN `paused_reason`,
--                       DROP COLUMN `resume_count`,
--                       DROP COLUMN `last_resume_at`;
-- DROP TABLE IF EXISTS `user_companion_settings`;
-- DELETE FROM `badges` WHERE `code` IN ('habit_restart','self_acceptance');
-- ============================================================
