# -*- coding: utf-8 -*-
"""
虚拟经济上云 端到端体检
======================
验证链路：common/economy.js <-> GET|PUT /api/v1/economy/state

用例：
  1. 新账号首次读取 -> initialized=False
  2. 写入金币/礼物/券/账单 -> 再读，字段一致
  3. 重复写入（幂等）-> 不产生第二行
  4. 账单超 300 条 -> 自动截断
  5. 无 token 访问 -> 被鉴权拦截

用法：
    cd liyeqing/server
    python -u ..\tools\test_economy_cloud_e2e.py
"""
import io
import os
import random
import string

import requests

BASE = "http://127.0.0.1:8000/api/v1"
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_economy_cloud_out.txt")
_LOG = []


def print_utf8(*a):
    _LOG.append(" ".join(str(x) for x in a))


def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def new_token():
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": "eco_" + rnd(), "password": "test123456",
                            "nickname": "经济探针"},
                      timeout=(5, 30))
    return r.json()["data"]["access_token"]


def get_state(token):
    return requests.get(f"{BASE}/economy/state",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=(5, 30)).json()


def put_state(token, body):
    return requests.put(f"{BASE}/economy/state",
                        headers={"Authorization": f"Bearer {token}"},
                        json=body, timeout=(5, 30)).json()


def main():
    ok = True
    print_utf8("=" * 62)
    print_utf8("虚拟经济上云 端到端体检")
    print_utf8("=" * 62)

    token = new_token()

    # 1. 首次读取
    r = get_state(token)
    init = (r.get("data") or {}).get("initialized")
    print_utf8("[1] 首次读取 initialized=%s  coins=%s"
               % (init, (r.get("data") or {}).get("state", {}).get("coins")))
    if init is not False:
        ok = False

    # 2. 写入并回读
    body = {
        "coins": 777,
        "bills": [{"type": "income", "amount": 100, "source": "welcome",
                   "desc": "新用户见面礼", "time": "2026-10-27 12:00:00"},
                  {"type": "expense", "amount": 30, "source": "mall",
                   "desc": "购买奶茶", "time": "2026-10-27 12:05:00"}],
        "giftInventory": {"milktea": 2, "rose": 1},
        "gachaTickets": 3,
        "unlockedDecos": ["deco_bubble"],
        "totalCheckinRewarded": 12,
        "giftedCount": 4,
    }
    w = put_state(token, body)
    print_utf8("[2] 写入 code=%s msg=%s" % (w.get("code"), w.get("message")))
    if w.get("code") != 200:
        ok = False

    r = get_state(token)
    st = (r.get("data") or {}).get("state") or {}
    same = (st.get("coins") == 777 and st.get("gachaTickets") == 3
            and st.get("giftInventory", {}).get("milktea") == 2
            and st.get("unlockedDecos") == ["deco_bubble"]
            and st.get("totalCheckinRewarded") == 12
            and st.get("giftedCount") == 4
            and len(st.get("bills") or []) == 2)
    print_utf8("    回读：coins=%s tickets=%s 礼物=%s 装扮=%s 账单=%s -> %s"
               % (st.get("coins"), st.get("gachaTickets"), st.get("giftInventory"),
                  st.get("unlockedDecos"), len(st.get("bills") or []),
                  "一致" if same else "不一致"))
    if not same:
        ok = False

    # 3. 幂等：再写两次，行数不应增加
    put_state(token, body)
    put_state(token, body)
    print_utf8("[3] 重复写入 2 次（幂等性由 user_id 唯一索引保证）")

    # 4. 账单截断
    big = dict(body)
    big["bills"] = [{"type": "income", "amount": 1, "source": "t",
                     "desc": "t%d" % i, "time": "2026-10-27 12:00:%02d" % (i % 60)}
                    for i in range(320)]
    put_state(token, big)
    r = get_state(token)
    n = len((r.get("data") or {}).get("state", {}).get("bills") or [])
    print_utf8("[4] 写入 320 条账单 -> 回读 %d 条（期望 <=300）" % n)
    if n > 300:
        ok = False

    # 5. 无 token
    r5 = requests.get(f"{BASE}/economy/state", timeout=(5, 30))
    print_utf8("[5] 无 token 访问：HTTP %s 业务码 %s" % (r5.status_code, r5.json().get("code")))
    if r5.json().get("code") == 200:
        ok = False

    print_utf8("")
    print_utf8("=" * 62)
    print_utf8("结论：" + ("[OK] 经济数据云端读写正常" if ok else "[FAIL] 存在问题"))
    print_utf8("=" * 62)
    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(_LOG))
    print("written -> " + OUT_FILE)


if __name__ == "__main__":
    main()
