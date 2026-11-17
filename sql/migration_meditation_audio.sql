-- 正念音频资源路径迁移
-- 问题：audio_resources.audio_url 指向 /static/audio/*.mp3，但该目录与文件从来不存在，
--       H5 打开正念页时全部 404，播放器 onError 降级为计时器空放（有进度条但没声音）。
-- 方案：音频改为由 FastAPI 的 /uploads 静态挂载提供（与头像资源同一套相对路径约定），
--       文件为 30 秒无缝循环的环境音床（生成器见 tools/gen_meditation_audio.py）。
--       文件落盘路径：server/uploads/audio/*.wav
-- 说明：这些是程序合成的占位音床，后续可直接替换为真人引导音频（换文件 + 改 mime 即可）。

UPDATE audio_resources SET audio_url = '/uploads/audio/breath_5min.wav'   WHERE audio_url = '/static/audio/breath_5min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/breath_10min.wav'  WHERE audio_url = '/static/audio/breath_10min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/breath_15min.wav'  WHERE audio_url = '/static/audio/breath_15min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/scan_5min.wav'     WHERE audio_url = '/static/audio/scan_5min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/scan_10min.wav'    WHERE audio_url = '/static/audio/scan_10min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/scan_20min.wav'    WHERE audio_url = '/static/audio/scan_20min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/med_5min.wav'      WHERE audio_url = '/static/audio/med_5min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/med_15min.wav'     WHERE audio_url = '/static/audio/med_15min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/med_30min.wav'     WHERE audio_url = '/static/audio/med_30min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/anxiety_5min.wav'  WHERE audio_url = '/static/audio/anxiety_5min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/anxiety_15min.wav' WHERE audio_url = '/static/audio/anxiety_15min.mp3';
UPDATE audio_resources SET audio_url = '/uploads/audio/anxiety_25min.wav' WHERE audio_url = '/static/audio/anxiety_25min.mp3';

-- 校验：应返回 12 行，且 0 行仍指向 /static/audio
-- SELECT audio_url FROM audio_resources;
-- SELECT COUNT(*) FROM audio_resources WHERE audio_url LIKE '/static/audio%';  -- 期望 0
