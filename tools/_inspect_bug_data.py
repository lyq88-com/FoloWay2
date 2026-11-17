# -*- coding: utf-8 -*-
"""BUG-001/002 修复前的数据现状勘察"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.core.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== ai_roles ===")
    for r in db.execute(text("SELECT * FROM ai_roles ORDER BY id")).mappings().all():
        print({k: (str(v)[:40]) for k, v in r.items()})

    print("\n=== ai_roles 列 ===")
    for r in db.execute(text("SHOW COLUMNS FROM ai_roles")).all():
        print(r)

    print("\n=== companion_records 近 5 条 ===")
    try:
        for r in db.execute(text("SELECT * FROM companion_records ORDER BY id DESC LIMIT 5")).mappings().all():
            print({k: (str(v)[:30]) for k, v in r.items()})
    except Exception as e:
        print("ERR", e)

    print("\n=== user(Flask) 列 ===")
    for r in db.execute(text("SHOW COLUMNS FROM user")).all():
        print(r)

    print("\n=== user(Flask) 行数 / 样本 ===")
    print(db.execute(text("SELECT COUNT(*) FROM user")).scalar())
    for r in db.execute(text("SELECT id, username, email FROM user ORDER BY id DESC LIMIT 8")).mappings().all():
        print(dict(r))

    print("\n=== users(FastAPI) 行数 / 样本 ===")
    print(db.execute(text("SELECT COUNT(*) FROM users")).scalar())
    for r in db.execute(text("SELECT id, username, email, nickname, phone FROM users ORDER BY id DESC LIMIT 8")).mappings().all():
        print(dict(r))

    print("\n=== 同名账号在两表的 id 对照（取 users 最近 8 条按 username 反查 user 表）===")
    for r in db.execute(text(
        "SELECT u.id AS users_id, u.username, f.id AS flask_id "
        "FROM users u LEFT JOIN user f ON f.username = u.username "
        "ORDER BY u.id DESC LIMIT 12"
    )).mappings().all():
        print(dict(r))
finally:
    db.close()
