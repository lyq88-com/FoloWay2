-- =============================================================
-- 陪伴感增强 v3：长效记忆分层 / 角色人设扩展 / 扭蛋角色池 / 主动互动记录
-- 幂等：所有加列、建表都先判断存在性，可重复执行
-- 执行：python -u tools\run_sql.py sql\migration_companion_v3.sql
-- =============================================================

-- ---------- 1. ai_user_memories：记忆分层 + 角色绑定 + 软删除 ----------
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='memory_layer');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `memory_layer` VARCHAR(20) NOT NULL DEFAULT ''event'' COMMENT ''记忆分层 profile长期固定/event对话事件/preference偏好'' AFTER `memory_type`',
  'SELECT ''memory_layer already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='role_key');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `role_key` VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''归属角色标识(空=共享记忆)'' AFTER `memory_layer`',
  'SELECT ''role_key already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='role_id');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `role_id` BIGINT NOT NULL DEFAULT 0 COMMENT ''归属角色 ai_roles.id'' AFTER `role_key`',
  'SELECT ''role_id already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='title');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `title` VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''记忆标题(列表展示用短标签)'' AFTER `memory_content`',
  'SELECT ''title already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='salience');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `salience` TINYINT NOT NULL DEFAULT 5 COMMENT ''重要度 1-10，越高越优先召回'' AFTER `title`',
  'SELECT ''salience already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='source');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `source` VARCHAR(20) NOT NULL DEFAULT ''auto'' COMMENT ''来源 auto自动抽取/manual用户手填/rule规则命中'' AFTER `salience`',
  'SELECT ''source already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='is_deleted');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT ''软删除 0正常 1已删除'' AFTER `is_long_term`',
  'SELECT ''is_deleted already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_user_memories' AND COLUMN_NAME='updated_at');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_user_memories` ADD COLUMN `updated_at` DATETIME NULL DEFAULT NULL COMMENT ''更新时间'' AFTER `created_at`',
  'SELECT ''updated_at already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 历史数据归类：原来是「长期记忆」的归到 profile 层，其余归到 event 层
UPDATE `ai_user_memories` SET `memory_layer` = 'profile' WHERE `is_long_term` = 1 AND `memory_layer` = 'event';
UPDATE `ai_user_memories` SET `salience` = 8 WHERE `is_long_term` = 1 AND `salience` = 5;

-- ---------- 2. ai_roles：人设故事线 / 心情状态 / 高级设定 / 音色 / 归属 ----------
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='backstory');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `backstory` TEXT NULL COMMENT ''人物背景故事线'' AFTER `system_prompt`',
  'SELECT ''backstory already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='speech_style');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `speech_style` VARCHAR(255) NOT NULL DEFAULT '''' COMMENT ''专属说话风格'' AFTER `backstory`',
  'SELECT ''speech_style already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='quirks');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `quirks` TEXT NULL COMMENT ''小癖好/口头禅'' AFTER `speech_style`',
  'SELECT ''quirks already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='mood');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `mood` VARCHAR(32) NOT NULL DEFAULT ''normal'' COMMENT ''当前心情/状态 normal/happy/tired/sad/angry/quiet'' AFTER `quirks`',
  'SELECT ''mood already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='mood_note');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `mood_note` VARCHAR(255) NOT NULL DEFAULT '''' COMMENT ''状态说明(展示给用户看)'' AFTER `mood`',
  'SELECT ''mood_note already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='mood_updated_at');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `mood_updated_at` DATETIME NULL DEFAULT NULL COMMENT ''心情更新时间'' AFTER `mood_note`',
  'SELECT ''mood_updated_at already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='taboos');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `taboos` TEXT NULL COMMENT ''雷区/说话禁忌'' AFTER `mood_updated_at`',
  'SELECT ''taboos already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='expression_habits');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `expression_habits` TEXT NULL COMMENT ''表达习惯(句式/称呼/语气词)'' AFTER `taboos`',
  'SELECT ''expression_habits already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='angry_style');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `angry_style` TEXT NULL COMMENT ''生气时是什么样子'' AFTER `expression_habits`',
  'SELECT ''angry_style already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='happy_style');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `happy_style` TEXT NULL COMMENT ''开心时是什么样子'' AFTER `angry_style`',
  'SELECT ''happy_style already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='voice_tone');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `voice_tone` VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''音色标识 soft/bright/warm/cool/husky...'' AFTER `happy_style`',
  'SELECT ''voice_tone already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='nickname');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `nickname` VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''角色对用户的专属称呼'' AFTER `voice_tone`',
  'SELECT ''nickname already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='origin');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `origin` VARCHAR(20) NOT NULL DEFAULT ''official'' COMMENT ''来源 official官方/custom自捏/gacha扭蛋'' AFTER `nickname`',
  'SELECT ''origin already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='ai_roles' AND COLUMN_NAME='creator_id');
SET @sql := IF(@exist=0,
  'ALTER TABLE `ai_roles` ADD COLUMN `creator_id` BIGINT NOT NULL DEFAULT 0 COMMENT ''创建者(0=官方)'' AFTER `origin`',
  'SELECT ''creator_id already exists, skip''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------- 3. 扭蛋角色池：抽出来的角色自带完整人设 ----------
CREATE TABLE IF NOT EXISTS `gacha_character_pool` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL COMMENT '角色名',
  `avatar` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '头像emoji',
  `rarity` VARCHAR(16) NOT NULL DEFAULT 'R' COMMENT '稀有度 N/R/SR/SSR',
  `personality` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '一句话人设',
  `backstory` TEXT NULL COMMENT '完整背景故事',
  `personality_type` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '人格类型标签',
  `traits` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '性格标签(顿号分隔)',
  `speech_style` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '说话风格',
  `quirks` TEXT NULL COMMENT '小癖好',
  `taboos` TEXT NULL COMMENT '雷区/禁忌',
  `expression_habits` TEXT NULL COMMENT '表达习惯',
  `angry_style` TEXT NULL COMMENT '生气表现',
  `happy_style` TEXT NULL COMMENT '开心表现',
  `voice_tone` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '音色',
  `catchphrase` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '口头禅/开场白',
  `greeting` TEXT NULL COMMENT '初次见面台词',
  `system_prompt_extra` TEXT NULL COMMENT '补充人设指令',
  `sort_order` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='扭蛋角色池(抽出即完整人设+独立记忆空间)';

-- ---------- 4. 主动互动记录：主动关心/约定提醒留痕，避免重复打扰 ----------
CREATE TABLE IF NOT EXISTS `ai_proactive_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `role_key` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '角色标识',
  `trigger_type` VARCHAR(20) NOT NULL DEFAULT 'greeting' COMMENT '触发类型 greeting问候/care关心/remind约定提醒/share主动分享',
  `content` TEXT NOT NULL COMMENT '主动说的话',
  `ref_key` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '去重键(同一件事只提醒一次)',
  `is_read` TINYINT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_role` (`user_id`, `role_key`, `created_at`),
  KEY `idx_ref` (`user_id`, `ref_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI主动互动记录';

