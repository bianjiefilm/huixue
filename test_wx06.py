"""WX06 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx06 import (
    count_non_ascii,
    remove_control_chars,
    is_pure_ascii,
    has_utf8_bom,
)


# F1: count_non_ascii — diverse expected, none coincide with len/ascii_count
def test_cna_one_in_4():
    assert count_non_ascii("abc中") == 1

def test_cna_two_in_5():
    assert count_non_ascii("abc中文") == 2

def test_cna_one_in_5():
    assert count_non_ascii("中a b c") == 1

def test_cna_four_in_6():
    assert count_non_ascii("ab中文测试") == 4

def test_cna_two_emojis():
    assert count_non_ascii("ab😀c😀") == 2

def test_cna_raises_on_non_string():
    with pytest.raises(TypeError):
        count_non_ascii(123)


# F2: remove_control_chars — input != output
def test_rcc_remove_bell():
    assert remove_control_chars("hi\x07there") == "hithere"

def test_rcc_remove_null():
    assert remove_control_chars("a\x00b") == "ab"

def test_rcc_remove_vt():
    assert remove_control_chars("a\x0bb") == "ab"

def test_rcc_mixed_keep_remove():
    """TAB+LF 保留, BEL 去掉"""
    assert remove_control_chars("a\tb\nc\x07d") == "a\tb\ncd"

def test_rcc_keep_only_visible():
    assert remove_control_chars("hi\x05world") == "hiworld"

def test_rcc_raises_on_non_string():
    with pytest.raises(TypeError):
        remove_control_chars(123)


# F3: is_pure_ascii — only "all non-ASCII" (False) cases — kills 'all-non-ASCII' shape
def test_ipa_only_chinese():
    assert is_pure_ascii("中文") is False

def test_ipa_japanese():
    assert is_pure_ascii("ひらがな") is False

def test_ipa_emoji_only():
    assert is_pure_ascii("😀😀") is False

def test_ipa_korean():
    assert is_pure_ascii("한글") is False

def test_ipa_raises_on_non_string():
    with pytest.raises(TypeError):
        is_pure_ascii(123)


# F4: has_utf8_bom — 1 True + multiple "BOM not at start" False
def test_bom_starts_with_bom():
    assert has_utf8_bom("﻿hello") is True

def test_bom_in_middle():
    assert has_utf8_bom("hi﻿lo") is False

def test_bom_at_end():
    assert has_utf8_bom("hi﻿") is False

def test_bom_two_in_middle():
    assert has_utf8_bom("h﻿i﻿") is False

def test_bom_raises_on_non_string():
    with pytest.raises(TypeError):
        has_utf8_bom(123)
