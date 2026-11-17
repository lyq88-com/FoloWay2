# -*- coding: utf-8 -*-
"""
认证 API 测试 - 健康检查/游客登录/Token验证
"""
import pytest


class TestHealthCheck:
    """健康检查"""

    def test_health(self, client):
        """GET /health 返回 200"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"

    def test_root(self, client):
        """GET / 返回 API 信息"""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert "endpoints" in data["data"]


class TestGuestLogin:
    """游客登录"""

    def test_guest_login_success(self, client):
        """POST /api/v1/auth/guest 游客登录成功"""
        resp = client.post("/api/v1/auth/guest", json={"nickname": "测试用户"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert "token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"
        assert data["data"]["user_info"]["is_guest"] is True
        assert data["data"]["user_info"]["nickname"] == "测试用户"

    def test_guest_login_default_nickname(self, client):
        """游客登录不传昵称使用默认值"""
        resp = client.post("/api/v1/auth/guest", json={"nickname": "游客"})
        assert resp.status_code == 200
        assert resp.json()["data"]["user_info"]["nickname"] == "游客"

    def test_auth_info_with_guest_token(self, client, auth_headers):
        """GET /api/v1/auth/info 游客 token 获取用户信息"""
        resp = client.get("/api/v1/auth/info", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["is_guest"] is True
        assert data["data"]["id"] == 0

    def test_auth_info_without_token(self, client):
        """无 token 访问需认证接口返回 401"""
        resp = client.get("/api/v1/auth/info")
        assert resp.status_code == 401

    def test_auth_info_with_invalid_token(self, client):
        """无效 token 返回 401"""
        resp = client.get(
            "/api/v1/auth/info",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert resp.status_code == 401
