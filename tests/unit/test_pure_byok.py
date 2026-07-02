"""
Unit tests for backend/app/core/byok.py — BYOK pure validation.
"""
import pytest
from app.core.byok import is_agentpilot_enabled, validate_api_key_format, byok_status


class TestIsAgentpilotEnabled:

    def test_both_present(self):
        assert is_agentpilot_enabled("sk-abc", "ws-123") is True

    def test_missing_key(self):
        assert is_agentpilot_enabled(None, "ws-123") is False

    def test_missing_workspace(self):
        assert is_agentpilot_enabled("sk-abc", None) is False

    def test_both_missing(self):
        assert is_agentpilot_enabled(None, None) is False

    def test_empty_key(self):
        assert is_agentpilot_enabled("", "ws-123") is False

    def test_empty_workspace(self):
        assert is_agentpilot_enabled("sk-abc", "") is False


class TestValidateApiKeyFormat:

    def test_valid(self):
        r = validate_api_key_format("sk-abcdef12345678")
        assert r["valid"] is True
        assert r["reason"] is None

    def test_none(self):
        r = validate_api_key_format(None)
        assert r["valid"] is False
        assert "empty" in r["reason"]

    def test_empty_string(self):
        r = validate_api_key_format("")
        assert r["valid"] is False

    def test_too_short(self):
        r = validate_api_key_format("abc")
        assert r["valid"] is False
        assert "short" in r["reason"]

    def test_custom_min_length(self):
        r = validate_api_key_format("abc", min_length=3)
        assert r["valid"] is True

    def test_whitespace(self):
        r = validate_api_key_format("  sk-abcdef  ")
        assert r["valid"] is False
        assert "whitespace" in r["reason"]


class TestByokStatus:

    def test_fully_configured(self):
        s = byok_status("sk-x", "ws-1", "ark-y")
        assert s["agentpilot_enabled"] is True
        assert s["ark_configured"] is True
        assert s["fully_configured"] is True

    def test_no_ark(self):
        s = byok_status("sk-x", "ws-1", None)
        assert s["agentpilot_enabled"] is True
        assert s["ark_configured"] is False
        assert s["fully_configured"] is False

    def test_nothing_configured(self):
        s = byok_status(None, None, None)
        assert s["fully_configured"] is False
        assert s["agentpilot_enabled"] is False
        assert s["ark_configured"] is False
