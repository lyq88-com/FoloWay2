-- ============================================================
-- 习惯-伙伴融合 · 打卡上下文延续（2026-10-28）
-- 目标：让一次打卡不再只是「一句一次性鼓励」，而是一段可延续的对话，
--       并且 AI 能串联这条习惯从开始到现在的完整历程。
--
-- 幂等：可重复执行，已存在则跳过。
-- 配套执行器：tools/apply_migration_habit_context.py
-- ============================================================

-- 1) 用户伙伴偏好：新增「按习惯的短期静默表」
--    用户说「先不说这个了 / 不想聊这个」之后，这条习惯静默 3 天：
--    期间不挂载会话上下文、不被主动提起。
SET @db = DATABASE();

SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'user_companion_settings'
    AND COLUMN_NAME = 'muted_habits_json'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE `user_companion_settings` ADD COLUMN `muted_habits_json` TEXT NULL COMMENT ''按习惯的短期静默表 {habit_id: 截止时刻}'' AFTER `habit_topic_off_at`',
  'SELECT ''= user_companion_settings.muted_habits_json 已存在，跳过''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) chat_sessions.habit_id 已存在（阶段J 扩展字段，语义正好就是
--    「这条会话当前挂载的习惯上下文」），本次直接复用，不新增列。
--    值为 0 表示普通闲聊会话。