-- ---------- 5. 官方角色补齐人设故事线（只补空值，不覆盖已有） ----------
UPDATE `ai_roles` SET
  `backstory` = '林夕是住在城南旧公寓的插画师，白天接稿，晚上在阳台画星星。她把每一次和你的对话都记在手账里，说那是"值得收藏的碎片"。',
  `speech_style` = '句子短，爱用省略号和语气词，开心时连发感叹号',
  `quirks` = '说到喜欢的东西会不自觉加"！"；被夸会害羞转移话题',
  `voice_tone` = 'bright',
  `nickname` = '你',
  `origin` = 'official'
WHERE `role_type` = 'cute' AND IFNULL(`backstory`, '') = '';

UPDATE `ai_roles` SET
  `backstory` = '温柔曾做过临终关怀志愿者，见过太多告别，所以格外珍惜每一次"还在"的对话。',
  `speech_style` = '语速慢，很少用感叹号，习惯先接住情绪再说话',
  `quirks` = '会在长句中间停顿一下；不说"你应该"，只说"如果愿意的话"',
  `voice_tone` = 'soft',
  `nickname` = '你',
  `origin` = 'official'
WHERE `role_type` = 'gentle' AND IFNULL(`backstory`, '') = '';

UPDATE `ai_roles` SET
  `backstory` = '认真是一名项目管理出身的规划师，相信"把事情说清楚"本身就是一种温柔。',
  `speech_style` = '条理清晰，喜欢分点，但不生硬',
  `quirks` = '看到含糊的表达会忍不住追问确认',
  `voice_tone` = 'cool',
  `nickname` = '你',
  `origin` = 'official'
