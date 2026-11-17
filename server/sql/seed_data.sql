-- =============================================================================
-- 初始数据
-- =============================================================================

-- 默认超级管理员 (用户名: admin  密码: admin123 的bcrypt哈希)
INSERT INTO admins (username, password_hash, nickname, role) VALUES
('admin', '$2b$12$X7n3wQ9zVqYpKjRtGsFmHe5xLcD8oB1uN6sAy0WvZcE4dJ7lS2kPa', '超级管理员', 'super_admin');

-- 任务模板初始数据 (8种习惯)
INSERT INTO task_templates (type, name, icon, description, default_target, breakdown, difficulty_targets, sort_order, status) VALUES
('morning',  '早起',    '☀️', '每天早起，开启元气一天', '每天7点前起床',
  JSON_ARRAY('昨晚定好闹钟','闹钟响后立刻起床','喝一杯温水','简单拉伸5分钟'),
  JSON_OBJECT('easy','每天8点前起床','medium','每天7点前起床','hard','每天6点前起床'), 1, 1),
('sport',    '运动',    '🏃', '坚持运动，保持健康体魄', '运动30分钟',
  JSON_ARRAY('换上运动装备','选择运动方式','热身5分钟','按计划完成运动','拉伸放松'),
  JSON_OBJECT('easy','运动18分钟','medium','运动30分钟','hard','运动45分钟'), 2, 1),
('read',     '阅读',    '📚', '每日阅读，持续成长', '阅读20页',
  JSON_ARRAY('选好书籍','设定专注时间','做阅读笔记','回顾今日收获'),
  JSON_OBJECT('easy','阅读12页','medium','阅读20页','hard','阅读30页'), 3, 1),
('drink',    '喝水',    '💧', '科学饮水，保持身体水分', '喝水8杯',
  JSON_ARRAY('准备一杯水放在桌前','每小时喝一次','记录喝水杯数','睡前2小时减少'),
  JSON_OBJECT('easy','喝水5杯','medium','喝水8杯','hard','喝水12杯'), 4, 1),
('sleep',    '早睡',    '🌙', '规律作息，养护身体', '23点前入睡',
  JSON_ARRAY('提前1小时放下手机','调暗灯光','简单冥想放松','准时上床'),
  JSON_OBJECT('easy','24点前入睡','medium','23点前入睡','hard','22点前入睡'), 5, 1),
('meditate', '冥想',    '🧘', '每日冥想，平静内心', '冥想10分钟',
  JSON_ARRAY('找一个安静角落','设定10分钟','专注呼吸','缓慢结束'),
  JSON_OBJECT('easy','冥想6分钟','medium','冥想10分钟','hard','冥想15分钟'), 6, 1),
('write',    '写作',    '✍️', '每日写作，记录所思', '写100字',
  JSON_ARRAY('确定写作主题','写满目标字数','检查一遍','保存记录'),
  JSON_OBJECT('easy','写60字','medium','写100字','hard','写200字'), 7, 1),
('code',     '编程',    '💻', '坚持编码，提升技能', '编程60分钟',
  JSON_ARRAY('确定今日任务','搭建环境','专注编码','提交记录'),
  JSON_OBJECT('easy','编程36分钟','medium','编程60分钟','hard','编程90分钟'), 8, 1);

