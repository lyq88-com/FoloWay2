# -*- coding: utf-8 -*-
"""
简易测试运行器 - 不依赖 pytest, 直接运行核心测试
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crisis_service import CrisisService
from app.services.emotion_service import EmotionService
from app.services.auth_service import AuthService

passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        failed += 1


# ========== CrisisService 测试 ==========
print("\n=== CrisisService ===")

def crisis_normal():
    r = CrisisService.check_crisis("今天天气真好")
    assert r["level"] == "normal", f"expected normal, got {r['level']}"

def crisis_empty():
    r = CrisisService.check_crisis("")
    assert r["level"] == "normal"

def crisis_critical():
    r = CrisisService.check_crisis("我不想活了")
    assert r["level"] == "critical"
    assert len(r["resources"]) >= 3

def crisis_negative():
    r = CrisisService.check_crisis("我好难过")
    assert r["level"] == "high"
    assert len(r["message"]) > 10

def crisis_keywords():
    for kw in ["自杀", "想死", "不想活", "结束生命", "绝望", "解脱"]:
        r = CrisisService.check_crisis(f"真的很{kw}")
        assert r["level"] == "critical", f"keyword '{kw}' should trigger critical"

def crisis_resources():
    resources = CrisisService.get_resources()
    assert len(resources) >= 3
    assert any(r["phone"] == "400-161-9995" for r in resources)

def crisis_long_text():
    long = "今天工作很忙，压力很大，真的撑不下去了，不想活了"
    r = CrisisService.check_crisis(long)
    assert r["level"] == "critical"

test("crisis_normal", crisis_normal)
test("crisis_empty", crisis_empty)
test("crisis_critical", crisis_critical)
test("crisis_negative", crisis_negative)
test("crisis_keywords", crisis_keywords)
test("crisis_resources", crisis_resources)
test("crisis_long_text", crisis_long_text)


# ========== EmotionService 测试 ==========
print("\n=== EmotionService ===")

def emotion_happy():
    r = EmotionService.analyze_emotion("今天好开心啊")
    assert r["emotion"] == "happy"
    assert r["valence"] == "positive"

def emotion_sad():
    r = EmotionService.analyze_emotion("好难过，什么都不顺利")
    assert r["emotion"] == "sad"
    assert r["valence"] == "negative"

def emotion_angry():
    r = EmotionService.analyze_emotion("气死我了，太烦了")
    assert r["emotion"] == "angry"

def emotion_tired():
    r = EmotionService.analyze_emotion("今天好累，疲惫不堪")
    assert r["emotion"] == "tired"

def emotion_empty():
    r = EmotionService.analyze_emotion("")
    assert r["emotion"] == "neutral"

def emotion_none():
    r = EmotionService.analyze_emotion(None)
    assert r["emotion"] == "neutral"

def emotion_trend():
    from datetime import datetime
    today = datetime.now().date().strftime("%Y-%m-%d")
    records = [
        {"record_date": today, "emotion": "happy", "intensity": 8},
        {"record_date": today, "emotion": "sad", "intensity": 3},
    ]
    r = EmotionService.get_emotion_trend(records, days=7)
    assert len(r["labels"]) == 7
    assert r["intensities"][-1] == 5.5

def emotion_triggers():
    records = [
        {"emotion": "sad", "intensity": 7, "tags": ["工作", "压力"]},
        {"emotion": "angry", "intensity": 8, "tags": ["工作"]},
        {"emotion": "happy", "intensity": 6, "tags": ["运动"]},
    ]
    r = EmotionService.get_trigger_analysis(records)
    assert r[0]["tag"] == "工作"
    assert r[0]["count"] == 2
    assert r[0]["negative_ratio"] == 100.0

def emotion_labels():
    for emo in ["happy", "excited", "calm", "sad", "angry", "tired"]:
        assert emo in EmotionService.EMOTION_LABELS

test("emotion_happy", emotion_happy)
test("emotion_sad", emotion_sad)
test("emotion_angry", emotion_angry)
test("emotion_tired", emotion_tired)
test("emotion_empty", emotion_empty)
test("emotion_none", emotion_none)
test("emotion_trend", emotion_trend)
test("emotion_triggers", emotion_triggers)
test("emotion_labels", emotion_labels)


# ========== AuthService 测试 ==========
print("\n=== AuthService ===")

def auth_create_token():
    token = AuthService.create_access_token(123, {"phone": "13800138000"})
    assert token is not None
    assert len(token) > 50

def auth_decode_token():
    token = AuthService.create_access_token(456, {"nickname": "测试"})
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "456"
    assert payload["type"] == "access"

def auth_get_user_id():
    token = AuthService.create_access_token(789)
    user_id = AuthService.get_user_id_from_token(token)
    assert user_id == 789

def auth_guest_zero():
    token = AuthService.create_access_token(0, {"guest": True})
    user_id = AuthService.get_user_id_from_token(token)
    assert user_id == 0  # 不能被 falsy 过滤

def auth_invalid_token():
    assert AuthService.decode_token("invalid") is None
    assert AuthService.get_user_id_from_token("invalid") is None

def auth_admin_token():
    token = AuthService.create_admin_token(1, "admin")
    payload = AuthService.decode_token(token)
    assert payload["type"] == "admin"
    assert payload["role"] == "admin"
    # admin token 不能作为 access token
    assert AuthService.get_user_id_from_token(token) is None

def auth_password_hash():
    hashed = AuthService.hash_password("test123")
    assert hashed != "test123"
    assert AuthService.verify_password("test123", hashed) is True
    assert AuthService.verify_password("wrong", hashed) is False

test("auth_create_token", auth_create_token)
test("auth_decode_token", auth_decode_token)
test("auth_get_user_id", auth_get_user_id)
test("auth_guest_zero", auth_guest_zero)
test("auth_invalid_token", auth_invalid_token)
test("auth_admin_token", auth_admin_token)
test("auth_password_hash", auth_password_hash)


# ========== FastAPI 端点测试 ==========
print("\n=== FastAPI Endpoints ===")

def api_health():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["status"] == "healthy"

def api_guest_login():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.post("/api/v1/auth/guest", json={"nickname": "测试游客"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "token" in data["data"]
    assert data["data"]["user_info"]["is_guest"] is True

def api_auth_info_guest():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    # 先登录获取 token
    resp = client.post("/api/v1/auth/guest", json={"nickname": "测试"})
    token = resp.json()["data"]["token"]
    # 用 token 获取信息
    resp2 = client.get("/api/v1/auth/info", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["data"]["is_guest"] is True
    assert data["data"]["id"] == 0

def api_auth_info_no_token():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.get("/api/v1/auth/info")
    assert resp.status_code == 401

test("api_health", api_health)
test("api_guest_login", api_guest_login)
test("api_auth_info_guest", api_auth_info_guest)
test("api_auth_info_no_token", api_auth_info_no_token)


# ========== 结果 ==========
print(f"\n{'='*50}")
print(f"  Total: {passed + failed}  |  Passed: {passed}  |  Failed: {failed}")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
