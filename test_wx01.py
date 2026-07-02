"""WX01 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx01 import (
    classify_value_status,
    compute_quality_ratio,
    get_cleaning_priority,
    decide_drop_or_fill,
)

TOL = 1e-6


# F1: classify_value_status
def test_cls_valid_in_range():
    """5 ∈ [0, 10] → valid"""
    assert classify_value_status(5, 0, 10) == "valid"

def test_cls_out_of_range_low():
    """-5 < valid_min → out_of_range"""
    assert classify_value_status(-5, 0, 10) == "out_of_range"

def test_cls_out_of_range_high():
    """100 > valid_max → out_of_range"""
    assert classify_value_status(100, 0, 10) == "out_of_range"

def test_cls_missing_none():
    """None → missing"""
    assert classify_value_status(None, 0, 10) == "missing"

def test_cls_missing_empty_string():
    """空字符串 → missing"""
    assert classify_value_status("", 0, 10) == "missing"

def test_cls_missing_custom_marker():
    """custom marker -1 → missing"""
    assert classify_value_status(-1, 0, 10, missing_marker=-1) == "missing"

def test_cls_negative_in_range():
    """-3 ∈ [-10, 5] → valid (boundary 负数有效)"""
    assert classify_value_status(-3, -10, 5) == "valid"

def test_cls_raises_on_non_numeric_min():
    with pytest.raises(TypeError):
        classify_value_status(5, "0", 10)


# F2: compute_quality_ratio
def test_qr_perfect():
    """100/100 → 1.0"""
    assert abs(compute_quality_ratio(100, 100) - 1.0) < TOL

def test_qr_half():
    """50/100 → 0.5"""
    assert abs(compute_quality_ratio(50, 100) - 0.5) < TOL

def test_qr_partial_78():
    """78/100 → 0.78"""
    assert abs(compute_quality_ratio(78, 100) - 0.78) < TOL

def test_qr_zero_valid():
    """0/100 → 0.0 (boundary)"""
    assert abs(compute_quality_ratio(0, 100) - 0.0) < TOL

def test_qr_three_quarters():
    """3/4 = 0.75 (整数除法陷阱测试)"""
    assert abs(compute_quality_ratio(3, 4) - 0.75) < TOL

def test_qr_raises_on_zero_total():
    with pytest.raises(ValueError):
        compute_quality_ratio(0, 0)

def test_qr_raises_on_valid_gt_total():
    with pytest.raises(ValueError):
        compute_quality_ratio(101, 100)

def test_qr_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_quality_ratio(5.0, 10)


# F3: get_cleaning_priority
def test_priority_missing():
    assert get_cleaning_priority("missing") == 1

def test_priority_duplicate():
    assert get_cleaning_priority("duplicate") == 2

def test_priority_outlier():
    assert get_cleaning_priority("outlier") == 3

def test_priority_format():
    assert get_cleaning_priority("format") == 4

def test_priority_consistency():
    assert get_cleaning_priority("consistency") == 5

def test_priority_raises_on_unknown():
    with pytest.raises(ValueError):
        get_cleaning_priority("unknown_step")

def test_priority_raises_on_empty():
    """空字符串 boundary"""
    with pytest.raises(ValueError):
        get_cleaning_priority("")

def test_priority_raises_on_non_string():
    with pytest.raises(TypeError):
        get_cleaning_priority(123)


# F4: decide_drop_or_fill
def test_decide_drop_high_missing():
    """80% missing > 0.5 → drop"""
    assert decide_drop_or_fill(80, 100, 0.5) == "drop"

def test_decide_fill_low_missing():
    """20% missing < 0.5 → fill"""
    assert decide_drop_or_fill(20, 100, 0.5) == "fill"

def test_decide_just_above_threshold():
    """51% missing > 0.5 → drop"""
    assert decide_drop_or_fill(51, 100, 0.5) == "drop"

def test_decide_zero_missing():
    """0 missing → fill (boundary)"""
    assert decide_drop_or_fill(0, 100, 0.5) == "fill"

def test_decide_custom_threshold_03():
    """20% > 0.3? no, → fill; 40% > 0.3? yes → drop"""
    assert decide_drop_or_fill(20, 100, 0.3) == "fill"
    assert decide_drop_or_fill(40, 100, 0.3) == "drop"

def test_decide_raises_on_zero_total():
    with pytest.raises(ValueError):
        decide_drop_or_fill(0, 0, 0.5)

def test_decide_raises_on_invalid_threshold():
    with pytest.raises(ValueError):
        decide_drop_or_fill(20, 100, 1.5)

def test_decide_raises_on_non_int():
    with pytest.raises(TypeError):
        decide_drop_or_fill("20", 100, 0.5)
