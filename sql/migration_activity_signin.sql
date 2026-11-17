-- ============================================================
-- 活动模块：每日签到
--
-- 背景：pages/activity/activity 原来是纯占位页（只有一个返回按钮 +「功能建设中」）。
--       本迁移给它提供真正的数据支撑：每日签到 + 连续天数。
--
-- 零副作用：全新表，不碰任何已有表。可重复执行（CREATE TABLE IF NOT EXISTS）。
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_signin` (
  `id`         BIGINT      NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT      NOT NULL COMMENT '用户ID(users.id)',
  `last_date`  DATE        NULL     COMMENT '最近一次签到日期(自然日)',
  `streak`     INT         NOT NULL DEFAULT 0 COMMENT '当前连续签到天数',
  `max_streak` INT         NOT NULL DEFAULT 0 COMMENT '历史最长连续天数',
  `total_days` INT         NOT NULL DEFAULT 0 COMMENT '累计签到天数',
  `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_signin` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户每日签到';
