# -*- coding: utf-8 -*-
"""活动模块验证（2026-10-27）

pages/activity/activity 原是纯占位页（只有「功能建设中 · 敬请期待」），
现在补了每日签到 + 活跃任务进度，本脚本验证后端接口。

覆盖：
  1. 首次查询：未签到
  2. 首次签到：成功 + 发奖 + streak=1
  3. 重复签到：不重复发奖（同一自然日只算一次）
  4. 任务进度接口
  5. 鉴权：无 token 401

运行：
    cd liyeqing && python -u tools\\test_activity_signin.py
"""
import io
import sys
import random
import string

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API = "http://127.0.0.1:8000/api/v1"
OK = 200

PASS, FAIL = [], []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  [{}] {} {}".format(tag, name, ("| " + str(detail)) if detail else ""))
    (PASS if cond else FAIL).append(name)
    return cond


def rnd(prefix="act"):
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main():
    print("=" * 66)
    print("活动模块验证：每日签到 / 活跃任务")
    print("=" * 66)

    u, p = rnd(), "Test@12345"
    r = requests.post(API + "/auth/register-username",
                      json={"username": u, "password": p}, timeout=10).json()
    token = (r.get("data") or {}).get("access_token")
    if not token:
        r = requests.post(API + "/auth/login-username",
                          json={"username": u, "password": p}, timeout=10).json()
        token = (r.get("data") or {}).get("access_token")
    if not check("拿到 token", bool(token), r.get("message") if not token else ""):
        return 1
    H = {"Authorization": "Bearer " + token}

    # ---------- 1. 首次查询 ----------
    print("\n[1] 首次查询签到状态")
    body = requests.get(API + "/activity/signin", headers=H, timeout=10).json()
    d = body.get("data") or {}
    check("业务码 200", body.get("code") == OK, body.get("message"))
    check("初始未签到", d.get("signed_today") is False, d.get("signed_today"))
    check("初始连续 0 天", d.get("streak") == 0, d.get("streak"))
    check("返回今日可领奖励", (d.get("today_reward") or 0) > 0, d.get("today_reward"))

    # ---------- 2. 首次签到 ----------
    print("\n[2] 首次签到")
    body = requests.post(API + "/activity/signin", json={}, headers=H, timeout=10).json()
    d = body.get("data") or {}
    check("业务码 200", body.get("code") == OK, body.get("message"))
    check("签到成功", d.get("signed") is True, d.get("message"))
    check("连续天数 = 1", d.get("streak") == 1, d.get("streak"))
    check("累计天数 = 1", d.get("total_days") == 1, d.get("total_days"))
    check("发出奖励 > 0", (d.get("reward") or 0) > 0, d.get("reward"))

    # ---------- 3. 重复签到 ----------
    print("\n[3] 同日重复签到（不应重复发奖）")
    body = requests.post(API + "/activity/signin", json={}, headers=H, timeout=10).json()
    d = body.get("data") or {}
    check("业务码 200", body.get("code") == OK)
    check("第二次 signed=False", d.get("signed") is False, d.get("message"))
    check("第二次 reward=0", (d.get("reward") or 0) == 0, d.get("reward"))
    check("累计天数仍是 1", d.get("total_days") == 1, d.get("total_days"))

    # 状态接口也应显示已签到
    body = requests.get(API + "/activity/signin", headers=H, timeout=10).json()
    d = body.get("data") or {}
    check("状态接口显示今日已签到", d.get("signed_today") is True, d.get("signed_today"))
    check("今日可领奖励归 0", (d.get("today_reward") or 0) == 0, d.get("today_reward"))
    check("返回 last_date", bool(d.get("last_date")), d.get("last_date"))

    # ---------- 4. 任务进度 ----------
    print("\n[4] 活跃任务进度")
    body = requests.get(API + "/activity/tasks", headers=H, timeout=10).json()
    d = body.get("data") or {}
    tasks = d.get("list") or []
    check("业务码 200", body.get("code") == OK)
    check("返回 4 个任务", len(tasks) == 4, len(tasks))
    check("任务字段完整",
          all({"id", "name", "current", "target", "progress", "done"} <= set(t) for t in tasks))
    check("进度百分比在 0~100",
          all(0 <= t["progress"] <= 100 for t in tasks))

    # ---------- 5. 鉴权 ----------
    print("\n[5] 鉴权")
    r = requests.get(API + "/activity/signin", timeout=10)
    check("无 token 访问被拒", r.status_code == 401 or (r.json().get("code") or 0) != OK, r.status_code)

    print("\n" + "=" * 66)
    print("PASS {} / FAIL {}".format(len(PASS), len(FAIL)))
    if FAIL:
        print("失败项：" + "、".join(FAIL))
    print("=" * 66)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
