# -*- coding: utf-8 -*-
"""
AI 真模型链路体检脚本
====================
用途：证明 pages/chat/chat.vue -> /api/v1/chat/send -> FastAPI 8000 这条主链路
     到底用的是「真大模型」还是「本地 mock 模板」。

判定原理：问一个 mock 模板绝对答不上来的事实性问题。
  - 若命中的是 mock，_generate_mock_reply 只会按关键词匹配，
    对不匹配的输入一律回 "我在认真听着呢。能跟我多说说吗？我会一直在这里陪你。"
  - 若命中的是真模型，会给出事实性答案。

用法：
    cd liyeqing/server
    python -u ..\tools\test_ai_real_model.py
"""
import io
import json
import os
import random
import string
import sys
import time

import requests

BASE = "http://127.0.0.1:8000/api/v1"
TIMEOUT = (5, 90)
# PowerShell 控制台是 GBK，中文直接 print 会乱码 —— 统一写 UTF-8 文件再读
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ai_probe_out.txt")
_LOG = []


def print_utf8(*a, **kw):
    line = " ".join(str(x) for x in a)
    _LOG.append(line)

# mock 模板的全部固定话术（用于识别"假 AI"）
MOCK_REPLIES = {
    "我听到你了，现在感觉一定不太好受。不管发生了什么，你愿意跟我说说吗？我会一直在这里陪着你。",
    "看起来你遇到了让你很不开心的事情。深呼吸，先让自己平静下来。然后我们一起想想怎么处理好？",
    "哇！听到你这么开心我也跟着高兴起来了！你值得这些美好，继续加油呀！",
    "太棒了！每一次坚持都是对自己的承诺。继续保持，你会越来越好！",
    "我在呢！今天感觉怎么样？有什么想跟我聊聊的吗？",
    "我在认真听着呢。能跟我多说说吗？我会一直在这里陪你。",
    "AI服务暂时不可用，请稍后再试",
}


def rnd(n=8):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def get_token():
    user = "ai_probe_" + rnd(6)
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": user, "password": "test123456",
                            "nickname": "AI探针"},
                      timeout=TIMEOUT)
    data = r.json()
    if data.get("code") == 200:
        return data["data"]["access_token"], user
    # 已存在则换号重试一次
    user = "ai_probe_" + rnd(6)
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": user, "password": "test123456",
                            "nickname": "AI探针"},
                      timeout=TIMEOUT)
    data = r.json()
    return data["data"]["access_token"], user


def ask(token, content, role_type="companion", dialogue_style="gentle"):
    """发一条消息，收完整 SSE 流，返回 (拼接回复, 首字延迟秒数)"""
    t0 = time.time()
    first = None
    buf = []
    with requests.post(
        f"{BASE}/chat/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": content, "role_type": role_type,
              "dialogue_style": dialogue_style, "session_id": 0,
              "scene_type": "", "scene_name": "", "language": ""},
        stream=True, timeout=TIMEOUT,
    ) as resp:
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data: "):
                continue
            try:
                d = json.loads(raw[6:])
            except json.JSONDecodeError:
                continue
            c = d.get("content", "")
            if c:
                if first is None:
                    first = time.time() - t0
                buf.append(c)
            if d.get("done"):
                break
    return "".join(buf), (first or 0)


def main():
    print_utf8("=" * 62)
    print_utf8("AI 真模型链路体检 —— 目标 FastAPI 8000")
    print_utf8("=" * 62)

    token, user = get_token()
    print_utf8("[1] 拿 token 成功，测试账号：", user)

    cases = [
        ("事实问答", "用一句话解释什么是量子纠缠"),
        ("日常闲聊", "在干嘛呢"),
        ("习惯话题", "我今天又没早起，怎么办"),
    ]

    ok = True
    for name, q in cases:
        reply, delay = ask(token, q)
        is_mock = reply in MOCK_REPLIES
        flag = "[FAIL] MOCK模板" if is_mock else "[OK] 真模型"
        print_utf8("")
        print_utf8("[2]", name, "| 提问：", q)
        print_utf8("    首字延迟：%.2fs   判定：%s" % (delay, flag))
        print_utf8("    回复(%d字)：%s" % (len(reply), reply))
        if is_mock:
            ok = False

    print_utf8("")
    print_utf8("=" * 62)
    if ok:
        print_utf8("结论：[OK] 主链路走的是【真大模型】")
    else:
        print_utf8("结论：[FAIL] 主链路仍在走【本地 mock 模板】")
        print_utf8("       检查 server/.env 的 AI_MODEL=openai 并重启 8000")
    print_utf8("=" * 62)

    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(_LOG))
    print("written -> " + OUT_FILE)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
