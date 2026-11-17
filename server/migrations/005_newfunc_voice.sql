-- ============================================================
-- 005_newfunc_voice.sql —— 【newfunc 增量】多语种/方言语音包模块建表 SQL
-- 独立新增 5 张表，不修改任何旧表；无外键，bot_id / uid 仅逻辑关联
-- MySQL 5.7+ / 8.0，utf8mb4
-- ============================================================

-- 1. 语音包（语种/方言维度，如 ko-kr 韩语、zh-hk 粤语、zh-liaoning 东北话、zh-shaanxi 陕西话）
CREATE TABLE IF NOT EXISTS `tts_voice_pack` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `pack_code` VARCHAR(32) NOT NULL COMMENT '语音包编码 ko-kr/ja-jp/zh-hk/zh-liaoning/zh-shaanxi/zh-default',
  `name` VARCHAR(50) NOT NULL COMMENT '显示名（韩语语音包/日语语音包…）',
  `lang_code` VARCHAR(16) NOT NULL COMMENT 'BCP-47 语种 ko/ja/yue/zh',
  `region` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '地区 KR/JP/HK/CN-Sichuan',
  `sample_text` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '试听示例文本',
  `provider` VARCHAR(20) NOT NULL DEFAULT 'edge' COMMENT 'TTS 供应商 edge/azure/local',
  `is_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '1启用 0停用',
  `sort` INT NOT NULL DEFAULT 0 COMMENT '排序（越小越靠前）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pack_code` (`pack_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='多语种/方言语音包';

-- 2. 语音包音色（一个语种包下多个音色，男/女声）
CREATE TABLE IF NOT EXISTS `tts_voice_timbre` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `pack_code` VARCHAR(32) NOT NULL COMMENT '所属语音包编码',
  `voice_id` VARCHAR(64) NOT NULL COMMENT '音色ID（供应商音色标识）',
  `name` VARCHAR(50) NOT NULL COMMENT '音色显示名',
  `gender` VARCHAR(10) NOT NULL DEFAULT 'female' COMMENT 'male/female',
  `is_default` TINYINT NOT NULL DEFAULT 0 COMMENT '该包默认音色 1是 0否',
  `is_enabled` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_voice_id` (`voice_id`),
  KEY `idx_pack_code` (`pack_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语音包音色明细';

-- 3. TTS 音频缓存（key=md5(voice_id|text)，命中直接回音频，减少重复请求）
CREATE TABLE IF NOT EXISTS `tts_cache` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `cache_key` VARCHAR(40) NOT NULL COMMENT 'md5(voice_id|text)',
  `voice_id` VARCHAR(64) NOT NULL,
  `text` VARCHAR(2000) NOT NULL COMMENT '合成原文',
  `audio_path` VARCHAR(300) NOT NULL COMMENT '音频文件相对路径',
  `audio_format` VARCHAR(10) NOT NULL DEFAULT 'mp3',
  `size_bytes` INT NOT NULL DEFAULT 0,
  `hits` INT NOT NULL DEFAULT 0 COMMENT '命中次数',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_hit_at` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cache_key` (`cache_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS 音频缓存';

-- 4. 用户语音设置（每用户一行：默认音色，回退链终点之一）
CREATE TABLE IF NOT EXISTS `tts_user_setting` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `uid` BIGINT NOT NULL COMMENT '用户ID',
  `voice_id` VARCHAR(64) NOT NULL DEFAULT 'zh-CN-XiaoxiaoNeural' COMMENT '默认音色（原有普通话音色）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uid` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户 TTS 默认语音设置';

-- 5. AI 伙伴专属语音绑定（不同人设伙伴搭配不同语种/方言音色）
CREATE TABLE IF NOT EXISTS `tts_bot_voice` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `uid` BIGINT NOT NULL,
  `bot_id` BIGINT NOT NULL COMMENT 'AI 伙伴ID（逻辑关联 ai_bot_info.id，无外键）',
  `voice_id` VARCHAR(64) NOT NULL COMMENT '绑定音色ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bot_id` (`bot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 伙伴语音包绑定';
