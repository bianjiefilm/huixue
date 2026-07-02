"""
Unit tests for backend/app/core/security_pure.py — pure security helpers.
"""
import pytest
from datetime import datetime, timedelta
from app.core.security_pure import (
    build_token_payload,
    extract_token_fields,
    is_token_payload_valid,
    build_user_response,
)


FIXED_NOW = datetime(2026, 4, 16, 12, 0, 0)


class TestBuildTokenPayload:

    def test_default_expiry(self):
        p = build_token_payload({"sub": "alice"}, now=FIXED_NOW)
        assert p["sub"] == "alice"
        assert p["exp"] == FIXED_NOW + timedelta(minutes=15)

    def test_custom_expiry(self):
        delta = timedelta(hours=8)
        p = build_token_payload({"user_id": 1}, expires_delta=delta, now=FIXED_NOW)
        assert p["exp"] == FIXED_NOW + delta

    def test_does_not_mutate_input(self):
        original = {"sub": "bob"}
        build_token_payload(original, now=FIXED_NOW)
        assert "exp" not in original

    def test_preserves_extra_fields(self):
        p = build_token_payload({"sub": "x", "role": "admin"}, now=FIXED_NOW)
        assert p["role"] == "admin"


class TestExtractTokenFields:

    def test_full_payload(self):
        r = extract_token_fields({"user_id": 1, "sub": "alice", "role": "teacher"})
        assert r == {"user_id": 1, "username": "alice", "role": "teacher"}

    def test_partial_payload(self):
        r = extract_token_fields({"sub": "bob"})
        assert r["user_id"] is None
        assert r["username"] == "bob"
        assert r["role"] is None

    def test_empty_payload(self):
        r = extract_token_fields({})
        assert r["user_id"] is None
        assert r["username"] is None


class TestIsTokenPayloadValid:

    def test_user_id_only(self):
        assert is_token_payload_valid({"user_id": 1}) is True

    def test_sub_only(self):
        assert is_token_payload_valid({"sub": "alice"}) is True

    def test_both(self):
        assert is_token_payload_valid({"user_id": 1, "sub": "alice"}) is True

    def test_neither(self):
        assert is_token_payload_valid({"role": "admin"}) is False

    def test_empty(self):
        assert is_token_payload_valid({}) is False


class TestBuildUserResponse:

    def test_basic(self):
        r = build_user_response(4, "teacher1", "t@example.com", "teacher", False, True)
        assert r["id"] == 4
        assert r["user_id"] == 4
        assert r["username"] == "teacher1"
        assert r["email"] == "t@example.com"
        assert r["roles"] == ["teacher"]
        assert r["is_superuser"] is False
        assert r["is_active"] is True

    def test_admin(self):
        r = build_user_response(1, "admin", None, "admin", True, True)
        assert r["roles"] == ["admin"]
        assert r["is_superuser"] is True
        assert r["email"] is None
