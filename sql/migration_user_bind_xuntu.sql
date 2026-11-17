-- ============================================================
-- 迁移：Flask 侧 user 表增加 xuntu_user_id（指向 FastAPI users.id）
-- 关联缺陷：BUG-002（双用户表 id 不共享，跨服务注册/登录导致数据串号或查不到）
-- 修复后：Flask 注册/登录时同步 users 表，并以 users.id 作为 JWT 的 sub，
--         两套用户体系通过本列建立唯一映射。
-- 执行方式：
--   cd liyeqing\server && python ..\tools\run_sql.py ..\sql\migration_user_bind_xuntu.sql
-- ============================================================

ALTER TABLE `user`
  ADD COLUMN xuntu_user_id BIGINT NULL DEFAULT NULL COMMENT '对应 users(FastAPI).id' AFTER email;

ALTER TABLE `user`
  ADD INDEX idx_user_xuntu_user_id (xuntu_user_id);
