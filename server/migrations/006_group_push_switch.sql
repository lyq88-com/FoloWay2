-- ============================================================
-- 006_group_push_switch.sql
-- 模块4｜群聊扩展：群聊消息提醒独立开关
-- 说明：
--   1. 仅新增一列，不删除/重命名/修改原有列，不新增索引，不影响原有查询与写入；
--   2. 存量行自动取默认值 1（开启），与原有推送默认行为一致；
--   3. 服务端 get_or_create_setting() 内已有幂等补列兜底，
--      即使忘记执行本脚本，首次访问推送设置时也会自动补列；
--   4. 回滚：ALTER TABLE `push_setting` DROP COLUMN `group_push_enabled`;
-- ============================================================
ALTER TABLE `push_setting`
  ADD COLUMN `group_push_enabled` TINYINT NOT NULL DEFAULT 1
  COMMENT '群聊消息提醒开关 0关 1开' AFTER `diary_read_auth`;
