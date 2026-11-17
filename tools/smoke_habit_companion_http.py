# -*- coding: utf-8 -*-
"""
习惯-伙伴融合 HTTP 冒烟（打真实端口，验证路由已注册 + 基本可用）

用法: python -u tools/smoke_habit_companion_http.py [端口]   # 默认 8010
说明: FastAPI 未注册的路由返回 HTTP 404 + {"detail":"Not Found"}；
      已注册但鉴权不通过返回 HTTP 200 + body.code=401。
      所以「不是 HTTP 404」即证明路由已加载。
"""
import random
import sys

import pymysql
import requests

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8010
BASE = f"http://127.0.0.1:{PORT}/api/v1"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  ({detail})" if detail else ""))


def main():
    # ---------- 注册临时用户拿 token ----------
    uname = "hc_%04d" % random.randint(1000, 9999)
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": uname, "password": "123456", "nickname": "冒烟"},
                      timeout=15)
    if r.status_code != 200:
        print("注册失败:", r.status_code, r.text[:200])
        return 1
    body = r.json()
    token = (body.get("data") or {}).get("access_token")
    if not token:
        print("拿不到 token:", body)
        return 1
    H = {"Authorization": f"Bearer {token}"}
    print(f"\n临时用户 {uname}（端口 {PORT}）\n")

    def call(method, path, **kw):
        try:
            resp = requests.request(method, BASE + path, headers=H, timeout=20, **kw)
        except Exception as e:
            return None, f"请求异常 {e}"
        return resp, ""

    try:
        # ============ 1. 创建习惯（带目标/期待感受） ============
        print("[1] 习惯创建与过往")
        resp, err = call("post", "/habit/create",
                         json={"name": "晚饭后散步", "target": "每天走20分钟",
                               "hope": "想让晚上不那么焦虑", "habit_type": "sport"})
        check("POST /habit/create 可用", resp is not None and resp.status_code == 200, err)
        d = (resp.json().get("data") or {}) if resp else {}
        hid = d.get("id")
        check("创建返回习惯 id", bool(hid), str(hid))
        check("创建返回伙伴口吻回复", bool(d.get("companion_reply")),
              (d.get("companion_reply") or "")[:30])

        # ============ 2. 新路由可达性 ============
        print("\n[2] 新增路由可达性")
        routes = [
            ("GET", f"/habit/{hid}/story"),
            ("POST", f"/habit/{hid}/pause"),
            ("POST", f"/habit/{hid}/resume"),
            ("POST", f"/habit/{hid}/missed"),
            ("GET", "/habit/companion/setting"),
            ("PUT", "/habit/companion/setting"),
            ("POST", "/habit/verbal/parse"),
            ("POST", "/habit/verbal/confirm"),
            ("GET", f"/habit/{hid}/world-fragment"),
            ("GET", "/stats/companion-review"),
            ("GET", "/stats/habits"),
            ("GET", "/archive/monthly-companion"),
            ("GET", "/memory/list?topic=habit"),
            ("POST", "/habit/encouragement"),
            ("POST", "/world/fragment/from-habit"),
        ]
        for m, p in routes:
            kw = {"json": {}} if m in ("POST", "PUT") else {}
            if p.endswith("/pause"):
                kw = {"json": {"reason": "最近有点累"}}
            if p.endswith("/resume") or p.endswith("/missed"):
                kw = {"json": {}}
            if p.endswith("/verbal/parse"):
                kw = {"json": {"text": "今天我把晚饭后散步做完了"}}
            if p.endswith("/verbal/confirm"):
                kw = {"json": {"habit_id": hid, "confirmed": False}}
            if p.endswith("/encouragement"):
                kw = {"json": {"habit_id": hid, "action": "checkin", "emotion": "tired"}}
            if p.endswith("/from-habit"):
                kw = {"json": {"world_id": 0, "habit_id": hid}}
            if p.endswith("/setting") and m == "PUT":
                kw = {"json": {"allow_habit_topic": 1}}
            resp, err = call(m.lower(), p, **kw)
            ok = resp is not None and resp.status_code == 200 and "code" in resp.json()
            check(f"{m} {p}", ok, err or ("" if not resp else f"HTTP {resp.status_code}"))

        # ============ 3. 关键业务字段 ============
        print("\n[3] 关键业务字段")
        resp, _ = call("get", "/habit/list")
        lst = (resp.json().get("data") or []) if resp else []
        check("/habit/list 含 is_paused 字段", bool(lst) and "is_paused" in lst[0],
              str(list((lst or [{}])[0].keys())[:8]))
        check("/habit/list 含 resume_count 字段", bool(lst) and "resume_count" in lst[0])

        resp, _ = call("get", f"/habit/{hid}/story")
        s = (resp.json().get("data") or {}) if resp else {}
        check("story 含 created_at", bool(s.get("created_at")), str(s.get("created_at")))
        check("story 含 timeline", isinstance(s.get("timeline"), list))
        check("story brief 不含完成率", "完成率" not in (s.get("brief") or ""), s.get("brief", ""))

        resp, _ = call("get", "/stats/companion-review?days=30")
        rev = ((resp.json().get("data") or {}).get("review") or "") if resp else ""
        check("companion-review 有复盘文本", bool(rev))
        check("复盘不含完成率/排名/打分",
              all(k not in rev for k in ("完成率", "排名", "评分", "得分")))

        resp, _ = call("get", "/archive/monthly-companion")
        ms = ((resp.json().get("data") or {}).get("story") or "") if resp else ""
        check("monthly-companion 有月度故事", bool(ms))
        check("月度故事不含排名打分", all(k not in ms for k in ("排名", "评分", "得分", "完成率")))

        resp, _ = call("get", "/memory/list?topic=habit")
        md = (resp.json().get("data") or {}) if resp else {}
        check("memory topic=habit 返回 list", "list" in md, str(list(md.keys())))
        check("习惯记忆非空", len(md.get("list") or []) > 0, str(len(md.get("list") or [])))

        # ============ 4. 话术红线（接口出口） ============
        print("\n[4] 话术红线")
        banned = ["加油", "努力", "坚持住", "别放弃", "不要半途而废", "再接再厉"]
        resp, _ = call("post", "/habit/encouragement",
                       json={"habit_id": hid, "action": "missed", "emotion": "sad"})
        msg = ((resp.json().get("data") or {}).get("message") or "") if resp else ""
        check("未完成鼓励语不含禁用词", not any(b in msg for b in banned), msg)

        # ============ 5. 暂停态行为（HTTP 层） ============
        print("\n[5] 暂停态行为")
        call("post", f"/habit/{hid}/pause", json={"reason": "先歇两天"})
        resp, _ = call("post", "/habit/checkin", json={"habit_id": hid})
        code = resp.json().get("code") if resp else None
        check("暂停后打卡被拒(code=409)", code == 409, f"code={code}")
        resp, _ = call("get", "/habit/list")
        lst = (resp.json().get("data") or []) if resp else []
        check("暂停习惯不出现在默认列表", all(x.get("id") != hid for x in lst))
        resp, _ = call("get", "/habit/list?include_paused=1")
        lst2 = (resp.json().get("data") or []) if resp else []
        check("include_paused=1 能查到", any(x.get("id") == hid for x in lst2),
              f"count={len(lst2)}")
        check("暂停项带 is_paused=1",
              any(x.get("id") == hid and x.get("is_paused") == 1 for x in lst2))
        call("post", f"/habit/{hid}/resume", json={})
        resp, _ = call("get", f"/habit/{hid}/story")
        s = (resp.json().get("data") or {}) if resp else {}
        # 注意：[2] 环节已暂停+重启过一次，此处是第 2 次，故断言 >=1 而非 ==1
        check("重启后 resume_count>0", (s.get("resume_count") or 0) >= 1,
              str(s.get("resume_count")))

        # ============ 6. 总开关 ============
        print("\n[6] 习惯话题总开关")
        call("put", "/habit/companion/setting", json={"allow_habit_topic": 0})
        resp, _ = call("get", "/habit/companion/setting")
        sd = (resp.json().get("data") or {}) if resp else {}
        check("关闭后读回 allow_habit_topic=0", sd.get("allow_habit_topic") == 0, str(sd))
        call("put", "/habit/companion/setting", json={"allow_habit_topic": 1})
        resp, _ = call("get", "/habit/companion/setting")
        sd = (resp.json().get("data") or {}) if resp else {}
        check("重新开启读回 1", sd.get("allow_habit_topic") == 1, str(sd))

    finally:
        # ---------- 清理临时用户 ----------
        print("\n[cleanup] 删除临时用户及其数据")
        try:
            conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="123456",
                                   database="ai_habit_partner", charset="utf8mb4", autocommit=True)
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s", (uname,))
            row = cur.fetchone()
            if row:
                uid = row[0]
                for t in ("ai_user_memories", "user_companion_settings", "checkin_items",
                          "checkins", "habits", "emotion_records", "habit_achievements"):
                    try:
                        cur.execute(f"DELETE FROM {t} WHERE user_id=%s", (uid,))
                    except Exception:
                        pass
                cur.execute("DELETE FROM users WHERE id=%s", (uid,))
            conn.close()
            print("  已清理")
        except Exception as e:
            print("  清理失败(可忽略):", e)

    print("\n" + "=" * 60)
    print(f"结果: PASS {len(PASS)} / FAIL {len(FAIL)}")
    for f in FAIL:
        print("  - " + f)
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
