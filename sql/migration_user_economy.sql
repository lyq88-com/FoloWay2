-- ============================================================
-- 虚拟经济上云：把 localStorage(xuntu_economy) 搬到 MySQL
-- 可重复执行（CREATE TABLE IF NOT EXISTS）
-- 执行：mysql -u root -p ai_habit_partner < migration_user_economy.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_economy` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` BIGINT NOT NULL COMMENT '用户ID(users.id)',
  `coins` INT NOT NULL DEFAULT 0 COMMENT '金币余额',
  `gacha_tickets` INT NOT NULL DEFAULT 0 COMMENT '扭蛋券数量',
  `total_checkin_rewarded` INT NOT NULL DEFAULT 0 COMMENT '累计打卡奖励次数',
  `gifted_count` INT NOT NULL DEFAULT 0 COMMENT '累计送礼次数',
  `gift_inventory` TEXT NULL COMMENT '礼物背包 JSON {giftId: count}',
  `unlocked_decos` TEXT NULL COMMENT '已解锁装扮/气泡/背景 id 数组 JSON',
  `bills` TEXT NULL COMMENT '收支账单 JSON 数组(最多保留最近300条)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_ue_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户虚拟经济状态(云端, 替代 localStorage xuntu_economy)';
