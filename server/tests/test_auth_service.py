# -*- coding: utf-8 -*-
"""
JWT认证服务测试 - Token生成/验证/密码哈希
"""
import pytest
from app.services.auth_service import AuthService


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_access_token(self):
        """生成 access token"""
        token = AuthService.create_access_token(123, {"phone": "13800138000"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_valid_token(self):
        """解码有效 token"""
        token = AuthService.create_access_token(456, {"nickname": "测试"})
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "456"
        assert payload["type"] == "access"
        assert payload["nickname"] == "测试"

    def test_get_user_id_from_token(self):
        """从 token 获取用户ID"""
        token = AuthService.create_access_token(789)
        user_id = AuthService.get_user_id_from_token(token)
        assert user_id == 789

    def test_guest_user_id_zero(self):
        """游客 user_id=0 的 token"""
        token = AuthService.create_access_token(0, {"guest": True})
        user_id = AuthService.get_user_id_from_token(token)
        assert user_id == 0  # 不能被 falsy 过滤

    def test_decode_invalid_token(self):
        """解码无效 token 返回 None"""
        result = AuthService.decode_token("invalid.token.here")
        assert result is None

    def test_decode_none_token(self):
        """解码 None 返回 None"""
        result = AuthService.decode_token(None)
        assert result is None

    def test_get_user_id_invalid_token(self):
        """无效 token 获取用户ID返回 None"""
        result = AuthService.get_user_id_from_token("invalid_token")
        assert result is None

    def test_admin_token_type(self):
        """管理员 token 类型为 admin"""
        token = AuthService.create_admin_token(1, "super_admin")
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["type"] == "admin"
        assert payload["role"] == "super_admin"

    def test_admin_token_not_access_type(self):
        """管理员 token 不能作为 access token 使用"""
        token = AuthService.create_admin_token(1)
        # get_user_id_from_token 只接受 type=access 的 token
        user_id = AuthService.get_user_id_from_token(token)
        assert user_id is None


class TestPasswordHash:
    """密码哈希测试"""

    def test_hash_password(self):
        """密码哈希"""
        hashed = AuthService.hash_password("test123456")
        assert hashed is not None
        assert hashed != "test123456"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """验证正确密码"""
        hashed = AuthService.hash_password("mypassword")
        assert AuthService.verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        """验证错误密码"""
        hashed = AuthService.hash_password("mypassword")
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_verify_empty_hash(self):
        """验证空哈希"""
        assert AuthService.verify_password("test", "") is False
        assert AuthService.verify_password("test", None) is False

    def test_different_passwords_different_hashes(self):
        """不同密码生成不同哈希"""
        h1 = AuthService.hash_password("password1")
        h2 = AuthService.hash_password("password2")
        assert h1 != h2
