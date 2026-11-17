# -*- coding: utf-8 -*-
"""
准备一个可直接用于 AI 端到端验证的账号：
  注册 -> 保存性格测评结果（跳过测评引导页）-> 创建两个习惯
输出 用户名/密码，供浏览器登录使用。

用法：
    cd liyeqing/server
    python -u ..\tools\setup_ai_e2e_account.py
"""
import io
import os
import random
import string

import requests

BASE = "http://127.0.0.1:8000/api/v1"
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ai_e2e_account.txt")


def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def main():
    username = "aie2e_" + rnd()
    password = "test123456"

    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": username, "password": password,
                            "nickname": "AI端到端"},
                      timeout=(5, 30))
    token = r.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # 1) 性格测评结果：跳过首次登录的测评引导页
    requests.post(f"{BASE}/personality/result", headers=h,
                  json={"personality": "buddha", "emotionalResilience": "medium",
                        "procrastination": "low", "companionStyle": "warm",
                        "quizVersion": "v1", "source": "app"},
                  timeout=(5, 30))

    # 2) 两个习惯，用于触发打卡成功/失败的 AI 互动
    for name, icon in (("早起", "🌅"), ("喝水", "💧")):
        requests.post(f"{BASE}/habit/create", headers=h,
                      json={"name": name, "icon": icon, "description": name,
                            "target": "每天", "difficulty": "easy",
                            "color": "#6B8E7B", "reminder_time": "07:00"},
                      timeout=(5, 30))

    text = "username=%s\npassword=%s\n" % (username, password)
    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