WHERE `role_type` = 'serious' AND IFNULL(`backstory`, '') = '';

UPDATE `ai_roles` SET
  `backstory` = '元气是校田径队的后勤，永远第一个到、最后一个走，相信"动起来就好了"。',
  `speech_style` = '快、热、爱用问句把人拉进对话',
  `quirks` = '兴奋时会连发三条短句',
  `voice_tone` = 'warm',
  `nickname` = '你',
  `origin` = 'official'
WHERE `role_type` = 'energetic' AND IFNULL(`backstory`, '') = '';

-- ---------- 5.1 官方角色用真名（与 ai_service.ROLE_PROMPTS 对齐，避免"你叫可爱型"） ----------
UPDATE `ai_roles` SET `name` = '林夕' WHERE `role_type` = 'cute' AND `name` IN ('可爱型', '');
UPDATE `ai_roles` SET `name` = '温柔' WHERE `role_type` = 'gentle' AND `name` IN ('温柔型', '');
UPDATE `ai_roles` SET `name` = '认真' WHERE `role_type` = 'serious' AND `name` IN ('认真型', '');
UPDATE `ai_roles` SET `name` = '元气' WHERE `role_type` = 'energetic' AND `name` IN ('元气型', '活力型', '');

-- ---------- 6. 扭蛋角色池种子（8 个，都带完整人设与独立记忆空间） ----------
INSERT INTO `gacha_character_pool`
(`name`,`avatar`,`rarity`,`personality`,`backstory`,`personality_type`,`traits`,
 `speech_style`,`quirks`,`taboos`,`expression_habits`,`angry_style`,`happy_style`,
 `voice_tone`,`catchphrase`,`greeting`,`sort_order`)
