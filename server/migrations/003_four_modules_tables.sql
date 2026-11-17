-- ============================================================================
-- 四大新增模块建表 SQL（AI习惯打卡陪伴 App · 库 ai_habit_partner）
--   模块1 世界世界观: worlds / world_roles / world_notes / world_note_comments
--                     world_plots / world_plot_unlocks / world_relations
--   模块2 日程提醒:   schedules
--   模块3 互动扭蛋:   gacha_templates / user_gacha_wallet / user_gacha_records
--                     user_gacha_favorites
-- 全部使用 InnoDB + utf8mb4，可重复执行（IF NOT EXISTS）
-- ============================================================================

-- ============ 模块2：日程提醒 ============
CREATE TABLE IF NOT EXISTS `schedules` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
  `title` VARCHAR(100) NOT NULL COMMENT '日程标题',
  `description` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '日程备注',
  `schedule_date` DATE NOT NULL COMMENT '日程日期',
  `start_time` VARCHAR(5) NOT NULL DEFAULT '08:00' COMMENT '开始时间 HH:MM',
  `end_time` VARCHAR(5) NOT NULL DEFAULT '09:00' COMMENT '结束时间 HH:MM',
  `habit_id` BIGINT NOT NULL DEFAULT 0 COMMENT '绑定习惯ID(0=未绑定，完成日程自动打卡)',
  `is_done` TINYINT NOT NULL DEFAULT 0 COMMENT '是否完成 0否 1是',
  `source` VARCHAR(10) NOT NULL DEFAULT 'manual' COMMENT '来源 manual用户创建 ai伙伴生成',
  `remind_minutes` INT NOT NULL DEFAULT 5 COMMENT '提前提醒分钟数',
  `reminded` TINYINT NOT NULL DEFAULT 0 COMMENT '今日是否已推送提醒 0否 1是',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1正常 0删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sched_user_date` (`user_id`, `schedule_date`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日程提醒';

-- ============ 模块3：互动扭蛋机 ============
-- 扭蛋剧本模板（官方 + 用户自创）
CREATE TABLE IF NOT EXISTS `gacha_templates` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `creator_id` BIGINT NOT NULL DEFAULT 0 COMMENT '创建者用户ID(0=官方)',
  `title` VARCHAR(100) NOT NULL COMMENT '剧本标题',
  `description` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '剧本简介',
  `category` VARCHAR(20) NOT NULL DEFAULT 'chat' COMMENT '分类 companion陪伴打卡/emotion情绪倾诉/chat趣味闲聊',
  `opening_text` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '抽中后AI开场白',
  `questions` TEXT NULL COMMENT '剧情问答JSON [{question, options:[], hint}]',
  `is_official` TINYINT NOT NULL DEFAULT 0 COMMENT '是否官方 1是 0否',
  `use_count` INT NOT NULL DEFAULT 0 COMMENT '被抽取次数(最热排序依据)',
  `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1上架 0下架',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_gacha_cat_stat` (`category`, `status`),
  KEY `idx_gacha_creator` (`creator_id`, `status`),
  KEY `idx_gacha_hot` (`status`, `use_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='扭蛋剧本模板';

-- 用户扭蛋币钱包（打卡赚取，不充值）
CREATE TABLE IF NOT EXISTS `user_gacha_wallet` (
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `coin_balance` INT NOT NULL DEFAULT 0 COMMENT '当前扭蛋币余额',
  `total_earned` INT NOT NULL DEFAULT 0 COMMENT '累计获得',
  `total_cost` INT NOT NULL DEFAULT 0 COMMENT '累计消耗',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户扭蛋币钱包';

-- 用户扭蛋抽取记录
CREATE TABLE IF NOT EXISTS `user_gacha_records` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `template_id` BIGINT NOT NULL COMMENT '抽中的剧本ID',
  `cost` INT NOT NULL DEFAULT 10 COMMENT '本次消耗扭蛋币',
  `status` VARCHAR(10) NOT NULL DEFAULT 'drawn' COMMENT 'drawn已抽取 finished已完成',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `finished_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_egg_rec_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户扭蛋记录';

-- 用户收藏的扭蛋剧本
CREATE TABLE IF NOT EXISTS `user_gacha_favorites` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `template_id` BIGINT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_gacha_fav` (`user_id`, `template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏扭蛋';

-- ============ 模块1+4：世界世界观 + AI角色互动笔记 ============
-- 世界
CREATE TABLE IF NOT EXISTS `worlds` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `creator_id` BIGINT NOT NULL COMMENT '创建者用户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '世界名字',
  `description` VARCHAR(1000) NOT NULL DEFAULT '' COMMENT '世界描述',
  `rules` TEXT NULL COMMENT '世界观规则',
  `cover` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '封面图URL',
  `is_public` TINYINT NOT NULL DEFAULT 1 COMMENT '公开1 / 私人0（私人仅本人可见）',
  `member_count` INT NOT NULL DEFAULT 1 COMMENT '成员数（冗余）',
  `note_count` INT NOT NULL DEFAULT 0 COMMENT '笔记数（冗余）',
  `checkin_target` INT NOT NULL DEFAULT 3 COMMENT '解锁下一段剧情所需打卡数',
  `checkin_total` INT NOT NULL DEFAULT 0 COMMENT '世界内累计打卡数（冗余）',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1正常 0删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_worlds_public` (`is_public`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='虚拟世界';

-- 世界成员（AI角色 + 用户，用 join_type 区分）
CREATE TABLE IF NOT EXISTS `world_roles` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `world_id` BIGINT NOT NULL COMMENT '世界ID',
  `role_id` BIGINT NOT NULL DEFAULT 0 COMMENT 'AI角色ID(ai_roles.id；自定义角色为0)',
  `role_name` VARCHAR(50) NOT NULL DEFAULT '' COMMENT '角色名（AI名/用户名/自设名）',
  `role_avatar` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '角色头像(emoji或URL)',
  `is_custom` TINYINT NOT NULL DEFAULT 0 COMMENT '是否自设角色 1是 0否',
  `join_type` VARCHAR(10) NOT NULL DEFAULT 'ai' COMMENT 'ai角色 / user用户',
  `user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '用户成员的用户ID（AI行为0）',
  `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否在世界内 1在 0已退出',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_wr_world` (`world_id`, `is_active`),
  KEY `idx_wr_user` (`user_id`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='世界成员关联';

-- 世界笔记（AI角色笔记 + 用户打卡笔记）
CREATE TABLE IF NOT EXISTS `world_notes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `world_id` BIGINT NOT NULL COMMENT '世界ID',
  `author_role_id` BIGINT NOT NULL DEFAULT 0 COMMENT 'AI作者角色ID（用户笔记为0）',
  `author_user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '用户作者ID（AI笔记为0）',
  `author_name` VARCHAR(50) NOT NULL DEFAULT '' COMMENT '作者显示名',
  `author_avatar` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '作者头像',
  `note_type` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT 'normal普通/checkin打卡笔记/feedback打卡AI反馈/system系统',
  `content` VARCHAR(1000) NOT NULL COMMENT '笔记内容',
  `related_user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '反馈/关联的用户ID',
  `related_habit_id` BIGINT NOT NULL DEFAULT 0 COMMENT '关联习惯ID',
  `comment_count` INT NOT NULL DEFAULT 0 COMMENT '评论数（冗余）',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态 1正常 0删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_wn_world_time` (`world_id`, `status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='世界笔记';

-- 世界笔记评论（AI互评 / 用户评论）
CREATE TABLE IF NOT EXISTS `world_note_comments` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `note_id` BIGINT NOT NULL COMMENT '笔记ID',
  `author_role_id` BIGINT NOT NULL DEFAULT 0 COMMENT 'AI评论者角色ID',
  `author_user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '用户评论者ID',
  `author_name` VARCHAR(50) NOT NULL DEFAULT '',
  `author_avatar` VARCHAR(500) NOT NULL DEFAULT '',
  `content` VARCHAR(500) NOT NULL COMMENT '评论内容',
  `reply_to_id` BIGINT NOT NULL DEFAULT 0 COMMENT '回复的评论ID',
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_wnc_note` (`note_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='世界笔记评论';

-- 世界剧情碎片（世界打卡任务解锁）
CREATE TABLE IF NOT EXISTS `world_plots` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `world_id` BIGINT NOT NULL COMMENT '世界ID',
  `title` VARCHAR(100) NOT NULL COMMENT '剧情标题',
  `content` TEXT NOT NULL COMMENT '剧情碎片内容',
  `required_checkins` INT NOT NULL DEFAULT 3 COMMENT '解锁所需世界内累计打卡数',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '剧情顺序',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_wp_world` (`world_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='世界剧情碎片';

-- 用户在某世界已解锁的剧情
CREATE TABLE IF NOT EXISTS `world_plot_unlocks` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `world_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `plot_id` BIGINT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_world_user_plot` (`world_id`, `user_id`, `plot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='剧情解锁记录';

-- AI角色关系（同世界内互评产生关系变化）
CREATE TABLE IF NOT EXISTS `world_relations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `world_id` BIGINT NOT NULL,
  `role_a_id` BIGINT NOT NULL COMMENT '角色A(ai_roles.id)',
  `role_b_id` BIGINT NOT NULL COMMENT '角色B(ai_roles.id)',
  `relation_label` VARCHAR(50) NOT NULL DEFAULT '初识' COMMENT '关系标签 初识/好友/挚友/对手...',
  `score` INT NOT NULL DEFAULT 0 COMMENT '关系分值',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_world_role_pair` (`world_id`, `role_a_id`, `role_b_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI角色关系';
