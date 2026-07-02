"""WX08 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx08 import (
    parse_numeric_string,
    clip_to_range,
    round_half_up,
    is_numeric_string,
)

TOL = 1e-6


# F1: parse_numeric_string — all inputs need $/¥/, (so plain float fails)
def test_parse_dollar_thousands():
    assert abs(parse_numeric_string("$1,234.56") - 1234.56) < TOL

def test_parse_yuan_thousands():
    assert abs(parse_numeric_string("￥9,876.5") - 9876.5) < TOL

def test_parse_yen():
    assert abs(parse_numeric_string("¥500") - 500.0) < TOL

def test_parse_dollar_no_thousands():
    assert abs(parse_numeric_string("$50") - 50.0) < TOL

def test_parse_multi_thousands():
    assert abs(parse_numeric_string("1,234,567.89") - 1234567.89) < TOL

def test_parse_simple_with_thousands():
    assert abs(parse_numeric_string("1,000") - 1000.0) < TOL

def test_parse_raises_on_letters():
    with pytest.raises(ValueError):
        parse_numeric_string("abc")

def test_parse_raises_on_unit_suffix():
    with pytest.raises(ValueError):
        parse_numeric_string("100.00 USD")

def test_parse_raises_on_non_string():
    with pytest.raises(TypeError):
        parse_numeric_string(123)


# F2: clip_to_range — all expected != value
def test_clip_below():
    """50 截到 [100, 200] → 100 (low)"""
    assert abs(clip_to_range(50.0, 100.0, 200.0) - 100.0) < TOL

def test_clip_above():
    """300 截到 [0, 100] → 100"""
    assert abs(clip_to_range(300.0, 0.0, 100.0) - 100.0) < TOL

def test_clip_negative_below():
    """-50 截到 [-10, 10] → -10"""
    assert abs(clip_to_range(-50.0, -10.0, 10.0) - (-10.0)) < TOL

def test_clip_raises_on_lower_gt_upper():
    with pytest.raises(ValueError):
        clip_to_range(50.0, 100.0, 0.0)


# F3: round_half_up — focus on .5 cases (banker's vs half-up differ)
def test_round_half_up_05():
    """0.5 → 1.0"""
    assert abs(round_half_up(0.5) - 1.0) < TOL

def test_round_half_up_15():
    """1.5 → 2.0 (banker would also give 2)"""
    assert abs(round_half_up(1.5) - 2.0) < TOL

def test_round_half_up_25():
    """2.5 → 3.0 (kills banker)"""
    assert abs(round_half_up(2.5) - 3.0) < TOL

def test_round_half_up_45():
    """4.5 → 5.0 (kills banker, banker would give 4)"""
    assert abs(round_half_up(4.5) - 5.0) < TOL

def test_round_half_up_with_decimals_2():
    """1.235 round 2 → 1.24"""
    assert abs(round_half_up(1.235, 2) - 1.24) < TOL

def test_round_half_up_055():
    """0.55 round 1 → 0.6 (kills banker)"""
    assert abs(round_half_up(0.55, 1) - 0.6) < TOL

def test_round_half_up_raises_on_negative_decimals():
    with pytest.raises(ValueError):
        round_half_up(1.5, -1)

def test_round_half_up_raises_on_non_numeric():
    with pytest.raises(TypeError):
        round_half_up("1.5")


# F4: is_numeric_string — most expected True (since hardcode False)
def test_isn_dollar():
    assert is_numeric_string("$1,234.56") is True

def test_isn_yen():
    assert is_numeric_string("¥500") is True

def test_isn_yuan_thousands():
    assert is_numeric_string("￥1,000") is True

def test_isn_negative():
    assert is_numeric_string("-100.25") is True

def test_isn_invalid_letters():
    assert is_numeric_string("abc") is False

def test_isn_invalid_unit_suffix():
    assert is_numeric_string("100.00 USD") is False

def test_isn_raises_on_non_string():
    with pytest.raises(TypeError):
        is_numeric_string(123)
