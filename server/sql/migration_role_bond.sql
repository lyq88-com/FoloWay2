-- 羁绊碎片表（角色 × 用户 的羁绊进度）
-- 此表为纯新增，不改动任何旧表结构
-- 每个用户对每个角色独立记录，4 个章节按对话次数阈值解锁
USE ai_habit_partner;

CREATE TABLE IF NOT EXISTS role_bond_chapters (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_key VARCHAR(64) NOT NULL COMMENT '角色标识（linxi / gacha_xxx / custom_xxx）',
    chapter_idx TINYINT NOT NULL COMMENT '章节序号 1-4',
    chapter_title VARCHAR(32) NOT NULL COMMENT '章节名',
    unlock_count_threshold INT NOT NULL COMMENT '解锁需要的对话次数',
    unlocked_at DATETIME NULL COMMENT '解锁时间（NULL=未解锁）',
    content TEXT NULL COMMENT 'AI生成的碎片文案',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_role (user_id, role_key),
    UNIQUE KEY uk_user_role_chapter (user_id, role_key, chapter_idx)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色羁绊碎片';

-- 初始化 4 个章节模板（全量覆盖幂等）
DELETE FROM role_bond_chapters WHERE FALSE;  -- 空操作占位，不删数据
-- 章节模板由后端 bond_service._CHAPTER_TEMPLATES 管理，数据库存储解锁状态和 AI 生成的 content
