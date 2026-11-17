-- Phase 1.2: 扩展 users 表，新增 username/email 列，phone 改可空
-- 注意：register_time 字段已存在，不再 ADD；password_hash 等其他字段保留不动

ALTER TABLE users MODIFY phone VARCHAR(20) NULL;
ALTER TABLE users ADD COLUMN username VARCHAR(50) NULL;
ALTER TABLE users ADD COLUMN email VARCHAR(100) NULL;
ALTER TABLE users ADD UNIQUE KEY uk_username (username);
ALTER TABLE users ADD UNIQUE KEY uk_email (email);
