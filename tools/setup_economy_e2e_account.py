# -*- coding: utf-8 -*-
"""
准备用于「经济上云」前端验证的账号：
  注册 -> 性格测评结果 -> 两个习惯 -> 云端预置经济数据（金币555 / 星星×2 / 扭蛋券1）

用法：
    cd liyeqing/server
    python -u ..\tools\setup_economy_e2e_account.py
"""
import io
import os
import random
import string

import requests

BASE = "http://127.0.0.1:8000/api/v1"
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_economy_e2e_account.txt")


def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def main():
    username = "ecosync_" + rnd()
    password = "test123456"
    token = requests.post(f"{BASE}/auth/register-username",
                          json={"username": username, "password": password,
                                "nickname": "经济同步"},
                          timeout=(5, 30)).json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    requests.post(f"{BASE}/personality/result", headers=h,
                  json={"personality": "buddha", "emotionalResilience": "medium",
                        "procrastination": "low", "companionStyle": "warm",
                        "quizVersion": "v1", "source": "app"},
                  timeout=(5, 30))
    for name, icon in (("早起", "🌅"), ("喝水", "💧")):
        requests.post(f"{BASE}/habit/create", headers=h,
                      json={"name": name, "icon": icon, "description": name,
                            "target": "每天", "difficulty": "easy",
                            "color": "#6B8E7B", "reminder_time": "07:00"},
                      timeout=(5, 30))

    requests.put(f"{BASE}/economy/state", headers=h,
                 json={"coins": 555,
                       "bills": [{"type": "income", "amount": 555, "source": "seed",
                                  "desc": "脚本预置", "time": "2026-10-27 12:00:00"}],
                       "giftInventory": {"star": 2},
                       "gachaTickets": 1,
                       "unlockedDecos": [],
                       "totalCheckinRewarded": 0,
                       "giftedCount": 0},
                 timeout=(5, 30))

    text = "username=%s\npassword=%s\n" % (username, password)
    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
