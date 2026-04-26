import pytest
from src.shared.security import hash_password, verify_password, create_access_token, decode_access_token


class TestPasswordHashing:
    def test_hash_password_produces_different_hash_each_time(self):
        """bcrypt should produce unique hashes due to salt."""
        hash1 = hash_password("testpassword")
        hash2 = hash_password("testpassword")
        assert hash1 != hash2

    def test_verify_password_returns_true_for_correct_password(self):
        password = "securepassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self):
        password = "securepassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_longer_than_original_password(self):
        """bcrypt hashes are typically 60 characters."""
        hashed = hash_password("password")
        assert len(hashed) >= 60


class TestJWTTokens:
    def test_create_and_decode_token(self):
        user_id = 123
        token = create_access_token(user_id)
        assert token is not None

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["user_id"] == user_id

    def test_decode_invalid_token_returns_none(self):
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_token_contains_expiration(self):
        token = create_access_token(1)
        payload = decode_access_token(token)
        assert "exp" in payload