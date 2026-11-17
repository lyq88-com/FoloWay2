# -*- coding: utf-8 -*-
"""陪伴角色体系统一验证（2026-10-27）

背景：陪伴模块原先只能选 ai_roles 的 4 个「人格类型」，与项目的 20 个具名角色
      （frontend/common/ai-characters.js 的 CHARACTERS）是两套数据。
      本次改造让陪伴记录记住 20 个具名角色：companion_records 新增 role_key / role_name，
      原 role_id 保留不动（世界模块与历史数据仍依赖 ai_roles）。

覆盖：
  1. 落库：role_key / role_name 正确写入并回读
  2. 兜底：不传 / 传空 → 默认 linxi
  3. 健壮：超长截断、首尾空格 trim、非字符串强转
  4. 兼容：旧客户端传字符串 role_id（如 'companion'）依然不 422
  5. 历史：老记录（role_key=''）不受影响，仍可正常读出

运行：
    cd liyeqing && python -u tools\\test_companion_role_key.py
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


def rnd(prefix="rolekey"):
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main():
    print("=" * 66)
    print("陪伴角色体系统一验证：companion_records.role_key")
    print("=" * 66)

    # ---------- 准备账号 ----------
    u, p = rnd(), "Test@12345"
    r = requests.post(API + "/auth/register-username",
                      json={"username": u, "password": p}, timeout=10).json()
    token = (r.get("data") or {}).get("access_token")
    if not token:
        r = requests.post(API + "/auth/login-username",
                          json={"username": u, "password": p}, timeout=10).json()
        token = (r.get("data") or {}).get("access_token")
    if not check("拿到业务侧 token", bool(token), r.get("message") if not token else ""):
        return 1
    H = {"Authorization": "Bearer " + token}

    def start(**kw):
        payload = {"scene_type": "study", "scene_name": "学习"}
        payload.update(kw)
        return requests.post(API + "/companion/start", json=payload, headers=H, timeout=10)

    def end(rec_id):
        return requests.post(API + "/companion/end", json={"record_id": rec_id},
                             headers=H, timeout=10)

    # ---------- 1. 正常落库 ----------
    print("\n[1] role_key 落库与回读")
    resp = start(role_key="yuki", role_name="Yuki")
    body = resp.json()
    d = body.get("data") or {}
    check("HTTP 200", resp.status_code == 200)
    check("业务码 200", body.get("code") == OK, body.get("message"))
    check("role_key 回显 yuki", d.get("role_key") == "yuki", d.get("role_key"))
    check("role_name 回显 Yuki", d.get("role_name") == "Yuki", d.get("role_name"))
    check("旧字段 role_id 仍在（兼容）", isinstance(d.get("role_id"), int), d.get("role_id"))
    rec_id = d.get("id")
    check("拿到记录 id", bool(rec_id), rec_id)

    # 从列表接口回读，确认是真的落库而不是只在响应里
    lst = requests.get(API + "/companion/records", headers=H, timeout=10).json()
    items = ((lst.get("data") or {}).get("list")) or []
    hit = next((x for x in items if x.get("id") == rec_id), None)
    check("列表接口能查到该记录", hit is not None)
    if hit:
        check("落库 role_key=yuki", hit.get("role_key") == "yuki", hit.get("role_key"))
        check("落库 role_name=Yuki", hit.get("role_name") == "Yuki", hit.get("role_name"))
    if rec_id:
        end(rec_id)

    # ---------- 2. 兜底默认 linxi ----------
    print("\n[2] 兜底：不传 / 传空 → linxi")
    resp = start()
    d = (resp.json().get("data") or {})
    check("不传 role_key → linxi", d.get("role_key") == "linxi", d.get("role_key"))
    if d.get("id"):
        end(d["id"])

    resp = start(role_key="   ", role_name="")
    d = (resp.json().get("data") or {})
    check("传空白 role_key → linxi", d.get("role_key") == "linxi", d.get("role_key"))
    if d.get("id"):
        end(d["id"])

    # ---------- 3. 健壮性 ----------
    print("\n[3] 健壮：trim / 截断 / 非字符串")
    resp = start(role_key="  nova  ", role_name=" Nova ")
    d = (resp.json().get("data") or {})
    check("首尾空格被 trim", d.get("role_key") == "nova", repr(d.get("role_key")))
    check("role_name 同样 trim", d.get("role_name") == "Nova", repr(d.get("role_name")))
    if d.get("id"):
        end(d["id"])

    long_key = "a" * 100
    resp = start(role_key=long_key)
    d = (resp.json().get("data") or {})
    check("超长 key 被截到 64", len(d.get("role_key") or "") == 64, len(d.get("role_key") or ""))
    if d.get("id"):
        end(d["id"])

    resp = start(role_key=12345)
    d = (resp.json().get("data") or {})
    check("数字型 role_key 不报错", resp.json().get("code") == OK, resp.json().get("message"))
    if d.get("id"):
        end(d["id"])

    # ---------- 4. 旧客户端兼容 ----------
    print("\n[4] 兼容：旧客户端传字符串 role_id")
    resp = start(role_id="companion")
    body = resp.json()
    check("字符串 role_id 不 422", body.get("code") == OK, body.get("message"))
    d = body.get("data") or {}
    check("这种情况下 role_key 兜底 linxi", d.get("role_key") == "linxi", d.get("role_key"))
    if d.get("id"):
        end(d["id"])

    # ---------- 5. 历史数据不受影响 ----------
    print("\n[5] 历史：老记录 role_key 为空不影响读出")
    lst = requests.get(API + "/companion/records", headers=H, timeout=10).json()
    items = ((lst.get("data") or {}).get("list")) or []
    check("记录列表接口正常", lst.get("code") == OK)
    check("每条记录都带 role_key 字段",
          all("role_key" in x for x in items), "共 {} 条".format(len(items)))

    # ---------- 汇总 ----------
    print("\n" + "=" * 66)
    print("PASS {} / FAIL {}".format(len(PASS), len(FAIL)))
    if FAIL:
        print("失败项：" + "、".join(FAIL))
    print("=" * 66)
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
