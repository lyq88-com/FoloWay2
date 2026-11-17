-- ============================================
-- 朋友圈三张表: moments / moment_likes / moment_comments
-- 库: ai_habit_partner (与现有表共用)
-- ============================================

-- 1. 朋友圈动态表
CREATE TABLE IF NOT EXISTS `moments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '发布者用户ID',
  `content` TEXT NULL COMMENT '文字内容',
  `images` TEXT NOT NULL DEFAULT '' COMMENT '图片URL数组JSON',
  `location` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '位置',
  `like_count` BIGINT NOT NULL DEFAULT 0 COMMENT '点赞数(冗余)',
  `comment_count` BIGINT NOT NULL DEFAULT 0 COMMENT '评论数(冗余)',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 0已删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_moments_user` (`user_id`),
  KEY `idx_moments_status_created` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='朋友圈动态';

-- 2. 点赞表(带唯一约束, 防止重复点赞)
CREATE TABLE IF NOT EXISTS `moment_likes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `moment_id` BIGINT NOT NULL COMMENT '动态ID',
  `user_id` BIGINT NOT NULL COMMENT '点赞用户ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_moment_user_like` (`moment_id`, `user_id`),
  KEY `idx_moment_likes_moment` (`moment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='朋友圈点赞';

-- 3. 评论表
CREATE TABLE IF NOT EXISTS `moment_comments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `moment_id` BIGINT NOT NULL COMMENT '动态ID',
  `user_id` BIGINT NOT NULL COMMENT '评论用户ID',
  `content` VARCHAR(500) NOT NULL COMMENT '评论内容',
  `reply_to_id` BIGINT NOT NULL DEFAULT 0 COMMENT '回复的评论ID(0=直接评论)',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 0已删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_moment_comments_moment` (`moment_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='朋友圈评论';
