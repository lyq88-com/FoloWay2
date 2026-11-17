# -*- coding: utf-8 -*-
"""
POST /api/v1/chat/quick 接口体检
================================
用途：验证「业务触发式 AI」（打卡鼓励 / 情绪疏导 / 正念引导 / 地图节点分享）
     走的 common/ai-service.js -> /api/v1/chat/quick 这条新链路确实能拿到真大模型回复。

用法：
    cd liyeqing/server
    python -u ..\tools\test_ai_quick_api.py
"""
import io
import os
import random
import string
import time

import requests

BASE = "http://127.0.0.1:8000/api/v1"
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ai_quick_out.txt")
_LOG = []


def print_utf8(*a):
    _LOG.append(" ".join(str(x) for x in a))


def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def get_token():
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": "qk_" + rnd(), "password": "test123456",
                            "nickname": "quick探针"},
                      timeout=(5, 30))
    return r.json()["data"]["access_token"]


def quick(token, system, user_msg):
    t0 = time.time()
    r = requests.post(f"{BASE}/chat/quick",
                      headers={"Authorization": f"Bearer {token}"},
                      json={"messages": [
                          {"role": "system", "content": system},
                          {"role": "user", "content": user_msg},
                      ]},
                      timeout=(5, 60))
    cost = time.time() - t0
    return r.status_code, r.json(), cost


def main():
    print_utf8("=" * 62)
    print_utf8("POST /api/v1/chat/quick 接口体检")
    print_utf8("=" * 62)
    token = get_token()
    print_utf8("[1] token 已获取")

    cases = [
        ("打卡成功", "你是林夕，一位温柔的倾听者。回复50-150字，口语化。",
         "【当前触发事件】打卡成功：完成了「早起」，连续 7 天"),
        ("情绪记录", "你是林夕，一位温柔的倾听者。回复50-150字，口语化。",
         "【当前触发事件】情绪记录：记录了焦虑情绪，强度 4"),
        ("正念完成", "你是林夕，一位温柔的倾听者。回复50-150字，口语化。",
         "【当前触发事件】正念完成：完成了「5分钟呼吸」正念练习"),
    ]

    ok = True
    for name, sysp, msg in cases:
        st, body, cost = quick(token, sysp, msg)
        reply = (body.get("data") or {}).get("reply", "")
        good = st == 200 and body.get("code") == 200 and len(reply) > 5
        print_utf8("")
        print_utf8("[2] %s | HTTP %s code=%s 耗时 %.2fs" % (name, st, body.get("code"), cost))
        print_utf8("    回复(%d字)：%s" % (len(reply), reply))
        if not good:
            ok = False
            print_utf8("    [FAIL] 原始响应：" + str(body)[:300])

    # 负例：最后一条不是 user
    st, body, _ = quick(token, "sys", "")
    r2 = requests.post(f"{BASE}/chat/quick",
                       headers={"Authorization": f"Bearer {token}"},
                       json={"messages": [{"role": "system", "content": "x"},
                                          {"role": "assistant", "content": "y"}]},
                       timeout=(5, 30))
    bad = r2.json()
    print_utf8("")
    print_utf8("[3] 负例(末条非user)：HTTP %s code=%s msg=%s"
               % (r2.status_code, bad.get("code"), bad.get("message")))
    if bad.get("code") == 200:
        ok = False

    print_utf8("")
    print_utf8("=" * 62)
    print_utf8("结论：" + ("[OK] 新接口可用" if ok else "[FAIL] 存在问题"))
    print_utf8("=" * 62)
    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(_LOG))
    print("written -> " + OUT_FILE)


if __name__ == "__main__":
    main()
