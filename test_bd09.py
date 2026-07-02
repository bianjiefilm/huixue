"""BD09 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd09 import (
    design_row_key_with_salt,
    compute_region_count,
    is_hot_row_key,
    compute_block_cache_hit_rate,
)

TOL = 1e-6


# F1: design_row_key_with_salt
def test_salt_typical():
    """prefix='event', ts=1714003200, salt=4 → salt=0, '0-event-1714003200'"""
    assert design_row_key_with_salt("event", 1714003200, 4) == "0-event-1714003200"

def test_salt_with_remainder():
    """ts=10, salt=4 → 10%4=2, '2-user-10'"""
    assert design_row_key_with_salt("user", 10, 4) == "2-user-10"

def test_salt_count_8():
    """ts=15, salt=8 → 15%8=7"""
    assert design_row_key_with_salt("device", 15, 8) == "7-device-15"

def test_salt_zero_timestamp():
    """ts=0 → salt=0"""
    assert design_row_key_with_salt("x", 0, 4) == "0-x-0"

def test_salt_count_1():
    """salt_count=1 → salt 总是 0"""
    assert design_row_key_with_salt("y", 100, 1) == "0-y-100"

def test_salt_raises_on_empty_prefix():
    with pytest.raises(ValueError):
        design_row_key_with_salt("", 100, 4)

def test_salt_raises_on_zero_salt_count():
    with pytest.raises(ValueError):
        design_row_key_with_salt("x", 100, 0)

def test_salt_raises_on_non_string():
    with pytest.raises(TypeError):
        design_row_key_with_salt(123, 100, 4)


# F2: compute_region_count (ceil)
def test_region_typical():
    """100 GB / 10 GB → 10"""
    assert compute_region_count(100.0) == 10

def test_region_partial_ceil():
    """15 GB / 10 GB → 2"""
    assert compute_region_count(15.0) == 2

def test_region_custom_size():
    """100 GB / 20 GB → 5"""
    assert compute_region_count(100.0, 20.0) == 5

def test_region_just_above_one():
    """11 GB / 10 GB → 2"""
    assert compute_region_count(11.0) == 2

def test_region_minimum():
    """1 GB → 1 (boundary)"""
    assert compute_region_count(1.0) == 1

def test_region_raises_on_zero():
    with pytest.raises(ValueError):
        compute_region_count(0)

def test_region_raises_on_zero_region_size():
    with pytest.raises(ValueError):
        compute_region_count(10, 0)


# F3: is_hot_row_key
def test_hot_yes():
    """{'a': 60, 'b': 30, 'c': 10} total=100, threshold=0.5: a=60>50 → True"""
    assert is_hot_row_key({"a": 60, "b": 30, "c": 10}, 100) is True

def test_hot_no():
    """{'a': 30, 'b': 30, 'c': 40} total=100: 都 <= 50 → False"""
    assert is_hot_row_key({"a": 30, "b": 30, "c": 40}, 100) is False

def test_hot_at_threshold():
    """count == total * threshold → False (>, 严格)"""
    assert is_hot_row_key({"a": 50, "b": 50}, 100) is False

def test_hot_just_above():
    """count = 51, total=100 → True"""
    assert is_hot_row_key({"a": 51, "b": 49}, 100) is True

def test_hot_custom_threshold():
    """threshold=0.3, {'a':40} total=100 → True"""
    assert is_hot_row_key({"a": 40, "b": 60}, 100, 0.3) is True

def test_hot_empty_dict():
    """空 dict → False (no hot)"""
    assert is_hot_row_key({}, 100) is False

def test_hot_raises_on_zero_total():
    with pytest.raises(ValueError):
        is_hot_row_key({"a": 1}, 0)

def test_hot_raises_on_non_dict():
    with pytest.raises(TypeError):
        is_hot_row_key("counts", 100)


# F4: compute_block_cache_hit_rate
def test_hr_typical():
    """900 / 1000 = 0.9"""
    assert abs(compute_block_cache_hit_rate(1000, 900) - 0.9) < TOL

def test_hr_half():
    """500 / 1000 = 0.5"""
    assert abs(compute_block_cache_hit_rate(1000, 500) - 0.5) < TOL

def test_hr_perfect():
    """100 / 100 = 1.0"""
    assert abs(compute_block_cache_hit_rate(100, 100) - 1.0) < TOL

def test_hr_all_miss():
    """100 / 100 reads but 0 hits → 0"""
    assert abs(compute_block_cache_hit_rate(100, 0) - 0.0) < TOL

def test_hr_decimal():
    """3 / 4 = 0.75"""
    assert abs(compute_block_cache_hit_rate(4, 3) - 0.75) < TOL

def test_hr_raises_on_zero_reads():
    with pytest.raises(ValueError):
        compute_block_cache_hit_rate(0, 0)

def test_hr_raises_on_hits_gt_reads():
    with pytest.raises(ValueError):
        compute_block_cache_hit_rate(100, 200)

def test_hr_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_block_cache_hit_rate(100.0, 50)
