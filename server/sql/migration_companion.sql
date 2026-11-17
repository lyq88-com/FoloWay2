-- ============================================================
-- 陪伴模式 (companion) 建表迁移
-- 数据库: ai_habit_partner (MySQL 8 / utf8mb4)
-- 对应 ORM 模型: server/app/models/companion.py
-- 用法: mysql -u root -p ai_habit_partner < migration_companion.sql
-- ============================================================

USE ai_habit_partner;

DROP TABLE IF EXISTS `companion_records`;

CREATE TABLE `companion_records` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id`       BIGINT       NOT NULL COMMENT '用户ID',
  `role_id`       BIGINT       NOT NULL DEFAULT 1 COMMENT '陪伴AI角色ID(关联ai_roles.id)',
  `scene_type`    VARCHAR(20)  NOT NULL DEFAULT 'custom' COMMENT '场景类型 sleep/study/work/sport/eat/custom',
  `scene_name`    VARCHAR(50)  NOT NULL DEFAULT '自定义' COMMENT '场景名称(自定义场景的用户输入)',
  `bg_img`        VARCHAR(500) NOT NULL DEFAULT '' COMMENT '背景图标识/URL',
  `bg_sound`      VARCHAR(50)  NOT NULL DEFAULT '静音' COMMENT '背景音 quiet/rain/fire/wave/forest/piano',
  `start_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time`      DATETIME     NULL COMMENT '结束时间',
  `duration_min`  INT          NOT NULL DEFAULT 0 COMMENT '陪伴时长(分钟)',
  `message_count` INT          NOT NULL DEFAULT 0 COMMENT '陪伴期间聊天消息数',
  `remark`        TEXT         NULL COMMENT '备注/陪伴小结',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态 1陪伴中 0已结束',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_status` (`user_id`, `status`),
  KEY `idx_user_start` (`user_id`, `start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='陪伴模式记录表';
