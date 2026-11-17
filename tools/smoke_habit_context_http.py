# -*- coding: utf-8 -*-
"""
打卡上下文延续 HTTP 冒烟（打真实端口，验证 /chat/send 的习惯会话模式真的生效）

用法: python -u tools/smoke_habit_context_http.py [端口]   # 默认 8000

覆盖：
  1. 打卡 → 返回 chat_context
  2. /chat/send 带 habit_id → SSE 回传 habit_context.active=true
  3. 同一会话继续发（不带 habit_id）→ 仍然挂载（需求5 持久化）
  4. 说「先不说这个了」→ habit_context.exited=true
  5. 总开关关闭 → 不再挂载
  6. POST /habit/topic/mute → 返回固定退出回应
"""
import io
import json
import os
import random
import sys

# Windows 控制台默认 GBK，AI 回复里带 emoji 会直接 UnicodeEncodeError 崩掉整个冒烟。
# 这里强制 stdout 用 UTF-8（Python 3.7+ 支持）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import requests  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}/api/v1"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"  ({detail})" if detail else ""))


def send_chat(H, content, habit_id=None, session_id=None):
    """发一条消息，返回 (session_id, habit_context, 回复文本)"""
    payload = {"content": content, "role_type": "gentle", "dialogue_style": "gentle"}
    if habit_id is not None:
        payload["habit_id"] = habit_id
    if session_id:
        payload["session_id"] = session_id
    resp = requests.post(f"{BASE}/chat/send", headers=H, json=payload,
                         timeout=60, stream=True)
    sid, hc, text = None, None, ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        try:
            evt = json.loads(line[5:].strip())
        except Exception:
            continue
        if evt.get("session_id"):
            sid = evt["session_id"]
        elif evt.get("habit_context"):
            hc = evt["habit_context"]
        elif evt.get("content"):
            text += evt["content"]
    return sid, hc, text


def main():
    uname = "hcx_%04d" % random.randint(1000, 9999)
    r = requests.post(f"{BASE}/auth/register-username",
                      json={"username": uname, "password": "123456", "nickname": "上下文冒烟"},
                      timeout=15)
    body = r.json()
    token = (body.get("data") or {}).get("access_token")
    if not token:
        print("拿不到 token:", body)
        return 1
    H = {"Authorization": f"Bearer {token}"}
    print(f"\n临时用户 {uname}（端口 {PORT}）\n")

    # ---------- 1. 创建习惯 + 打卡 ----------
    print("[1] 打卡返回 chat_context")
    resp = requests.post(f"{BASE}/habit/create", headers=H,
                         json={"name": "睡前读书", "target": "每天读20页",
                               "hope": "想睡前不看手机", "habit_type": "study"}, timeout=15)
    hid = (resp.json().get("data") or {}).get("id")
    check("创建习惯成功", bool(hid), str(hid))

    resp = requests.post(f"{BASE}/habit/checkin", headers=H,
                        json={"habit_id": hid, "emotion": "tired", "note": "眼睛都睁不开了"}, timeout=15)
    d = (resp.json().get("data") or {})
    ctx = d.get("chat_context") or {}
    check("打卡返回 chat_context", bool(ctx), str(ctx)[:80])
    check("chat_context.habit_id 正确", ctx.get("habit_id") == hid)
    check("chat_context.event = habit_checkin", ctx.get("event") == "habit_checkin", str(ctx.get("event")))
    check("chat_context.emotion = tired", ctx.get("emotion") == "tired", str(ctx.get("emotion")))
    check("打卡回复结合疲惫情绪",
          any(w in (d.get("companion_reply") or "") for w in ("累", "疲惫", "辛苦", "撑", "歇")),
          (d.get("companion_reply") or "")[:30])

    # ---------- 2. 带 habit_id 进入习惯会话模式 ----------
    print("\n[2] /chat/send 带 habit_id → 进入习惯会话模式")
    sid, hc, text = send_chat(H, "今天真的好累", habit_id=hid)
    check("拿到 session_id", bool(sid), str(sid))
    check("回传 habit_context", hc is not None, str(hc))
    check("habit_context.active = true", bool((hc or {}).get("active")), str(hc))
    check("habit_context.habit_name 正确", (hc or {}).get("habit_name") == "睡前读书")
    check("这条会话记住了本次打卡事件", (hc or {}).get("event") == "habit_checkin", str((hc or {}).get("event")))
    check("AI 有回复", bool(text.strip()), text[:30])

    # ---------- 3. 不传 habit_id 也要保持（需求5 持久化） ----------
    print("\n[3] 同一会话继续发：上下文自动延续")
    sid2, hc2, text2 = send_chat(H, "我最近压力好大", session_id=sid)
    check("仍是同一会话", sid2 == sid, f"{sid2} vs {sid}")
    check("不传 habit_id 也保持挂载", bool((hc2 or {}).get("active")), str(hc2))
    check("挂载的还是同一条习惯", (hc2 or {}).get("habit_id") == hid)

    # ---------- 4. 说出退出指令 ----------
    print("\n[4] 说「先不说这个了」→ 立刻退出并静默")
    sid3, hc3, text3 = send_chat(H, "先不说这个了", session_id=sid)
    check("habit_context.exited = true", bool((hc3 or {}).get("exited")), str(hc3))
    check("退出后不再挂载", not (hc3 or {}).get("active"))

    # 退出后再发普通消息，不应自动回到习惯话题
    sid4, hc4, _ = send_chat(H, "今天天气不错", session_id=sid)
    check("退出之后普通闲聊不再挂习惯", not (hc4 or {}).get("active"), str(hc4))

    # ---------- 5. 总开关关闭 ----------
    print("\n[5] 总开关关闭 → 任何情况都不挂习惯上下文")
    requests.put(f"{BASE}/habit/companion/setting", headers=H,
                 json={"allow_habit_topic": False}, timeout=15)
    sid5, hc5, _ = send_chat(H, "我不想看书了", habit_id=hid, session_id=sid)
    check("开关关闭后 habit_context 未激活", not (hc5 or {}).get("active"), str(hc5))
    check("原因标注为 topic_switch_off", (hc5 or {}).get("reason") == "topic_switch_off",
          str((hc5 or {}).get("reason")))

    # 重新打开，验证可恢复
    requests.put(f"{BASE}/habit/companion/setting", headers=H,
                 json={"allow_habit_topic": True}, timeout=15)
    sid6, hc6, _ = send_chat(H, "那本书还挺好看的", habit_id=hid, session_id=sid)
    check("重新打开后又能挂载", bool((hc6 or {}).get("active")), str(hc6))

    # ---------- 6. 静默接口 ----------
    print("\n[6] /habit/topic/mute")
    resp = requests.post(f"{BASE}/habit/topic/mute", headers=H,
                         json={"habit_id": hid, "days": 3}, timeout=15)
    md = (resp.json().get("data") or {})
    check("mute 接口可用", bool(md), str(md)[:80])
    check("mute 返回固定退出回应", md.get("reply") == "好，那我们先不说这个啦。", str(md.get("reply")))
    sid7, hc7, _ = send_chat(H, "再聊聊看书吧", session_id=sid)
    check("静默期内不自动沿用（未被主动挂载）", not (hc7 or {}).get("active"), str(hc7))
    requests.post(f"{BASE}/habit/topic/unmute", headers=H, json={"habit_id": hid}, timeout=15)

    print(f"\n结果: PASS {len(PASS)} / FAIL {len(FAIL)}")
    for f in FAIL:
        print("  - " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
