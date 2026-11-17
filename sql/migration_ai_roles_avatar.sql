-- ============================================================
-- 迁移：ai_roles 增加 avatar（角色头像 emoji）
-- 关联缺陷：BUG-001（陪伴对象选择页头像为空白块、角色列表为硬编码假数据）
-- 执行方式（无 mysql CLI 时）：
--   cd liyeqing\server && python ..\tools\run_sql.py ..\sql\migration_ai_roles_avatar.sql
-- 幂等：列已存在时跳过（由 run_sql.py / 手工执行前先 SHOW COLUMNS 确认）
-- ============================================================

ALTER TABLE ai_roles
  ADD COLUMN avatar VARCHAR(32) NOT NULL DEFAULT '' COMMENT '角色头像emoji' AFTER description;

-- 为已有角色填充头像（按 role_type 区分）
UPDATE ai_roles SET avatar = '🌸' WHERE role_type = 'cute'      AND (avatar = '' OR avatar IS NULL);
UPDATE ai_roles SET avatar = '🌿' WHERE role_type = 'gentle'    AND (avatar = '' OR avatar IS NULL);
UPDATE ai_roles SET avatar = '📘' WHERE role_type = 'serious'   AND (avatar = '' OR avatar IS NULL);
UPDATE ai_roles SET avatar = '⚡' WHERE role_type = 'energetic' AND (avatar = '' OR avatar IS NULL);

-- 兜底：其余未覆盖的 role_type 给一个通用头像
UPDATE ai_roles SET avatar = '🌿' WHERE avatar = '' OR avatar IS NULL;
