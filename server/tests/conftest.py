# -*- coding: utf-8 -*-
"""
后端测试配置 - pytest fixtures
"""
import sys
import os

# 将 server/app 加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def guest_token():
    """获取游客 token"""
    from app.services.auth_service import AuthService
    return AuthService.create_access_token(0, {"guest": True, "nickname": "测试游客"})


@pytest.fixture
def auth_headers(guest_token):
    """带游客 token 的请求头"""
    return {"Authorization": f"Bearer {guest_token}"}
