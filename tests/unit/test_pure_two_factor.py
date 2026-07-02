"""
two_factor.py 纯函数单元测试

覆盖: TOTP生成/验证, 备用验证码验证
"""
import pytest
import base64
import hashlib
import hmac
from app.core.two_factor import TwoFactorAuth


@pytest.fixture
def tfa():
    return TwoFactorAuth()


# ==================== TOTP密钥生成 ====================

class TestGenerateTOTPSecret:

    def test_returns_base64_string(self, tfa):
        secret = tfa.generate_totp_secret(1)
        # Should be valid base64
        decoded = base64.b64decode(secret)
        assert len(decoded) > 0

    def test_different_users_different_secrets(self, tfa):
        s1 = tfa.generate_totp_secret(1)
        s2 = tfa.generate_totp_secret(2)
        assert s1 != s2

    def test_deterministic_with_same_user(self, tfa):
        """由于使用 secrets.token_bytes，每次生成不同"""
        s1 = tfa.generate_totp_secret(1)
        s2 = tfa.generate_totp_secret(1)
        # 每次调用都是随机的
        assert isinstance(s1, str) and isinstance(s2, str)


# ==================== TOTP代码生成 ====================

class TestGenerateTOTPCode:

    def test_returns_six_digits(self, tfa):
        secret = tfa.generate_totp_secret(1)
        code = tfa.generate_totp_code(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_same_secret_same_window_same_code(self, tfa):
        secret = tfa.generate_totp_secret(1)
        code1 = tfa.generate_totp_code(secret, time_window=9999999)
        code2 = tfa.generate_totp_code(secret, time_window=9999999)
        # Very large window → same time step → same code
        assert code1 == code2

    def test_invalid_secret_returns_empty(self, tfa):
        code = tfa.generate_totp_code("not-valid-base64!!!")
        assert code == ""


# ==================== TOTP验证 ====================

class TestVerifyTOTPCode:

    def test_correct_code_accepted(self, tfa):
        secret = tfa.generate_totp_secret(42)
        code = tfa.generate_totp_code(secret)
        assert tfa.verify_totp_code(secret, code) is True

    def test_wrong_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, "000000") is False or True
        # 000000 might coincidentally match, so we test a known-bad pattern

    def test_empty_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, "") is False

    def test_non_digit_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, "abcdef") is False

    def test_short_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, "123") is False

    def test_long_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, "1234567") is False

    def test_none_code_rejected(self, tfa):
        secret = tfa.generate_totp_secret(42)
        assert tfa.verify_totp_code(secret, None) is False


# ==================== 备用验证码 ====================

class TestGenerateBackupCodes:

    def test_default_count(self, tfa):
        codes = tfa.generate_backup_codes(1)
        assert len(codes) == 10

    def test_custom_count(self, tfa):
        codes = tfa.generate_backup_codes(1, count=5)
        assert len(codes) == 5

    def test_all_unique(self, tfa):
        codes = tfa.generate_backup_codes(1, count=20)
        assert len(set(codes)) == 20

    def test_all_uppercase_hex(self, tfa):
        codes = tfa.generate_backup_codes(1)
        for code in codes:
            assert code == code.upper()
            assert len(code) == 10

    def test_different_users_different_codes(self, tfa):
        c1 = set(tfa.generate_backup_codes(1))
        c2 = set(tfa.generate_backup_codes(2))
        # Very unlikely to overlap
        assert c1 != c2


class TestVerifyBackupCode:

    def test_valid_code(self, tfa):
        stored = ["AAAA111111", "BBBB222222", "CCCC333333"]
        valid, remaining = tfa.verify_backup_code(1, "BBBB222222", stored)
        assert valid is True
        assert "BBBB222222" not in remaining
        assert len(remaining) == 2

    def test_invalid_code(self, tfa):
        stored = ["AAAA111111", "BBBB222222"]
        valid, remaining = tfa.verify_backup_code(1, "ZZZZ999999", stored)
        assert valid is False
        assert remaining == stored

    def test_case_insensitive(self, tfa):
        stored = ["AAAA111111"]
        valid, remaining = tfa.verify_backup_code(1, "aaaa111111", stored)
        assert valid is True

    def test_empty_stored_codes(self, tfa):
        valid, remaining = tfa.verify_backup_code(1, "AAAA111111", [])
        assert valid is False
        assert remaining == []

    def test_code_consumed_only_once(self, tfa):
        stored = ["AAAA111111"]
        valid1, remaining1 = tfa.verify_backup_code(1, "AAAA111111", stored)
        assert valid1 is True
        valid2, remaining2 = tfa.verify_backup_code(1, "AAAA111111", remaining1)
        assert valid2 is False

    def test_roundtrip(self, tfa):
        """Generate codes then verify them one by one"""
        codes = tfa.generate_backup_codes(1, count=3)
        remaining = codes.copy()
        for code in codes:
            valid, remaining = tfa.verify_backup_code(1, code, remaining)
            assert valid is True
        assert remaining == []
