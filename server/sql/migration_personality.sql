-- ============================================================
-- 性格测评上云: user_personality_results
-- 适用: 已存在的库(新环境用 init_db.py 的 create_all 即可, 此脚本幂等)
-- 执行: mysql -uroot -p ai_habit_partner < sql/migration_personality.sql
-- 说明: 本脚本 CREATE TABLE IF NOT EXISTS, 重复执行安全
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_personality_results` (
  `id`                   BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id`              BIGINT       NOT NULL                COMMENT '用户ID(users.id)',
  `personality`          VARCHAR(20)  NOT NULL DEFAULT ''     COMMENT '性格特质 anxious/perfect/procrastinator/buddha',
  `emotional_resilience` VARCHAR(20)  NOT NULL DEFAULT ''     COMMENT '情绪韧性 low/medium/high',
  `procrastination`      VARCHAR(20)  NOT NULL DEFAULT ''     COMMENT '拖延程度 low/medium/high',
  `companion_style`      VARCHAR(20)  NOT NULL DEFAULT ''     COMMENT '陪伴偏好 warm/smart/energetic/creative',
  `raw_scores`           TEXT                                 COMMENT '四维原始分 JSON',
  `answers`              TEXT                                 COMMENT '8题作答明细 JSON(可为空)',
  `quiz_version`         VARCHAR(20)  NOT NULL DEFAULT 'v1'   COMMENT '题库版本',
  `source`               VARCHAR(20)  NOT NULL DEFAULT 'app'  COMMENT '来源 app/admin/import/migrate',
  `is_active`            TINYINT      NOT NULL DEFAULT 1      COMMENT '是否当前生效 1生效 0历史',
  `created_at`           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_upr_user_active`  (`user_id`, `is_active`),
  KEY `idx_upr_user_created` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户性格测评结果(云端, is_active=1 为当前生效)';


-- ------------------------------------------------------------
-- 单生效位兜底: 把同一用户被重复置为生效的旧记录收敛为历史
-- (正常由应用层保证; 此语句用于修复历史脏数据, 可按需执行)
-- ------------------------------------------------------------
-- UPDATE `user_personality_results` r
--   JOIN (
--     SELECT user_id, MAX(id) AS keep_id
--     FROM `user_personality_results`
--     WHERE is_active = 1
--     GROUP BY user_id
--   ) k ON r.user_id = k.user_id AND r.is_active = 1
-- SET r.is_active = 0
-- WHERE r.id <> k.keep_id;
