# -*- coding: utf-8 -*-
"""
四大新模块 全量接口验证脚本 (模块1/2/3/4 + 打卡联动)
依赖: 后端已运行于 127.0.0.1:8000; 使用一次性测试账号
运行: C:\\Users\\小青\\AppData\\Local\\Programs\\Python\\Python314\\python.exe migrations\\test_four_modules.py
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
TOKEN = ""  # 由命令行传入
PASSED = []
FAILED = []


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"code": e.code, "message": "http error"}


def check(name, resp, expect_data=True):
    ok = resp.get("code") == 200 and (not expect_data or resp.get("data") is not None)
    mark = "PASS" if ok else "FAIL"
    (PASSED if ok else FAILED).append(name)
    print(f"[{mark}] {name}" + ("" if ok else f" -> {json.dumps(resp, ensure_ascii=False)[:200]}"))
    return resp


def main():
    print("========== 模块1+4: 虚拟世界 ==========")
    roles = check("世界-AI角色列表", call("GET", "/world/ai-roles"))
    role_ids = [r["id"] for r in roles["data"]][:2]

    w = check("世界-创建(公开+2AI角色+自设角色)", call("POST", "/world/create", {
        "name": "星轨小筑", "description": "测试用的温柔小世界", "rules": "在这里每份坚持都会被看见",
        "is_public": 1, "role_ids": role_ids, "custom_roles": ["月见"], "checkin_target": 1
    }))
    world_id = w["data"]["id"]

    check("世界-公开列表", call("GET", "/world/list?tab=public"))
    check("世界-我的世界", call("GET", "/world/list?tab=mine"))
    d = check("世界-详情(成员/剧情/打卡数)", call("GET", f"/world/detail/{world_id}"))
    assert len(d["data"]["members"]) == 4, f"成员应为4(我+2AI+1自设), 实际{len(d['data']['members'])}"
    assert len(d["data"]["plots"]) == 3, "应有3段默认剧情"
    print(f"    成员{len(d['data']['members'])}个, 剧情{len(d['data']['plots'])}段")

    note = check("世界-用户发布笔记", call("POST", f"/world/note/{world_id}",
                                          {"content": "我的第一条世界笔记", "note_type": "normal"}))
    note_id = note["data"]["id"]
    c = check("世界-评论笔记(触发AI回复/互评)", call("POST", f"/world/comment/{note_id}",
                                                   {"content": "写得好!", "reply_to_id": 0}))
    n_ai_comments = sum(1 for x in c["data"]["comments"] if x["author_role_id"])
    assert n_ai_comments >= 1, "AI应至少回复1条"
    print(f"    本次新增评论{len(c['data']['comments'])}条, 其中AI {n_ai_comments} 条")

    check("世界-笔记流", call("GET", f"/world/notes/{world_id}"))
    check("世界-评论列表", call("GET", f"/world/comments/{note_id}"))
    check("世界-AI互动消息", call("GET", f"/world/ai-interactions/{world_id}"))
    check("世界-角色关系列表", call("GET", f"/world/relations/{world_id}"))

    print("========== 模块2: 日程提醒 ==========")
    s = check("日程-创建", call("POST", "/schedule/create", {
        "title": "晨间阅读", "description": "读10页书", "schedule_date": "2026-09-19",
        "start_time": "08:00", "end_time": "08:30", "habit_id": 0, "remind_minutes": 5
    }))
    sid = s["data"]["id"]
    check("日程-单日列表", call("GET", "/schedule/list?day=2026-09-19"))
    check("日程-整月列表", call("GET", "/schedule/list?month=2026-09"))
    check("日程-详情", call("GET", f"/schedule/detail/{sid}"))
    check("日程-更新", call("PUT", f"/schedule/update/{sid}", {"title": "晨间阅读(改)"}))
    check("日程-完成(未绑习惯)", call("POST", f"/schedule/complete/{sid}"))
    check("日程-提醒扫描", call("GET", "/schedule/remind/scan"))
    check("日程-删除", call("DELETE", f"/schedule/delete/{sid}"))

    # ===== 先建一个习惯(打卡联动/AI生成日程都要用) =====
    tpl = call("GET", "/habit/templates")
    t0 = tpl["data"][0]
    h = call("POST", "/habit/add", {"template_id": t0["id"]})
    if h.get("code") != 200 or not h.get("data"):
        h = call("POST", "/habit/create", {"name": "测试喝水", "target": "每天8杯", "difficulty": "easy"})
    hd = h["data"]
    habit_id = hd["id"] if isinstance(hd, dict) else hd
    (PASSED if habit_id else FAILED).append("习惯-添加成功")
    print(f"[{'PASS' if habit_id else 'FAIL'}] 习惯-添加成功 (id={habit_id})")

    check("日程-AI生成建议", call("POST", "/schedule/ai-generate", {"for_date": "2026-09-19"}))

    print("========== 模块3: 互动扭蛋 ==========")
    wa = check("扭蛋-钱包", call("GET", "/gacha/wallet"))
    assert wa["data"]["coin_balance"] >= 0, "钱包应可用(首次访问自动创建)"
    check("扭蛋-剧本列表(推荐)", call("GET", "/gacha/list?tab=recommend"))
    check("扭蛋-剧本列表(最热)", call("GET", "/gacha/list?tab=hot"))
    my_tpl = check("扭蛋-创建自定义剧本", call("POST", "/gacha/create", {
        "title": "深夜电台", "description": "睡前聊聊", "category": "emotion",
        "opening_text": "欢迎收听深夜电台~",
        "questions": [
            {"question": "今晚睡得早吗?", "options": ["早睡", "夜猫子"], "hint": "注意休息哦"},
            {"question": "想听什么歌?", "options": ["慢歌", "白噪音"], "hint": "都很好"}
        ]
    }))
    check("扭蛋-收藏自定义剧本", call("POST", f"/gacha/favorite/{my_tpl['data']['id']}"))
    check("扭蛋-收藏列表", call("GET", "/gacha/list?tab=favorite"))
    check("扭蛋-我创建的", call("GET", "/gacha/list?tab=mine"))

    draw = check("扭蛋-抽取(扣10币+建会话)", call("POST", "/gacha/draw", {"category": "companion"}))
    dr = draw["data"]
    balance_after = dr["coin_balance"]
    assert balance_after == wa["data"]["coin_balance"] - 10, f"扣币后应少10, 实际{balance_after}"
    qs = dr["questions"]
    assert len(qs) >= 1, "剧本应有问题"

    a = check("扭蛋-问答第1题", call("POST", "/gacha/answer", {
        "record_id": dr["record_id"], "question_index": 0, "answer": qs[0]["options"][0]
    }))
    if len(qs) > 1:
        check("扭蛋-问答第2题", call("POST", "/gacha/answer", {
            "record_id": dr["record_id"], "question_index": 1, "answer": qs[1]["options"][0]
        }))
    else:
        assert a["data"]["finished"], "单题剧本应直接完成"
    check("扭蛋-抽取记录", call("GET", "/gacha/records"))

    # 验证扭蛋对话写入聊天历史(数据互通)
    sess = call("GET", "/chat/sessions")
    ok = any("【扭蛋】" in (x.get("title") or "") for x in (sess.get("data") or []))
    (PASSED if ok else FAILED).append("扭蛋-对话进入聊天会话列表")
    print(f"[{'PASS' if ok else 'FAIL'}] 扭蛋-对话进入聊天会话列表")

    print("========== 打卡联动(模块1+3+4) ==========")
    ck = check("打卡-习惯打卡(触发联动)", call("POST", "/habit/checkin", {"habit_id": habit_id, "note": "联动测试"}))
    lk = ck["data"].get("linkage", {})
    assert lk.get("coin_awarded") == 10, f"打卡应发10扭蛋币, 实际{lk}"
    assert lk.get("worlds_affected", 0) >= 1, "打卡应波及至少1个世界"
    print(f"    联动结果: +{lk['coin_awarded']}币, 余额{lk['coin_balance']}, 影响{lk['worlds_affected']}个世界, 解锁{lk['plots_unlocked']}段剧情")

    wa2 = check("扭蛋-钱包(打卡后+10)", call("GET", "/gacha/wallet"))
    assert wa2["data"]["coin_balance"] >= 10, "打卡后钱包应有币"

    d2 = check("世界-详情(打卡反馈后)", call("GET", f"/world/detail/{world_id}"))
    assert d2["data"]["my_checkin_count"] >= 1, "世界内应记录到打卡反馈"
    unlocked = [p for p in d2["data"]["plots"] if p["unlocked"]]
    assert len(unlocked) >= 1, "checkin_target=1时打卡1次应解锁首段剧情"
    print(f"    世界内打卡{d2['data']['my_checkin_count']}次, 已解锁{len(unlocked)}段剧情")

    # 世界打卡总数联动
    notes2 = call("GET", f"/world/notes/{world_id}")
    has_feedback = any(n["note_type"] == "feedback" for n in notes2["data"])
    (PASSED if has_feedback else FAILED).append("世界-AI打卡反馈笔记已生成")
    print(f"[{'PASS' if has_feedback else 'FAIL'}] 世界-AI打卡反馈笔记已生成")

    print("========== 原有功能回归 ==========")
    check("回归-用户信息", call("GET", "/auth/info"))
    check("回归-习惯列表", call("GET", "/habit/today"))
    check("回归-聊天会话", call("GET", "/chat/sessions"))
    check("回归-朋友圈列表", call("GET", "/moment/list"))

    print(f"\n===== 结果: {len(PASSED)} PASS / {len(FAILED)} FAIL =====")
    if FAILED:
        print("失败项:", FAILED)
        raise SystemExit(1)


if __name__ == "__main__":
    import sys
    TOKEN = sys.argv[1]
    main()