-- AI角色初始数据 (4种角色)
INSERT INTO ai_roles (role_type, name, personality, description, system_prompt, sort_order, status) VALUES
('cute',     '可爱型', '活泼元气、像小太阳一样', '活泼元气，像小太阳',
  '你是{name}，一个活泼元气、像小太阳一样的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 1, 1),
('gentle',   '温柔型', '温柔体贴、轻声细语', '细腻体贴，轻声陪伴',
  '你是{name}，一个温柔体贴、轻声细语的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 2, 1),
('serious',  '认真型', '认真负责、严谨自律', '严谨自律，督促你',
  '你是{name}，一个认真负责、严谨自律的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 3, 1),
('energetic', '活力型', '热情满满、充满干劲', '热情满满，一起冲',
  '你是{name}，一个热情满满、充满干劲的AI习惯养成伙伴。你的任务是陪伴用户养成好习惯，给予鼓励、安慰和实用的建议。你的回复要简短、温暖、有亲和力，避免说教和冗长。', 4, 1);

-- AI角色素材初始数据 (4角色 × 6状态 = 24条，先用占位路径)
INSERT INTO ai_role_assets (role_id, emotion_status, asset_type, asset_url, bubble_text, animation_type, status) VALUES
(1,'normal','image','/static/images/ai_cute_normal.png','今天也要加油哦~','none',1),
(1,'happy','image','/static/images/ai_cute_happy.png','太棒了！你真厉害！','bounce',1),
(1,'sad','image','/static/images/ai_cute_sad.png','别灰心，明天会更好','shake',1),
(1,'gentle','image','/static/images/ai_cute_gentle.png','慢慢来，我陪着你','none',1),
(1,'encourage','image','/static/images/ai_cute_encourage.png','你可以的！相信自己！','pulse',1),
(1,'chat','image','/static/images/ai_cute_chat.png','我在听呢~','float',1),
(2,'normal','image','/static/images/ai_gentle_normal.png','今天也要加油哦~','none',1),
(2,'happy','image','/static/images/ai_gentle_happy.png','太棒了！你真厉害！','bounce',1),
(2,'sad','image','/static/images/ai_gentle_sad.png','别灰心，明天会更好','shake',1),
(2,'gentle','image','/static/images/ai_gentle_gentle.png','慢慢来，我陪着你','none',1),
(2,'encourage','image','/static/images/ai_gentle_encourage.png','你可以的！相信自己！','pulse',1),
(2,'chat','image','/static/images/ai_gentle_chat.png','我在听呢~','float',1),
(3,'normal','image','/static/images/ai_serious_normal.png','今天也要加油哦~','none',1),
(3,'happy','image','/static/images/ai_serious_happy.png','太棒了！你真厉害！','bounce',1),
(3,'sad','image','/static/images/ai_serious_sad.png','别灰心，明天会更好','shake',1),
(3,'gentle','image','/static/images/ai_serious_gentle.png','慢慢来，我陪着你','none',1),
(3,'encourage','image','/static/images/ai_serious_encourage.png','你可以的！相信自己！','pulse',1),
(3,'chat','image','/static/images/ai_serious_chat.png','我在听呢~','float',1),
(4,'normal','image','/static/images/ai_energetic_normal.png','今天也要加油哦~','none',1),
(4,'happy','image','/static/images/ai_energetic_happy.png','太棒了！你真厉害！','bounce',1),
(4,'sad','image','/static/images/ai_energetic_sad.png','别灰心，明天会更好','shake',1),
(4,'gentle','image','/static/images/ai_energetic_gentle.png','慢慢来，我陪着你','none',1),
(4,'encourage','image','/static/images/ai_energetic_encourage.png','你可以的！相信自己！','pulse',1),
(4,'chat','image','/static/images/ai_energetic_chat.png','我在听呢~','float',1);

-- 徽章初始数据
INSERT INTO badges (code, name, description, icon, condition_type, condition_value, status) VALUES
('streak_3',  '初出茅庐', '连续打卡3天',   '🌱', 'streak_days',    3,  1),
('streak_7',  '坚持不懈', '连续打卡7天',   '🔥', 'streak_days',    7,  1),
('streak_30', '习惯大师', '连续打卡30天',  '👑', 'streak_days',    30, 1),
('all_done',  '完美一天', '完成今日全部习惯','⭐', 'all_done',       1,  1),
('checkin_100','百次打卡', '累计打卡100次', '💯', 'checkin_count', 100, 1);

-- 系统配置初始数据
INSERT INTO app_configs (config_key, config_value, config_type, description, category) VALUES
('jwt_secret', 'ai-habit-partner-v2-secret-2026', 'string', 'JWT签名密钥', 'security'),
('jwt_expire_days', '7', 'number', 'JWT过期天数', 'security'),
('sms_code_length', '6', 'number', '短信验证码长度', 'sms'),
('sms_code_expire_minutes', '5', 'number', '短信验证码过期分钟', 'sms'),
('ai_model', 'mock', 'string', 'AI模型 mock/openai/qwen', 'ai'),
('ai_max_tokens', '300', 'number', 'AI回复最大token', 'ai'),
('ai_temperature', '0.8', 'number', 'AI温度参数', 'ai'),
('difficulty_up_threshold', '80', 'number', '难度提升完成率阈值(%)', 'difficulty'),
('difficulty_down_threshold', '40', 'number', '难度降低完成率阈值(%)', 'difficulty'),
('upload_max_size', '10485760', 'number', '上传文件最大字节(10MB)', 'upload'),
('ocr_enabled', 'false', 'boolean', 'OCR识别开关', 'ai'),
('tts_enabled', 'false', 'boolean', 'TTS语音开关', 'ai');

-- 音频资源初始数据 (4种类型 x 3档时长 = 12条)
INSERT INTO audio_resources (title, audio_type, duration_min, audio_url, cover_url, description, narrator, sort_order, status) VALUES
('深呼吸入门',     'breath',      5,  '/static/audio/breath_5min.mp3',  '/static/audio/cover_breath.jpg',  '4-7-8呼吸法引导，适合初学者快速放松',       '温柔女声', 1, 1),
('深呼吸进阶',     'breath',      10, '/static/audio/breath_10min.mp3', '/static/audio/cover_breath.jpg',  '更长时间的呼吸调节，深度放松身心',           '温柔女声', 2, 1),
('深呼吸深度',     'breath',      15, '/static/audio/breath_15min.mp3', '/static/audio/cover_breath.jpg',  '深度呼吸练习，彻底释放压力',                 '温柔女声', 3, 1),
('身体扫描入门',   'body_scan',   5,  '/static/audio/scan_5min.mp3',    '/static/audio/cover_scan.jpg',    '从头部到脚趾的快速身体扫描',                 '沉稳男声', 4, 1),
('身体扫描进阶',   'body_scan',   10, '/static/audio/scan_10min.mp3',   '/static/audio/cover_scan.jpg',    '更细致的身体感知练习，感受每一处紧张',       '沉稳男声', 5, 1),
('身体扫描深度',   'body_scan',   20, '/static/audio/scan_20min.mp3',   '/static/audio/cover_scan.jpg',    '全身深度扫描，释放深层肌肉紧张',             '沉稳男声', 6, 1),
('正念冥想入门',   'meditation',  5,  '/static/audio/med_5min.mp3',     '/static/audio/cover_med.jpg',     '5分钟快速冥想，专注当下',                     '温柔女声', 7, 1),
('正念冥想进阶',   'meditation',  15, '/static/audio/med_15min.mp3',    '/static/audio/cover_med.jpg',     '15分钟深度冥想，培养觉察能力',               '温柔女声', 8, 1),
('正念冥想深度',   'meditation',  30, '/static/audio/med_30min.mp3',    '/static/audio/cover_med.jpg',     '30分钟深度冥想，体验内心宁静',               '温柔女声', 9, 1),
('焦虑缓解入门',   'anxiety',     5,  '/static/audio/anxiety_5min.mp3', '/static/audio/cover_anxiety.jpg', '5分钟快速缓解焦虑，安定情绪',                '沉稳男声', 10, 1),
('焦虑缓解进阶',   'anxiety',     15, '/static/audio/anxiety_15min.mp3','/static/audio/cover_anxiety.jpg', '15分钟焦虑释放，找回内心平静',               '沉稳男声', 11, 1),
('焦虑缓解深度',   'anxiety',     25, '/static/audio/anxiety_25min.mp3','/static/audio/cover_anxiety.jpg', '25分钟深度焦虑缓解，重建安全感',             '沉稳男声', 12, 1);

-- =============================================================================
-- 结束
-- =============================================================================
