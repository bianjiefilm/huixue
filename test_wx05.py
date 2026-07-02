"""WX05 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx05 import (
    normalize_phone_digits,
    normalize_email_lower,
    is_valid_email_basic,
    parse_simple_date_iso,
)


# F1: normalize_phone_digits — diverse outputs, no "already clean"
def test_phone_dashes_138():
    assert normalize_phone_digits("138-0000-0000") == "13800000000"

def test_phone_spaces_186():
    assert normalize_phone_digits("186 5555 1234") == "18655551234"

def test_phone_parens_199():
    assert normalize_phone_digits("(199) 8888-2222") == "19988882222"

def test_phone_intl_prefix_852():
    assert normalize_phone_digits("+852 9123-4567") == "85291234567"

def test_phone_alphanumeric_mix():
    """字母混杂: '1abc3xyz8' → '138'"""
    assert normalize_phone_digits("1abc3xyz8") == "138"

def test_phone_no_digits():
    """全字母 → 空串 (boundary)"""
    assert normalize_phone_digits("abc") == ""

def test_phone_raises_on_non_string():
    with pytest.raises(TypeError):
        normalize_phone_digits(13800000000)


# F2: normalize_email_lower — all tests need BOTH strip AND lower
def test_email_bob_163():
    assert normalize_email_lower("  Bob@163.COM  ") == "bob@163.com"

def test_email_carol_qq():
    assert normalize_email_lower(" Carol.X@qq.com  ") == "carol.x@qq.com"

def test_email_alice_uppercase_with_spaces():
    assert normalize_email_lower(" Alice@Gmail.com ") == "alice@gmail.com"

def test_email_dave_with_tabs():
    assert normalize_email_lower("\tDAVE@Hotmail.CO.UK\t") == "dave@hotmail.co.uk"

def test_email_empty_after_strip():
    """全空白 → '' (boundary)"""
    assert normalize_email_lower("   ") == ""

def test_email_raises_on_non_string():
    with pytest.raises(TypeError):
        normalize_email_lower(123)


# F3: is_valid_email_basic — heavy on False cases (kill always-True/Identity)
def test_invalid_no_at():
    assert is_valid_email_basic("alice.gmail.com") is False

def test_invalid_just_text():
    """无 @ 无 . → False"""
    assert is_valid_email_basic("notanemail") is False

def test_invalid_only_dot():
    assert is_valid_email_basic("alice.com") is False

def test_valid_typical():
    """1 个 valid 测试"""
    assert is_valid_email_basic("alice@gmail.com") is True

def test_valid_raises_on_non_string():
    with pytest.raises(TypeError):
        is_valid_email_basic(123)


# F4: parse_simple_date_iso — diverse, fewer raises (shape-attack passes them)
def test_date_2026_04_25():
    assert parse_simple_date_iso("2026-04-25") == (2026, 4, 25)

def test_date_2000_01_01():
    assert parse_simple_date_iso("2000-01-01") == (2000, 1, 1)

def test_date_2024_12_31():
    assert parse_simple_date_iso("2024-12-31") == (2024, 12, 31)

def test_date_leap_day_2024_02_29():
    assert parse_simple_date_iso("2024-02-29") == (2024, 2, 29)

def test_date_1999_09_09():
    """boundary 年份 < 2000"""
    assert parse_simple_date_iso("1999-09-09") == (1999, 9, 9)

def test_date_raises_on_non_numeric():
    """type 负例"""
    with pytest.raises(ValueError):
        parse_simple_date_iso("year-mm-dd")

def test_date_raises_on_non_string():
    with pytest.raises(TypeError):
        parse_simple_date_iso(20260425)
