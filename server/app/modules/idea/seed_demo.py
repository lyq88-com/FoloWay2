# -*- coding: utf-8 -*-
"""
「小想法」测试种子数据（仅为本功能演示/自测用）
================================================

作用：库里往往只有你一个人，发布想法后「匹配不到任何人」。
本脚本创建 3 个演示用户 + 若干条不同主题的想法，让你发布后能立刻看到共鸣。

用法（在 server 目录下）：
    py -3.12 app/modules/idea/seed_demo.py

说明：
- 只向 users / idea 表插入演示数据，不修改任何既有表结构。
- 重复执行不会重复插入（按用户名幂等）。
- 演示用户永远无法登录（无密码/无微信），仅作为「其他用户」的想法的归属。
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.user import User  # noqa: E402
from app.modules.idea import models as _m  # noqa: F401,E402
from app.modules.idea.models import Idea, IdeaSetting  # noqa: E402


DEMO_USERS = [
    ("demo_xiaoyu", "小雨", "慢慢来，别急"),
    ("demo_amin", "阿敏", "深夜emo选手"),
    ("demo_lzh", "老周", "打工人，打工魂"),
]

# (归属演示用户名, 文本) —— 覆盖多个主题，便于命中
DEMO_IDEAS = [
    ("demo_xiaoyu", "一个人的周末，安静到能听见自己的心跳。"),
    ("demo_xiaoyu", "今天又加班到很晚，回家的路上有点想哭。"),
    ("demo_amin", "深夜总是特别容易emo，明明没什么事。"),
    ("demo_amin", "最近总是失眠，翻来覆去到天亮。"),
    ("demo_amin", "有点想念小时候夏天的味道。"),
    ("demo_lzh", "工作压力好大，喘不过气，好想请个长假去海边。"),
    ("demo_lzh", "成年人的崩溃都是静音的，今天也撑住了。"),
    ("demo_lzh", "突然觉得一个人也挺好的，安静又自由。"),
]


def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        now = datetime.now()
        uid_map = {}
        for username, nickname, sign in DEMO_USERS:
            u = db.query(User).filter(User.username == username).first()
            if not u:
                u = User(
                    username=username, nickname=nickname, signature=sign,
                    avatar="", phone=None, email=None,
                    password_hash="", wx_openid="", wx_unionid="",
                    gender=0, status=1,
                    register_time=now, last_login_time=now, last_login_ip="127.0.0.1",
                )
                db.add(u)
                db.flush()
                print(f"[seed] 新建演示用户：{nickname}({username}) id={u.id}")
            uid_map[username] = u.id
            # 确保接受共鸣匹配
            if not db.query(IdeaSetting).filter(IdeaSetting.user_id == u.id).first():
                db.add(IdeaSetting(user_id=u.id, accept_resonance=1))
        db.commit()

        created = 0
        for i, (username, content) in enumerate(DEMO_IDEAS):
            exists = db.query(Idea).filter(
                Idea.uid == uid_map[username], Idea.content == content
            ).first()
            if exists:
                continue
            db.add(Idea(
                uid=uid_map[username], content=content, image="",
                is_anonymous=0, is_deleted=0,
                create_time=now - timedelta(minutes=i * 7),  # 制造时间差
            ))
            created += 1
        db.commit()
        print(f"[seed] 新增 {created} 条演示想法（已存在的不重复）")
        print("[seed] 完成。现在用你的账号发布一条，去「心愿岛 → 小想法」看共鸣吧")
    finally:
        db.close()


if __name__ == "__main__":
    main()
