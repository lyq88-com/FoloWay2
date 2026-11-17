# -*- coding: utf-8 -*-
"""
【newfunc 增量-语音包】自动化测试 —— /api/newfunc/tts/**
覆盖：语音包列表与种子 / 用户默认音色 / 多语种合成(韩日粤川) / 缓存命中 /
音频流下载 / 语种不支持与异常回退兜底 / AI伙伴绑定与解析链 / 缓存统计清理 /
旧接口回归（newfunc既有接口 + openapi 路由计数）
运行：cd server && python tests/newfunc_tts_test.py（需先在 8000 端口启动后端）
"""
import json
import os
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"
TOKEN = ""
PASSED = 0
FAILED = []


def req(method, path, body=None, raw=False):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if TOKEN:
        r.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            payload = resp.read()
            if raw:
                return resp.status, payload, resp.headers.get("Content-Type", "")
            return resp.status, json.loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as e:
        payload = e.read()
        if raw:
            return e.code, payload, e.headers.get("Content-Type", "")
        try:
            return e.code, json.loads(payload.decode("utf-8"))
        except Exception:
            return e.code, {"message": payload.decode("utf-8", "ignore")}


def check(name, cond, detail=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"PASS | {name}")
    else:
        FAILED.append(name)
        print(f"FAIL | {name} | {detail}")


def login():
    global TOKEN
    status, res = req("POST", "/api/v1/auth/login-username",
                      {"username": "idea_test_a", "password": "test123456"})
    if status != 200 or not res.get("data", {}).get("access_token"):
        # 尝试注册再登录
        req("POST", "/api/v1/auth/register-username",
            {"username": "idea_test_a", "password": "test123456",
             "nickname": "测试用户"})
        status, res = req("POST", "/api/v1/auth/login-username",
                          {"username": "idea_test_a", "password": "test123456"})
    TOKEN = res["data"]["access_token"]
    return TOKEN