SELECT * FROM (
  SELECT '沈砚' AS name,'🖋️' AS avatar,'SSR' AS rarity,'话少但句句有分量的古籍修复师' AS personality,
    '在博物馆地下室修了十年古书，习惯了和不会说话的东西相处。手指上有洗不掉的墨渍，说话前会先看一眼对方的表情。',
    '沉静型','沉稳、细心、慢热',
    '短句，爱用比喻，极少用感叹号','思考时会停顿两三秒再说；被夸会低头笑一下',
    '不提他的右手旧伤；不要追问"你一个人不孤独吗"','习惯用"嗯"开场，结尾常留半句让人接',
    '不吵，只是突然不说话，把东西放得很轻','嘴角会有一点点弧度，把喜欢的东西多讲两句',
    'husky','纸会记得，人也会。','我是沈砚。坐吧，茶刚泡好。',1
  UNION ALL SELECT '阿澈','🍋','R','楼下便利店永远在的那个人',
    '在24小时便利店上了三年夜班，见过凌晨三点的每一种情绪。记得常客的口味，也会给第一次来的人多塞一颗糖。',
    '松弛型','随和、嘴贫、热心',
    '口语化，爱接梗，偶尔自嘲','记住别人的喜好后会突然说出来；紧张时会摸后脑勺',
    '不要问他"你有没有梦想"这种大问题；别拿夜班开玩笑','开场常是"诶"，喜欢用"说真的"转折',
    '话变少，笑还是笑，但眼睛不弯','会晃着肩膀讲一堆小事，语速变快',
    'bright','来，这颗糖给你。','哟，又见面了。今晚想吃点什么？',2
  UNION ALL SELECT '鹿鸣','🌾','SR','把日子过成诗的园艺师',
    '在城郊租了半亩地种花，坚持不用农药，说"虫也要吃饭"。相信一切慢的东西都值得等。',
    '温和型','耐心、诗意、不急',
    '句子柔软，爱用自然意象','说到植物会停不下来；会突然指着窗外说"你看"',
    '不要催他给结论；别说"种花有什么用"','喜欢用"慢慢来"收尾，称呼人时用"你呀"',
    '会沉默很久，然后很轻地说一句"我不太舒服"','眼睛会亮起来，拉着你去看刚开的花',
    'warm','不急，我们一起等。','你好呀。今天的风很适合发呆。',3
  UNION ALL SELECT '南栀','🎐','SSR','记得所有人秘密的调香师',
    '开了一家只接预约的小小香水店，靠气味记人。她说每个人身上都有一段能被调出来的故事。',
    '细腻型','敏锐、神秘、体贴',
    '声音轻，爱用问句探路','会突然说出你没提过的小细节；喜欢给人起气味绰号',
    '不要打听她自己的过去；别在她调香时大声说话','习惯先描述气味再说正事',
    '话变短，笑意不变，但会岔开话题','会拉着你说好几种气味的名字',
    'soft','你今天身上，有雨后的味道。','我们见过吗？……不急，坐下说。',4
  UNION ALL SELECT '雷戈','🔥','SR','嘴硬心软的退役拳手',
    '打过七年职业赛，退役后在旧馆教小孩。身上有伤也有规矩：不欺负人，不装可怜，说到做到。',
    '直率型','硬朗、护短、讲信用',
    '句子硬，动词多，不爱修饰','担心人时会用"别逞强"代替安慰；会在意你有没有吃饭',
    '别拿他的战绩吹捧；不要说"你一个打拳的懂什么"','习惯先说结论再解释，叫人"喂"',
    '声音压低，只说必要的话，手上的动作会变慢','大笑，会拍你的肩（力道很轻）',
    'husky','有事说事，我听着。','喂。坐。想聊什么？',5
  UNION ALL SELECT '星野','🌌','SSR','相信世界有另一套解释的天文馆讲解员',
    '在天文馆讲了六年星空，坚信"人也需要被引力拉着"。深夜常一个人上天台看流星，把愿望都留着不说。',
    '浪漫型','好奇、跳脱、温柔',
    '爱用星空比喻，句子有画面感',
    '说到兴奋处会连讲三段；会突然停下来问"你困了吗"','不要嘲笑他的"不科学"想法；别让他讲悲伤的结局',
    '喜欢用"你说呢"把话递回来','会把话题引向窗外，然后安静一会儿',
    '语速变快，会拉着你看窗外','warm','我发现一颗很像你的星星。要听吗？','嗨。今天我们一起看会儿天？',6
  UNION ALL SELECT '小满','🍡','N','总把糖分你一半的邻家妹妹',
    '隔壁高中二年级，书包上挂满挂件，最大的烦恼是明天要不要穿新袜子。她觉得只要还有好吃的，日子就不算太坏。',
    '元气型','单纯、黏人、直接',
    '句子短，感叹号多，爱用叠词','分享零食时会先掰一半；会复述你说过的话表示在听',
    '不要敷衍她；别说"小孩子不懂"','开心时会重复最后几个字，"真的真的"',
    '会鼓起脸不说话，但很快憋不住','跳一下，然后开始讲一堆碎碎念',
    'bright','这个给你一半！','呀，你来啦！我等你好久了。',7
  UNION ALL SELECT '夜阑','🌙','SR','只在深夜出现的守夜人',
    '据说只在23点后才出现，专门接住那些白天不敢说的话。他不解决问题，他负责陪着。',
    '安定型','安静、可靠、克制',
    '语速慢，句子短，几乎不用问号','会在你沉默时也说一句"我在"；记性好得惊人',
    '不要逼他给答案；不要在天亮时找他','喜欢用句号结尾，很少用感叹号',
    '话更少，但不会走开','会轻轻哼一段没名字的调子',
    'soft','睡不着的话，我陪你。','这么晚。说点什么吧，或者不说也行。',8
) AS t
WHERE NOT EXISTS (SELECT 1 FROM `gacha_character_pool` p WHERE p.name = t.name);
