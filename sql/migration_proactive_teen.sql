-- ============================================================
-- migration_proactive_teen.sql —— 安全合规批次
-- users 表新增：允许AI主动消息 / 青少年模式 两个字段（additive，不影响现有数据）
-- 对应模型: app/models/user.py -> User.allow_proactive_msg / User.teen_mode
-- 幂等：MySQL 8 可用 IF NOT EXISTS；5.7 需先查 information_schema（下方存储过程方案）
-- ============================================================

-- 方案A：MySQL 8.0+ 直接执行
-- ALTER TABLE users
--   ADD COLUMN IF NOT EXISTS allow_proactive_msg TINYINT NOT NULL DEFAULT 1 COMMENT '允许AI主动消息 1允许 0关闭',
--   ADD COLUMN IF NOT EXISTS teen_mode TINYINT NOT NULL DEFAULT 0 COMMENT '青少年模式 1开启 0关闭';

-- 方案B：兼容 MySQL 5.7（逐列判断，存在则跳过）
DELIMITER $$
DROP PROCEDURE IF EXISTS _migrate_proactive_teen$$
CREATE PROCEDURE _migrate_proactive_teen()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'allow_proactive_msg'
    ) THEN
        ALTER TABLE users
            ADD COLUMN allow_proactive_msg TINYINT NOT NULL DEFAULT 1
            COMMENT '允许AI主动消息 1允许 0关闭';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'teen_mode'
    ) THEN
        ALTER TABLE users
            ADD COLUMN teen_mode TINYINT NOT NULL DEFAULT 0
            COMMENT '青少年模式 1开启 0关闭';
    END IF;
END$$
DELIMITER ;

CALL _migrate_proactive_teen();
DROP PROCEDURE IF EXISTS _migrate_proactive_teen;

-- 验证：
-- SHOW COLUMNS FROM users LIKE 'allow_proactive_msg';
-- SHOW COLUMNS FROM users LIKE 'teen_mode';
