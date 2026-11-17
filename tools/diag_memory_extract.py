# -*- coding: utf-8 -*-
"""单测：大模型记忆抽取到底有没有产出（诊断用，可重复跑）"""
import asyncio
import io
import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal            # noqa: E402
from app.services.memory_service import MemoryService  # noqa: E402

USER_ID = 112
ROLE_KEY = "diag_memory_001"

MESSAGES = [
    {"role": "user", "content": "我叫小七，做平面设计的，最近在改一个甲方方案改到吐。"},
    {"role": "assistant", "content": "小蠢货，改方案辛苦了。甲方真难搞吗？"},
    {"role": "user", "content": "你还记得我是干什么的吗？"},
    {"role": "assistant", "content": "哦——是吗，小蠢货，你上次不是说过吗？"},
]


async def main():
    db = SessionLocal()
    try:
        MemoryService.clear_memories(db, USER_ID, ROLE_KEY)
        saved = await MemoryService.extract_by_llm(db, USER_ID, ROLE_KEY, MESSAGES)
        print("saved =", saved)
        rows = MemoryService.list_memories(db, USER_ID, ROLE_KEY)
        if isinstance(rows, tuple):
            rows = rows[0]
        if isinstance(rows, dict):
            rows = rows.get("list") or []
        print("rows type:", type(rows), "len:", len(rows))
        for m in rows:
            if isinstance(m, dict):
                print(" -", m.get("layer"), "|", m.get("title"), "|", m.get("content"))
        io.open("../tools/diag_memory_extract.txt", "w", encoding="utf-8").write(
            "saved=%s\nrows=%s\n" % (saved, len(rows)) + "\n".join(
                "%s|%s|%s" % (m.get("layer"), m.get("title"), m.get("content"))
                for m in rows if isinstance(m, dict)))
    finally:
        db.close()


asyncio.run(main())
