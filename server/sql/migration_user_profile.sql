-- ============================================================
-- 编辑个人资料：users 表补「个性签名」列（幂等，可重复执行）
-- 背景：前端 profile-edit 有「个性签名」输入，但 users 表原本没有 signature 列，
--       导致签名填了保存后丢失。本脚本只新增列，不动任何既有数据。
-- 用法: mysql -uroot -p ai_habit_partner < sql/migration_user_profile.sql
-- 新环境无需执行：python init_db.py 的 create_all 会按 ORM 模型建出来。
-- ============================================================
SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'signature'
);

SET @ddl := IF(
    @col_exists = 0,
    'ALTER TABLE `users` ADD COLUMN `signature` VARCHAR(200) NOT NULL DEFAULT '''' COMMENT ''个性签名'' AFTER `avatar`',
    'DO 0'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'signature';
