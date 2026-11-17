-- ============================================================
-- migration_user_deletion_backup.sql —— 安全合规批次
-- 用户数据备份表：注销前快照 / 导出留档
-- 对应模型: app/models/user.py -> UserDataBackup
-- ============================================================

CREATE TABLE IF NOT EXISTS user_data_backups (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     BIGINT       NOT NULL                COMMENT '用户ID',
    backup_type VARCHAR(20)  NOT NULL DEFAULT 'deactivate' COMMENT '备份类型 deactivate注销/export导出',
    data_json   TEXT         NOT NULL                COMMENT '用户数据JSON快照',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_id (user_id),
    KEY idx_backup_type (backup_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户数据备份（注销快照/导出留档）';

-- 验证：
-- SHOW CREATE TABLE user_data_backups;