def main():
    print("=" * 60)
    print("【newfunc 增量-语音包】自动化测试")
    print("=" * 60)
    login()
    check("登录获取token", bool(TOKEN))

    # ---------- 1. 语音包列表与种子 ----------
    status, res = req("GET", "/api/newfunc/tts/voices")
    packs = res.get("data", [])
    codes = {p["pack_code"] for p in packs}
    check("语音包列表-200", status == 200)
    check("语音包列表-含原有普通话", "zh-default" in codes, codes)
    check("语音包列表-含韩语", "ko-kr" in codes, codes)
    check("语音包列表-含日语", "ja-jp" in codes, codes)
    check("语音包列表-含粤语", "zh-hk" in codes, codes)
    check("语音包列表-含东北话", "zh-liaoning" in codes, codes)
    check("语音包列表-含陕西话", "zh-shaanxi" in codes, codes)
    check("语音包列表-不含失效四川话", "zh-sichuan" not in codes, codes)
    ko = next(p for p in packs if p["pack_code"] == "ko-kr")
    check("韩语包含音色明细", len(ko["timbres"]) >= 2, ko["timbres"])

    # ---------- 2. 用户默认音色 ----------
    status, res = req("GET", "/api/newfunc/tts/setting")
    check("默认音色-读取200", status == 200 and res["data"].get("voice_id"), res)
    default_voice = res["data"]["voice_id"]
    status, res = req("POST", "/api/newfunc/tts/setting",
                      {"voice_id": "ko-KR-SunHiNeural"})
    check("默认音色-设为韩语", status == 200
          and res["data"]["voice_id"] == "ko-KR-SunHiNeural", res)
    status, res = req("POST", "/api/newfunc/tts/setting",
                      {"voice_id": "XX-FAKE-Neural"})
    check("默认音色-非法音色返回404码", status == 200 and res.get("code") == 404, res)
    # 测试后复位默认（幂等）
    req("POST", "/api/newfunc/tts/setting", {"voice_id": default_voice})

    # ---------- 3. 多语种合成 ----------
    samples = {
        "ko-kr": ("ko-KR-SunHiNeural", "안녕하세요, 테스트입니다."),
        "ja-jp": ("ja-JP-NanamiNeural", "こんにちは、テストです。"),
        "zh-hk": ("zh-HK-HiuMaanNeural", "你好呀，今日天气幾好。"),
        "zh-liaoning": ("zh-CN-liaoning-XiaobeiNeural", "哎呀妈呀，老好使了。"),
        "zh-shaanxi": ("zh-CN-shaanxi-XiaoniNeural", "嘹咋咧，今儿个天气真好。"),
    }
    first_key = {}
    for code, (vid, text) in samples.items():
        status, res = req("POST", "/api/newfunc/tts/synthesize",
                          {"text": text, "voice_id": vid})
        d = res.get("data", {})
        check(f"合成-{code}-200", status == 200, res)
        check(f"合成-{code}-音色正确", d.get("voice_id") == vid, d.get("voice_id"))
        check(f"合成-{code}-未回退", d.get("fallback") is False, d.get("fallback_reason"))
        check(f"合成-{code}-有audio_url", bool(d.get("audio_url")), d)
        first_key[code] = d.get("cache_key")

    # ---------- 4. 缓存命中（同文本同音色不重复请求） ----------
    vid, text = samples["ko-kr"]
    status, res = req("POST", "/api/newfunc/tts/synthesize",
                      {"text": text, "voice_id": vid})
    d = res.get("data", {})
    check("缓存-重复请求命中", d.get("cached") is True, d)
    check("缓存-同一cache_key", d.get("cache_key") == first_key["ko-kr"], d)

    # ---------- 5. 音频流下载 ----------
    status, payload, ctype = req("GET",
                                 f"/api/newfunc/tts/audio/{first_key['ko-kr']}",
                                 raw=True)
    check("音频下载-200", status == 200)
    check("音频下载-audio/mpeg", ctype.startswith("audio/mpeg"), ctype)
    check("音频下载-字节数>1000", len(payload) > 1000, len(payload))
    status, res = req("GET", "/api/newfunc/tts/audio/notexistkey000000")
    check("音频下载-不存在返回404码", res.get("code") == 404, res)

    # ---------- 6. 兜底回退 ----------
    status, res = req("POST", "/api/newfunc/tts/synthesize",
                      {"text": "回退测试文本", "voice_id": "xx-XX-FakeNeural"})
    d = res.get("data", {})
    check("兜底-不支持语种回退成功", status == 200 and d.get("fallback") is True, d)
    check("兜底-回退到默认语音", d.get("voice_id") == default_voice, d.get("voice_id"))
    check("兜底-有fallback_reason", bool(d.get("fallback_reason")), d)
    # bot 专属绑定音色解析
    status, res = req("POST", "/api/newfunc/bots",
                      {"name": "语音测试伙伴", "avatar": "🎙️",
                       "personality": "测试", "speak_style": "测试"})
    bot_id = res.get("data", {}).get("id")
    check("伙伴-创建成功", bool(bot_id), res)
    if bot_id:
        status, res = req("POST", f"/api/newfunc/tts/bots/{bot_id}/voice",
                          {"voice_id": "ja-JP-KeitaNeural"})
        check("伙伴-绑定日语音色", status == 200
              and res["data"]["bound_voice_id"] == "ja-JP-KeitaNeural", res)
        status, res = req("POST", "/api/newfunc/tts/synthesize",
                          {"text": "伙伴专属语音解析测试", "bot_id": bot_id})
        check("伙伴-合成走专属音色", res["data"]["voice_id"] == "ja-JP-KeitaNeural"
              and res["data"]["resolved_source"] == "bot_binding", res.get("data"))
        status, res = req("POST", "/api/newfunc/tts/synthesize",
                          {"text": "显式覆盖伙伴语音", "bot_id": bot_id,
                           "voice_id": "zh-HK-HiuMaanNeural"})
        check("伙伴-显式指定优先级最高", res["data"]["voice_id"] == "zh-HK-HiuMaanNeural", res.get("data"))
        status, res = req("DELETE", f"/api/newfunc/tts/bots/{bot_id}/voice")
        check("伙伴-解绑成功", status == 200, res)
        status, res = req("POST", "/api/newfunc/tts/synthesize",
                          {"text": "解绑后回退用户默认", "bot_id": bot_id})
        check("伙伴-解绑后回退默认", res["data"]["resolved_source"] == "user_setting", res.get("data"))
        status, res = req("GET", "/api/newfunc/tts/bots/99999999/voice")
        check("伙伴-不存在bot回退用户默认", status == 200
              and res["data"]["source"] == "user_setting", res)
        # 清理测试伙伴
        req("DELETE", f"/api/newfunc/bots/{bot_id}")

    # ---------- 7. 缓存统计与清理 ----------
    status, res = req("GET", "/api/newfunc/tts/cache/stats")
    n = res.get("data", {}).get("count", 0)
    check("缓存-统计有数据", status == 200 and n > 0, res)
    status, res = req("POST", "/api/newfunc/tts/cache/clear")
    check("缓存-清理成功", status == 200 and res["data"]["cleared"] == n, res)
    status, res = req("GET", "/api/newfunc/tts/cache/stats")
    check("缓存-清空后为0", res.get("data", {}).get("count") == 0, res)

    # ---------- 8. 旧接口回归（原有功能不受影响） ----------
    status, res = req("GET", "/api/newfunc/push/setting")
    check("回归-推送设置200", status == 200, res)
    status, res = req("GET", "/api/newfunc/bots")
    check("回归-伙伴列表200", status == 200, res)
    status, res = req("GET", "/api/newfunc/diary/day?date=2026-11-09")
    check("回归-情绪日记200", status == 200, res)
    status, res = req("GET", "/api/v1/habit/templates")
    check("回归-旧习惯模板接口200", status == 200, res)
    with urllib.request.urlopen(BASE + "/openapi.json", timeout=30) as r:
        paths = json.loads(r.read().decode("utf-8"))["paths"]
    tts_paths = [p for p in paths if "/api/newfunc/tts" in p]
    check("openapi-TTS路由已注册", len(tts_paths) >= 7, tts_paths)
    old_voice_paths = [p for p in paths if "voice" in p and "/api/newfunc" not in p]
    check("openapi-旧语音接口仍在", len(old_voice_paths) >= 1, old_voice_paths)

    # ---------- 汇总 ----------
    print("=" * 60)
    print(f"SUMMARY: PASS={PASSED} FAIL={len(FAILED)}")
    if FAILED:
        print("Failed:", FAILED)
    print("=" * 60)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
