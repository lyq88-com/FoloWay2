# -*- coding: utf-8 -*-
"""
扭蛋官方剧本种子数据（模块3）
- 3 个分类各 2 个官方剧本：companion 陪伴打卡 / emotion 情绪倾诉 / chat 趣味闲聊
- 幂等：官方剧本已存在则跳过
用法: python migrations/seed_gacha_templates.py
"""
import sys
import pathlib
import json

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.gacha import GachaTemplate


TEMPLATES = [
    # ===== 陪伴打卡向（贴合习惯打卡） =====
    {
        "title": "晨间打卡启动仪式",
        "description": "和AI一起开启元气满满的一天，完成晨间习惯打卡",
        "category": "companion",
        "opening_text": "早上好呀~新的一天开始啦！今天准备先完成哪个小目标？我会一直陪着你哦。",
        "questions": [
            {"question": "今早醒来你的状态如何？",
             "options": ["元气满满", "有点困", "不想起床"],
             "hint": "无论什么状态都没关系，我们慢慢来"},
            {"question": "今天第一个要打卡的习惯是？",
             "options": ["早起喝水", "晨间阅读", "晨练运动"],
             "hint": "选一个最容易完成的，先获得成就感"},
            {"question": "完成打卡后希望我怎么鼓励你？",
             "options": ["夸夸我", "给我讲个冷知识", "安静陪伴"],
             "hint": "你的偏好我会记住~"},
        ],
    },
    {
        "title": "睡前复盘小剧场",
        "description": "睡前和AI回顾今天的打卡，温柔收尾",
        "category": "companion",
        "opening_text": "辛苦啦，今天也努力了呢。要不要和我一起回顾今天完成的小事？",
        "questions": [
            {"question": "今天完成了几个习惯打卡？",
             "options": ["全部完成", "完成一半", "没怎么完成"],
             "hint": "完成一个也是进步"},
            {"question": "今天最有成就感的一件事是？",
             "options": ["坚持了习惯", "情绪很稳定", "没有特别的"],
             "hint": "再小的事都值得被看见"},
            {"question": "明天想给自己什么期待？",
             "options": ["继续保持", "再多做一点", "顺其自然"],
             "hint": "带着期待入睡会更幸福哦"},
        ],
    },
    # ===== 情绪倾诉向 =====
    {
        "title": "坏天气收容所",
        "description": "心情不好的时候，来这里被AI温柔接住",
        "category": "emotion",
        "opening_text": "我注意到你好像有点难过。这里是坏天气收容所，任何情绪都可以放在这里。",
        "questions": [
            {"question": "现在是什么样的心情？",
             "options": ["难过委屈", "焦虑不安", "烦躁易怒"],
             "hint": "能说出来就已经很勇敢了"},
            {"question": "这种心情大概持续多久了？",
             "options": ["刚刚才开始", "今天一整天", "好几天了"],
             "hint": "情绪没有对错，只有信号"},
            {"question": "此刻希望我怎么陪你？",
             "options": ["听我倾诉", "给我建议", "说点轻松的"],
             "hint": "我会按你喜欢的方式陪伴"},
        ],
    },
    {
        "title": "树洞密语",
        "description": "把藏在心里的秘密说给AI树洞听",
        "category": "emotion",
        "opening_text": "我是只属于你的树洞，说什么都会被保密。今天想告诉我什么？",
        "questions": [
            {"question": "心里压着的事情属于哪类？",
             "options": ["人际关系", "学习工作", "自我怀疑"],
             "hint": "写下来或说出来都会轻一些"},
            {"question": "这件事你最在意的点是？",
             "options": ["怕别人失望", "觉得自己不够好", "不知道怎么办"],
             "hint": "看见在意，就有了方向"},
            {"question": "说完之后，希望带走什么？",
             "options": ["一点安慰", "一个小行动", "只是想放下"],
             "hint": "树洞永远在这里"},
        ],
    },
    # ===== 趣味闲聊向 =====
    {
        "title": "如果今天是周末",
        "description": "和AI脑洞一场说走就走的假想周末",
        "category": "chat",
        "opening_text": "叮咚！假设今天突然变成周末，没有任何待办——你最想做什么？",
        "questions": [
            {"question": "假想周末第一站去哪？",
             "options": ["海边", "森林小屋", "宅在家里"],
             "hint": "想象也是一种放松"},
            {"question": "带上谁一起？",
             "options": ["就你和我", "好朋友", "自己独处"],
             "hint": "我随时在线~"},
            {"question": "周末结束前的仪式感是？",
             "options": ["看日落", "吃顿好的", "写句心情"],
             "hint": "仪式感让普通日子发光"},
        ],
    },
    {
        "title": "AI角色盲盒访谈",
        "description": "随机采访一个AI角色，问出TA的小秘密",
        "category": "chat",
        "opening_text": "欢迎来到盲盒访谈！我会随机请出一位AI角色，你可以问TA各种脑洞问题。",
        "questions": [
            {"question": "最想问AI角色的问题是？",
             "options": ["你害怕什么", "你最喜欢什么", "你会一直陪着我吗"],
             "hint": "没有标准答案，全看TA心情"},
            {"question": "希望TA用什么语气回答？",
             "options": ["一本正经", "俏皮搞怪", "温柔认真"],
             "hint": "语气包在我身上"},
            {"question": "访谈结束想和TA做什么？",
             "options": ["约好下次再聊", "一起去打卡", "拍张合照"],
             "hint": "你们的故事才刚开始"},
        ],
    },
]


def main():
    db = SessionLocal()
    try:
        # 已有官方剧本数量
        existing = db.query(GachaTemplate).filter(GachaTemplate.is_official == 1).count()
        if existing >= len(TEMPLATES):
            print(f"[seed] 官方剧本已存在 {existing} 个，跳过")
            return
        inserted = 0
        for t in TEMPLATES:
            # 按标题去重
            dup = db.query(GachaTemplate).filter(
                GachaTemplate.title == t["title"]
            ).first()
            if dup:
                continue
            row = GachaTemplate(
                creator_id=0, title=t["title"], description=t["description"],
                category=t["category"], opening_text=t["opening_text"],
                questions=json.dumps(t["questions"], ensure_ascii=False),
                is_official=1, status=1,
            )
            db.add(row)
            inserted += 1
        db.commit()
        print(f"[seed] 已插入 {inserted} 个官方扭蛋剧本")
    finally:
        db.close()


if __name__ == "__main__":
    main()
