# -*- coding: utf-8 -*-
"""
从 Flask user 表迁移到 FastAPI users 表
- 同库 ai_habit_partner，不带 server_flask_db 前缀
- Flask 表名 user（单数），FastAPI 表名 users（复数）
- 密码字段直接拷贝到 password_hash（passlib bcrypt 兼容原生 bcrypt）
- INSERT 不带 id（防自增冲突）
- 用 NOT EXISTS 防重复
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.core.database import engine


SQL = """
INSERT INTO users (
    username, email, password_hash, nickname,
    avatar, wx_openid, wx_unionid, gender,
    status, register_time, last_login_time, last_login_ip
)
SELECT
    u.username,
    u.email,
    u.password,
    u.username,
    '',
    '',
    '',
    0,
    1,
    COALESCE(u.create_time, NOW()),
    NOW(),
    ''
FROM user u
WHERE u.username IS NOT NULL
  AND u.username NOT IN (SELECT username FROM users WHERE username IS NOT NULL)
  -- email 已被 FastAPI 用户占用(很可能是同一人换用户名注册)时跳过该行
  AND u.email NOT IN (SELECT email FROM users WHERE email IS NOT NULL AND email <> '')
"""


def main():
    """执行迁移"""
    with engine.begin() as conn:
        result = conn.exec_driver_sql(SQL)
        print(f"[migrate] 已迁移 {result.rowcount} 个 Flask 用户到 FastAPI users 表")


if __name__ == "__main__":
    main()
