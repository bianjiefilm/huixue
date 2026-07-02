"""WX04 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx04 import (
    is_outlier_iqr,
    compute_iqr_bounds,
    clip_value_to_range,
    count_outliers,
)

TOL = 1e-6


# F1: is_outlier_iqr
def test_iqr_normal_value():
    """Q1=10, Q3=20, IQR=10, mult=1.5: lower=-5, upper=35. value=15 → not outlier"""
    assert is_outlier_iqr(15, 10, 20, 1.5) is False

def test_iqr_low_outlier():
    """value=-10 < lower=-5 → outlier"""
    assert is_outlier_iqr(-10, 10, 20, 1.5) is True

def test_iqr_at_upper_boundary():
    """value=35 == upper → not outlier (>, 严格大)"""
    assert is_outlier_iqr(35, 10, 20, 1.5) is False

def test_iqr_extreme_multiplier():
    """mult=3.0: lower=-20, upper=50. value=40 → not outlier"""
    assert is_outlier_iqr(40, 10, 20, 3.0) is False

def test_iqr_q1_eq_q3():
    """Q1==Q3 → IQR=0, lower=upper=q1. 任何不等于 q1 都是 outlier"""
    assert is_outlier_iqr(15, 10, 10, 1.5) is True
    assert is_outlier_iqr(10, 10, 10, 1.5) is False

def test_iqr_raises_on_q1_gt_q3():
    with pytest.raises(ValueError):
        is_outlier_iqr(15, 20, 10, 1.5)

def test_iqr_raises_on_non_numeric():
    with pytest.raises(TypeError):
        is_outlier_iqr("15", 10, 20, 1.5)


# F2: compute_iqr_bounds
def test_bounds_normal():
    """Q1=10, Q3=20, mult=1.5 → (-5, 35)"""
    lo, up = compute_iqr_bounds(10, 20, 1.5)
    assert abs(lo - (-5)) < TOL
    assert abs(up - 35) < TOL

def test_bounds_extreme_multiplier():
    """mult=3.0 → (-20, 50)"""
    lo, up = compute_iqr_bounds(10, 20, 3.0)
    assert abs(lo - (-20)) < TOL
    assert abs(up - 50) < TOL

def test_bounds_default():
    """default 1.5"""
    lo, up = compute_iqr_bounds(10, 20)
    assert abs(lo - (-5)) < TOL
    assert abs(up - 35) < TOL

def test_bounds_negative_q1():
    """Q1=-5, Q3=5, mult=1.5: IQR=10, → (-20, 20)"""
    lo, up = compute_iqr_bounds(-5, 5, 1.5)
    assert abs(lo - (-20)) < TOL
    assert abs(up - 20) < TOL

def test_bounds_q1_eq_q3():
    """Q1==Q3=10 → IQR=0, (10, 10) (boundary)"""
    lo, up = compute_iqr_bounds(10, 10, 1.5)
    assert abs(lo - 10) < TOL
    assert abs(up - 10) < TOL

def test_bounds_raises_on_q1_gt_q3():
    with pytest.raises(ValueError):
        compute_iqr_bounds(20, 10)

def test_bounds_raises_on_non_numeric():
    with pytest.raises(TypeError):
        compute_iqr_bounds("10", 20)


# F3: clip_value_to_range
def test_clip_in_range():
    assert abs(clip_value_to_range(15, 10, 20) - 15) < TOL

def test_clip_below_lower():
    assert abs(clip_value_to_range(5, 10, 20) - 10) < TOL

def test_clip_above_upper():
    assert abs(clip_value_to_range(25, 10, 20) - 20) < TOL

def test_clip_at_lower_boundary():
    assert abs(clip_value_to_range(10, 10, 20) - 10) < TOL

def test_clip_negative_range():
    assert abs(clip_value_to_range(-15, -10, -5) - (-10)) < TOL

def test_clip_raises_on_lower_gt_upper():
    with pytest.raises(ValueError):
        clip_value_to_range(15, 20, 10)


# F4: count_outliers (count outside [lower, upper], strict <, >)
def test_co_no_outliers():
    """全在范围内 → 0"""
    assert count_outliers([10, 15, 20], 5, 25) == 0

def test_co_one_high():
    assert count_outliers([10, 15, 30], 5, 25) == 1

def test_co_one_low():
    assert count_outliers([0, 15, 20], 5, 25) == 1

def test_co_mixed():
    assert count_outliers([0, 10, 15, 30, 50], 5, 25) == 3

def test_co_at_boundaries():
    """5 == lower 不算 outlier (< 严格)"""
    assert count_outliers([5, 25, 4, 26], 5, 25) == 2

def test_co_raises_on_lower_gt_upper():
    with pytest.raises(ValueError):
        count_outliers([10, 20], 30, 10)

def test_co_raises_on_non_list():
    with pytest.raises(TypeError):
        count_outliers("10,20", 0, 100)
