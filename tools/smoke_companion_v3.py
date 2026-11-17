# -*- coding: utf-8 -*-
r"""
陪伴感增强 v3 接口冒烟（只读 + 自造测试数据，不影响线上数据）

用法：
    python -u tools\smoke_companion_v3.py
前置：后端已启动（默认 http://127.0.0.1:8010，可用环境变量 QA_BASE 覆盖）
"""
import io
import os
import random
import string
import sys

import httpx

BASE = os.getenv("QA_BASE", "http://127.0.0.1:8010/api/v1")
OUT = []

PASS, FAIL = 0, 0


def log(ok, name, extra=""):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
    OUT.append(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {extra}" if extra else ""))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    rnd = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    username = f"smoke_{rnd}"
    client = httpx.Client(base_url=BASE, timeout=30.0)

    # 1. 注册拿 token
    r = client.post("/auth/register-username", json={
        "username": username, "password": "Test@12345",
    })
    body = r.json()
    token = (body.get("data") or {}).get("access_token") if body.get("code") == 200 else None
    log(bool(token), "注册并取到 token", f"code={body.get('code')} user={username}")
    if not token:
        OUT.append(f"注册响应：{str(body)[:300]}")
        return 1
    client.headers.update({"Authorization": f"Bearer {token}"})

    # 2. 记忆统计（初始应为 0）
    r = client.get("/memory/stats", params={"role_key": "cute"})
    d = r.json().get("data") or {}
    log(r.json().get("code") == 200, "记忆统计接口", f"total={d.get('total')} by_layer={d.get('by_layer')}")

    # 3. 手动添加一条长期信息
    r = client.post("/memory/add", json={
        "content": "用户让大家叫她小青", "layer": "profile",
        "title": "称呼", "salience": 9, "role_key": "cute",
    })
    ok = r.json().get("code") == 200
    mem_id = (r.json().get("data") or {}).get("id")
    log(ok, "手动添加长期记忆", f"id={mem_id}")

    # 4. 规则抽取：一句话同时命中称呼/偏好/约定三层
    text = "我叫阿七，我喜欢燕麦拿铁，别跟我说加油，我们约好周日去看展，记住我不吃香菜"
    r = client.post("/memory/extract", json={"text": text, "role_key": "cute"})
    saved = (r.json().get("data") or {}).get("saved")
    log(r.json().get("code") == 200 and (saved or 0) >= 3,
        "规则抽取（一句话抽多层）", f"新增 {saved} 条")

    # 5. 分层列表
    r = client.get("/memory/list", params={"role_key": "cute"})
    lst = (r.json().get("data") or {}).get("list") or []
    layers = {m["layer"] for m in lst}
    log(r.json().get("code") == 200 and len(lst) >= 3,
        "记忆列表分层展示", f"{len(lst)} 条，分层={sorted(layers)}")

    # 6. 角色隔离：换一个角色查，应看不到 cute 的专属记忆
    r = client.get("/memory/list", params={"role_key": "gacha_none"})
    lst2 = (r.json().get("data") or {}).get("list") or []
    ids2 = {m["id"] for m in lst2}
    isolated = not ({m["id"] for m in lst} & ids2)
    log(isolated, "记忆按角色隔离（A 角色记的不串到 B）",
        f"cute={len(lst)} 条 / 其他角色={len(lst2)} 条")

    # 7. 单条删除
    if mem_id:
        r = client.delete(f"/memory/{mem_id}")
        log(r.json().get("code") == 200, "单条删除记忆", r.json().get("message"))
        r = client.delete(f"/memory/{mem_id}")
        log(r.json().get("code") == 404, "重复删除返回 404（幂等）")

    # 8. 一键清空
    r = client.delete("/memory/clear", params={"role_key": "cute"})
    deleted = (r.json().get("data") or {}).get("deleted")
    r2 = client.get("/memory/stats", params={"role_key": "cute"})
    left = (r2.json().get("data") or {}).get("total")
    log(r.json().get("code") == 200 and left == 0, "一键清空记忆", f"清空 {deleted} 条，剩余 {left}")

    # 9. 角色列表 + 官方人设
    r = client.get("/persona/roles", params={"scope": "official", "detail": "true"})
    roles = r.json().get("data") or []
    has_story = all(x.get("backstory") for x in roles)
    log(r.json().get("code") == 200 and len(roles) >= 4 and has_story,
        "官方角色含完整人设故事线",
        f"{len(roles)} 个：" + "、".join(f"{x['name']}({x['moodLabel']})" for x in roles))

    # 10. 自捏角色（含雷区/禁忌/表达习惯/生气开心/音色）
    r = client.post("/persona/role", json={
        "name": "冒烟小搭档", "avatar": "🐱", "personality": "嘴硬心软",
        "backstory": "一只嘴上不饶人但会半夜给你盖被子的猫。",
        "speechStyle": "短句，爱用反问",
        "quirks": "被夸会岔开话题",
        "taboos": "不许提它的体重；不要说'猫就是高冷'",
        "expressionHabits": "结尾爱带'哼'",
        "angryStyle": "背过身去不看你，但尾巴还在晃",
        "happyStyle": "会蹭你的手，话变多",
        "voiceTone": "husky",
        "nickname": "笨蛋",
        "mood": "happy",
    })
    role = r.json().get("data") or {}
    role_id = role.get("id")
    log(r.json().get("code") == 200 and role.get("taboos") and role.get("voiceTone") == "husky",
        "自捏角色：雷区/禁忌/表达习惯/生气开心/音色",
        f"id={role_id} key={role.get('roleKey')} 音色={role.get('voiceTone')}")

    # 11. 设置心情状态
    if role_id:
        r = client.post(f"/persona/role/{role_id}/mood", json={"mood": "tired", "moodNote": "今天有点困"})
        mood = (r.json().get("data") or {}).get("mood")
        log(r.json().get("code") == 200 and mood == "tired", "设置角色心情/状态", f"mood={mood}")

    # 12. 扭蛋抽角色（完整人设 + 独立记忆空间）
    r = client.post("/persona/gacha/draw")
    g = r.json().get("data") or {}
    gkey = g.get("roleKey")
    log(r.json().get("code") == 200 and g.get("backstory") and g.get("isNew"),
        "扭蛋抽到完整人设角色",
        f"{g.get('rarityLabel')}·{g.get('name')} 音色={g.get('voiceTone')}")

    # 13. 扭蛋角色自带独立记忆空间（初见记忆属于它自己）
    if gkey:
        r = client.get("/memory/list", params={"role_key": gkey})
        gl = (r.json().get("data") or {}).get("list") or []
        log(r.json().get("code") == 200 and len(gl) >= 1,
            "扭蛋角色有独立记忆空间", f"{len(gl)} 条：" + (gl[0]["content"][:32] if gl else ""))
        # 且不会串到别的角色
        r = client.get("/memory/list", params={"role_key": "cute"})
        cl = (r.json().get("data") or {}).get("list") or []
        log(not ({m['id'] for m in gl} & {m['id'] for m in cl}),
            "扭蛋角色记忆不串到官方角色")

    # 14. 主动陪伴（fast=模板，不等大模型）
    r = client.get("/proactive/next", params={"role_key": "cute", "fast": "true"})
    p = r.json().get("data")
    log(r.json().get("code") == 200 and bool(p) and bool((p or {}).get("content")),
        "主动陪伴：取到主动消息",
        f"type={(p or {}).get('type')} content={(p or {}).get('content', '')[:40]}")
    # 同一件事 24h 内不再重复打扰
    r2 = client.get("/proactive/next", params={"role_key": "cute", "fast": "true"})
    log((r2.json().get("data") is None) or r2.json().get("data", {}).get("type") != (p or {}).get("type"),
        "主动消息去重（同一件事不反复打扰）")

    # 15. 回归：老接口不受影响
    r = client.get("/chat/personas")
    ps = r.json().get("data") or []
    log(r.json().get("code") == 200 and len(ps) >= 4 and "roleType" in ps[0],
        "回归：/chat/personas 结构未变（仅新增字段）",
        f"{len(ps)} 个角色，首个={ps[0].get('name')}/{ps[0].get('moodLabel')}")
    r = httpx.get(BASE.replace("/api/v1", "/health"), timeout=10.0)
    log(r.status_code == 200, "回归：健康检查", f"HTTP {r.status_code}")

    OUT.append("")
    OUT.append(f"===== 通过 {PASS} / 失败 {FAIL} =====")
    text = "\n".join(OUT)
    print(text)
    # PowerShell 重定向会产出 UTF-16，这里自己写一份 UTF-8 结果文件便于回读
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "smoke_companion_v3_result.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
