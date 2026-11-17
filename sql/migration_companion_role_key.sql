-- ============================================================
-- 陪伴记录：新增 role_key（20 个具名角色的字符串 id，如 linxi）
--
-- 背景：陪伴模块原先只能选 ai_roles 里的 4 个「人格类型」，
--       与项目的 20 个具名 AI 伙伴（frontend/common/ai-characters.js）是两套数据。
--       本迁移让陪伴记录能记住用户选的是 20 个里的哪一个。
--
-- 零副作用原则：
--   1. 只 ADD COLUMN，不修改、不删除 role_id（世界模块与历史数据仍依赖它）
--   2. 不回填历史数据（role_key 保持空串，由前端按旧逻辑兜底显示）
--   3. 可重复执行（先判断列是否存在）
-- ============================================================

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'companion_records'
    AND COLUMN_NAME = 'role_key'
);

SET @sql := IF(@exist = 0,
  'ALTER TABLE `companion_records` ADD COLUMN `role_key` VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''陪伴角色标识(ai-characters.js 字符串id, 如 linxi)'' AFTER `role_id`',
  'SELECT ''role_key already exists, skip'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 角色名快照：记录开启陪伴时角色叫什么，历史列表不用反查前端常量也能显示
SET @exist2 := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'companion_records'
    AND COLUMN_NAME = 'role_name'
);

SET @sql3 := IF(@exist2 = 0,
  'ALTER TABLE `companion_records` ADD COLUMN `role_name` VARCHAR(50) NOT NULL DEFAULT '''' COMMENT ''陪伴角色名快照'' AFTER `role_key`',
  'SELECT ''role_name already exists, skip'''
);

PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- 顺带给查询加索引（历史按角色筛选时可用）
SET @idx_exist := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'companion_records'
    AND INDEX_NAME = 'idx_user_rolekey'
);

SET @sql2 := IF(@idx_exist = 0,
  'ALTER TABLE `companion_records` ADD KEY `idx_user_rolekey` (`user_id`, `role_key`)',
  'SELECT ''idx_user_rolekey already exists, skip'''
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;
