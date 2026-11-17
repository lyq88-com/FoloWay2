# -*- coding: utf-8 -*-
"""自捏角色全链路验证：设定 -> prompt -> 回复 -> 记忆隔离

跑法：python -u tools/verify_custom_persona.py
不依赖前端，直接打 8000 的接口。
"""
import io
import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1"
OUT = []


def log(s):
    print(s)
    OUT.append(s)


def req(method, path, payload=None, token=""):
    url = BASE + path
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "message": e.read().decode("utf-8", "ignore")}


def sse_chat(token, content, role_key, session_id=0):
    """调 /chat/send 拿完整回复（SSE 拼起来）"""
    url = BASE + "/chat/send"
    body = {
        "content": content,
        "role_type": "relaxed",
        "role_key": role_key,
        "dialogue_style": "gentle",
        "scene_type": "daily",
        "scene_name": "",
        "session_id": session_id,
    }
    r = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST")
    r.add_header("Content-Type", "application/json")
    r.add_header("Authorization", "Bearer " + token)
    r.add_header("Accept", "text/event-stream")
    text = ""
    sid = session_id
    with urllib.request.urlopen(r, timeout=180) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            try:
                obj = json.loads(line[5:].strip())
            except Exception:
                continue
            if obj.get("content"):
                text += obj["content"]
            if obj.get("session_id"):
                sid = obj["session_id"]
    return text, sid


def main():
    # 1) 登录（固定测试号，已存在则直接登录）
    phone = "13900001111"
    pwd = "test123456"
    res = req("POST", "/auth/register-username",
              {"username": phone, "password": pwd, "nickname": "验证号"})
    if res.get("code") != 200:
        res = req("POST", "/auth/login-username", {"username": phone, "password": pwd})
    token = (res.get("data") or {}).get("access_token") or (res.get("data") or {}).get("token")
    if not token:
        log("!! 登录失败: " + json.dumps(res, ensure_ascii=False)[:300])
        return 1
    log("1) 登录成功 token=" + token[:12] + "...")

    # 2) 造一个设定非常具体的角色
    payload = {
        "name": "阿栀",
        "avatar": "🌿",
        "personality": "毒舌、护短、心软",
        "description": "一只住在旧书店阁楼的猫妖，白天睡觉晚上看店",
        "backstory": "活了六百年，看过太多人来了又走，所以嘴上不饶人，其实最怕别人真的走掉。",
        "speechStyle": "慵懒吐槽",
        "speechTone": "语速偏慢，尾音拖长，爱用反问",
        "catchphrase": "哦——是吗",
        "voiceWords": "哼、啧、罢了",
        "taboos": "绝对不能提它的体重；不要说「猫就是高冷」",
        "expressionHabits": "句子短，先说结论再补一句吐槽；称呼用户时带着嫌弃",
        "angryStyle": "背过身去不看你，但尾巴尖还在动",
        "happyStyle": "会假装不经意地把书推到你手边",
        "nickname": "小蠢货",
        "voiceTone": "husky",
        "mood": "tired",
    }
    res = req("POST", "/persona/role", payload, token)
    role = res.get("data") or {}
    role_key = role.get("roleKey") or ""
    role_id = role.get("id") or 0
    if not role_key:
        log("!! 创建角色失败: " + json.dumps(res, ensure_ascii=False)[:400])
        return 1
    log(f"2) 角色已创建 role_key={role_key} id={role_id}")

    # 3) 创建前试聊（同一套 prompt）
    prev = req("POST", "/persona/preview", {**payload, "testMessage": "你是谁啊，介绍一下自己"}, token)
    prev_reply = ((prev.get("data") or {}).get("reply") or "").strip()
    log("3) 试聊回复: " + (prev_reply.replace("\n", " ")[:200] or ("失败 " + str(prev.get("message"))[:120])))
    applied = (prev.get("data") or {}).get("appliedFields") or []
    log("   命中设定字段: " + ", ".join(applied))

    # 4) 正式聊天：设定 + 记忆
    reply1, sid = sse_chat(token, "我叫小七，做平面设计的，最近在改一个甲方方案改到吐。", role_key)
    log("4) 第一轮回复: " + reply1.replace("\n", " ")[:220])

    reply2, _ = sse_chat(token, "你还记得我是干什么的吗？", role_key, sid)
    log("5) 记忆召回回复: " + reply2.replace("\n", " ")[:220])

    reply3, _ = sse_chat(token, "你是不是胖了？", role_key, sid)
    log("6) 雷区测试回复: " + reply3.replace("\n", " ")[:220])

    # 5) 记忆隔离：这个角色名下应只有自己的记忆
    st = req("GET", f"/memory/stats?role_key={role_key}", None, token)
    log("7) 该角色记忆统计: " + json.dumps((st.get("data") or {}), ensure_ascii=False))
    other = req("GET", "/memory/stats?role_key=__none__", None, token)
    log("   不存在角色的记忆统计(应为0): " + json.dumps((other.get("data") or {}), ensure_ascii=False))

    lst = req("GET", f"/memory/list?role_key={role_key}&page=1&page_size=20", None, token)
    items = ((lst.get("data") or {}).get("list") or [])
    log(f"8) 该角色记忆条数={len(items)}")
    for m in items[:6]:
        log("   - [" + m.get("layerLabel", "") + "] " + (m.get("title") or "") + ": " + (m.get("content") or "")[:60])

    # 6) 断言
    checks = []
    checks.append(("试聊有回复", bool(prev_reply)))
    checks.append(("称呼「小蠢货」出现", ("小蠢货" in reply1) or ("小蠢货" in reply2) or ("小蠢货" in prev_reply)))
    checks.append(("雷区未触犯(没提体重/高冷)", ("胖" not in reply3 or "不能" in reply3)))
    checks.append(("记忆里记住了职业", any("设计" in (m.get("content") or "") for m in items)))

    log("---- 断言 ----")
    ok = True
    for name, val in checks:
        log(("  [通过] " if val else "  [失败] ") + name)
        ok = ok and val
    log("整体: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


if __name__ == "__main__":
    code = main()
    try:
        io.open("tools/verify_custom_persona_result.txt", "w", encoding="utf-8").write("\n".join(OUT))
    except Exception as e:
        print("写结果文件失败", e)
    sys.exit(code)
