# -*- coding: utf-8 -*-
"""BUG-001 / BUG-002 修复验证（E2E）

BUG-001：GET /chat/personas 返回硬编码假数据（字符串 id）→ 陪伴记录 422 不入库
BUG-002：Flask user 表与 FastAPI users 表 id 不共享 → 跨服务串号 / 注册后登录不了

运行：
    cd liyeqing
    python -u tools\\test_bug001_002_fix.py
"""
import io
import sys
import time
import random
import string

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API = "http://127.0.0.1:8000/api/v1"
FLASK = "http://127.0.0.1:5000/api"

PASS, FAIL = [], []

# 统一响应约定（app/schemas/common.py）：成功 code=200，失败 code=400/404/409...
OK = 200


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  [{}] {} {}".format(tag, name, ("| " + str(detail)) if detail else ""))
    (PASS if cond else FAIL).append(name)
    return cond


def rnd(prefix="bugfix"):
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main():
    print("=" * 66)
    print("BUG-001 验证：角色列表与陪伴记录入库")
    print("=" * 66)

    # ---------- 准备账号（FastAPI 主链路） ----------
    u, p = rnd("b1"), "Test@12345"
    r = requests.post(API + "/auth/register-username",
                      json={"username": u, "password": p}, timeout=10).json()
    token = (r.get("data") or {}).get("access_token")
    if not token:
        r = requests.post(API + "/auth/login-username",
                          json={"username": u, "password": p}, timeout=10).json()
        token = (r.get("data") or {}).get("access_token")
    check("拿到业务侧 token", bool(token), (r.get("message") if not token else ""))
    if not token:
        return 1
    H = {"Authorization": "Bearer " + token}

    # ---------- 1. personas 返回真实角色 ----------
    res = requests.get(API + "/chat/personas", headers=H, timeout=10).json()
    roles = (res.get("data") or [])
    check("personas 返回非空", len(roles) > 0, "共 {} 条".format(len(roles)))
    if roles:
        print("       角色样例：{}".format(roles[0]))
    ids_int = all(isinstance(x.get("id"), int) for x in roles)
    check("角色 id 全部为整型", ids_int, [x.get("id") for x in roles])
    check("角色头像非空", all((x.get("avatar") or "") for x in roles),
          [x.get("avatar") for x in roles])
    check("角色副标题有差异化内容",
          len({(x.get("traits") or [""])[0] for x in roles}) > 1,
          [ (x.get("traits") or [""])[0] for x in roles ])

    # ---------- 2. 用真实 role_id 开始陪伴 ----------
    target = roles[1]["id"] if len(roles) > 1 else roles[0]["id"]
    res = requests.post(API + "/companion/start", headers=H, timeout=10,
                        json={"role_id": target, "scene_type": "study",
                              "scene_name": "学习", "bg_img": "默认",
                              "bg_sound": "雨声"}).json()
    data = res.get("data") or {}
    check("开始陪伴返回成功（code=200 且有记录 id）",
          res.get("code") == OK and data.get("id"), res.get("message"))
    check("陪伴记录 role_id 与所选一致", data.get("role_id") == target,
          "期望 {} 实际 {}".format(target, data.get("role_id")))
    check("陪伴记录场景/背景音正确",
          data.get("scene_type") == "study" and data.get("bg_sound") == "雨声",
          "{}/{}".format(data.get("scene_type"), data.get("bg_sound")))
    rec_id = data.get("id")
    # 记录确实落在库里
    res2 = requests.get(API + "/companion/records?page=1&page_size=5", headers=H, timeout=10).json()
    in_db = any(x.get("id") == rec_id for x in ((res2.get("data") or {}).get("list") or []))
    check("陪伴记录可在列表中查到（已入库）", in_db, "record_id={}".format(rec_id))

    # ---------- 3. 兼容旧客户端传字符串 role_id（原会 422） ----------
    res = requests.post(API + "/companion/start", headers=H, timeout=10,
                        json={"role_id": "companion", "scene_type": "sleep",
                              "scene_name": "哄睡", "bg_img": "默认",
                              "bg_sound": "静音"}).json()
    ok_legacy = res.get("code") == OK and (res.get("data") or {}).get("id")
    check("字符串 role_id 不再 422，记录正常入库", ok_legacy, res.get("message"))
    if ok_legacy:
        print("       回退后 role_id={}（默认角色）".format((res.get("data") or {}).get("role_id")))

    print()
    print("=" * 66)
    print("BUG-002 验证：Flask 与 FastAPI 账号体系打通")
    print("=" * 66)

    # ---------- 1. 走 Flask 注册 ----------
    fu, fe, fp = rnd("b2"), rnd("b2") + "@test.com", "Test@12345"
    res = requests.post(FLASK + "/register", timeout=10,
                        json={"username": fu, "password": fp, "email": fe}).json()
    check("Flask 注册成功", res.get("code") == 200, res.get("message"))
    xid = (res.get("data") or {}).get("xuntu_user_id")
    check("注册返回业务侧 xuntu_user_id", bool(xid), xid)

    # ---------- 2. Flask 登录 → token 指向 users.id ----------
    res = requests.post(FLASK + "/login", timeout=10,
                        json={"username": fu, "password": fp}).json()
    check("Flask 登录成功", res.get("code") == 200, res.get("message"))
    ftoken = (res.get("data") or {}).get("access_token")
    check("登录返回 access_token", bool(ftoken))
    if ftoken:
        info = requests.get(API + "/auth/info", headers={"Authorization": "Bearer " + ftoken},
                            timeout=10).json()
        d = info.get("data") or {}
        check("Flask token 可被业务接口识别（不再串号）",
              info.get("code") == OK and d.get("username") == fu,
              "info.username={} 期望={}".format(d.get("username"), fu))
        check("业务侧用户 id 与注册时返回一致", d.get("id") == xid,
              "期望 {} 实际 {}".format(xid, d.get("id")))
        # 业务数据归属正确：用该 token 建一条习惯，再查回来
        hr = requests.post(API + "/habit/create", headers={"Authorization": "Bearer " + ftoken},
                           timeout=10, json={"name": "串号验证习惯", "icon": "🌱",
                                             "remind_time": "08:00"}).json()
        check("Flask 账号可正常写入业务数据", hr.get("code") == OK, hr.get("message"))
        lr = requests.get(API + "/habit/list", headers={"Authorization": "Bearer " + ftoken},
                          timeout=10).json()
        names = [h.get("name") for h in ((lr.get("data") or {}).get("list")
                                         if isinstance(lr.get("data"), dict) else (lr.get("data") or []))]
        check("用 Flask token 能查回自己刚建的数据", "串号验证习惯" in names, names)

    # ---------- 3. 反向：FastAPI 注册 → Flask 登录 ----------
    gu, gp = rnd("b2r"), "Test@12345"
    requests.post(API + "/auth/register-username", timeout=10,
                  json={"username": gu, "password": gp})
    res = requests.post(FLASK + "/login", timeout=10,
                        json={"username": gu, "password": gp}).json()
    check("FastAPI 注册的账号也能在 Flask 登录（双向打通）",
          res.get("code") == 200, res.get("message"))

    # ---------- 4. 历史账号惰性补建：模拟旧数据（清掉绑定后登录） ----------
    try:
        import pymysql
        conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="123456",
                               database="ai_habit_partner", charset="utf8mb4", autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM user WHERE username=%s", (fu,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE user SET xuntu_user_id=NULL WHERE id=%s", (row[0],))
        conn.close()
        res = requests.post(FLASK + "/login", timeout=10,
                            json={"username": fu, "password": fp}).json()
        check("绑定被清空的历史账号登录时自动补建", res.get("code") == 200, res.get("message"))
        if res.get("code") == 200:
            t2 = (res.get("data") or {}).get("access_token")
            info = requests.get(API + "/auth/info", headers={"Authorization": "Bearer " + t2},
                                timeout=10).json()
            check("补建后业务身份仍正确", (info.get("data") or {}).get("username") == fu,
                  (info.get("data") or {}).get("username"))
    except Exception as e:
        print("  [SKIP] 历史账号惰性补建检查失败：{}".format(e))

    print()
    print("=" * 66)
    print("结果：PASS {} / FAIL {}".format(len(PASS), len(FAIL)))
    if FAIL:
        print("失败项：")
        for f in FAIL:
            print("  - " + f)
    print("=" * 66)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
