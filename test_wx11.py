"""WX11 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx11 import (
    compute_completeness,
    compute_uniqueness,
    compute_validity_in_range,
    quality_summary_dict,
)

TOL = 1e-6


# F1: compute_completeness
def test_comp_no_missing():
    assert abs(compute_completeness([1, 2, 3, 4]) - 1.0) < TOL

def test_comp_two_missing_in_5():
    """[1, None, 3, "", 5] → 3/5 = 0.6"""
    assert abs(compute_completeness([1, None, 3, "", 5]) - 0.6) < TOL

def test_comp_three_missing_in_4():
    """[None, "NA", "null", 1] → 1/4 = 0.25"""
    assert abs(compute_completeness([None, "NA", "null", 1]) - 0.25) < TOL

def test_comp_custom_markers():
    """[1, -999, 2, -999] markers={-999} → 2/4 = 0.5"""
    assert abs(compute_completeness([1, -999, 2, -999], markers={-999}) - 0.5) < TOL

def test_comp_one_missing_in_3():
    """[1, 2, None] → 2/3"""
    assert abs(compute_completeness([1, 2, None]) - 2.0/3) < TOL

def test_comp_raises_on_empty():
    with pytest.raises(ValueError):
        compute_completeness([])

def test_comp_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_completeness("123")


# F2: compute_uniqueness
def test_uniq_all_distinct_5():
    assert abs(compute_uniqueness([1, 2, 3, 4, 5]) - 1.0) < TOL

def test_uniq_2_in_4():
    """[1, 2, 1, 2] → 2/4 = 0.5"""
    assert abs(compute_uniqueness([1, 2, 1, 2]) - 0.5) < TOL

def test_uniq_3_in_5():
    """[1, 1, 2, 2, 3] → 3/5 = 0.6"""
    assert abs(compute_uniqueness([1, 1, 2, 2, 3]) - 0.6) < TOL

def test_uniq_1_in_5():
    """[7, 7, 7, 7, 7] → 1/5 = 0.2"""
    assert abs(compute_uniqueness([7, 7, 7, 7, 7]) - 0.2) < TOL

def test_uniq_2_in_3_strings():
    """['a', 'b', 'a'] → 2/3"""
    assert abs(compute_uniqueness(["a", "b", "a"]) - 2.0/3) < TOL

def test_uniq_raises_on_empty():
    with pytest.raises(ValueError):
        compute_uniqueness([])

def test_uniq_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_uniqueness(123)


# F3: compute_validity_in_range
def test_valid_all_in_range():
    """[5, 10, 15] in [0, 20] → 3/3 = 1.0"""
    assert abs(compute_validity_in_range([5, 10, 15], 0, 20) - 1.0) < TOL

def test_valid_two_out_of_three():
    """[5, 100, 15] in [0, 20] → 2/3 (100 超出)"""
    assert abs(compute_validity_in_range([5, 100, 15], 0, 20) - 2.0/3) < TOL

def test_valid_one_in_four():
    """[5, 100, 200, 300] in [0, 50] → 1/4 = 0.25"""
    assert abs(compute_validity_in_range([5, 100, 200, 300], 0, 50) - 0.25) < TOL

def test_valid_three_in_five():
    """[5, 10, 15, 25, 30] in [0, 20] → 3/5 = 0.6"""
    assert abs(compute_validity_in_range([5, 10, 15, 25, 30], 0, 20) - 0.6) < TOL

def test_valid_at_boundaries():
    """[0, 20, -1, 21] in [0, 20] → 2/4 = 0.5 (闭区间)"""
    assert abs(compute_validity_in_range([0, 20, -1, 21], 0, 20) - 0.5) < TOL

def test_valid_raises_on_empty():
    with pytest.raises(ValueError):
        compute_validity_in_range([], 0, 100)

def test_valid_raises_on_lower_gt_upper():
    with pytest.raises(ValueError):
        compute_validity_in_range([1, 2, 3], 10, 0)


# F4: quality_summary_dict
def test_summary_perfect():
    r = quality_summary_dict(1.0, 1.0, 1.0)
    assert abs(r["completeness"] - 1.0) < TOL
    assert abs(r["uniqueness"] - 1.0) < TOL
    assert abs(r["validity"] - 1.0) < TOL
    assert abs(r["overall"] - 1.0) < TOL

def test_summary_typical():
    """0.9 + 0.5 + 0.8 → overall = 0.733..."""
    r = quality_summary_dict(0.9, 0.5, 0.8)
    assert abs(r["completeness"] - 0.9) < TOL
    assert abs(r["uniqueness"] - 0.5) < TOL
    assert abs(r["validity"] - 0.8) < TOL
    assert abs(r["overall"] - (0.9 + 0.5 + 0.8) / 3) < TOL

def test_summary_low_quality():
    """0.5 + 0.3 + 0.4 → overall = 0.4"""
    r = quality_summary_dict(0.5, 0.3, 0.4)
    assert abs(r["overall"] - 0.4) < TOL

def test_summary_zero():
    """全 0 → overall = 0"""
    r = quality_summary_dict(0.0, 0.0, 0.0)
    assert abs(r["overall"] - 0.0) < TOL

def test_summary_keys_complete():
    """4 个 key 都存在"""
    r = quality_summary_dict(0.5, 0.5, 0.5)
    assert "completeness" in r
    assert "uniqueness" in r
    assert "validity" in r
    assert "overall" in r

def test_summary_raises_on_out_of_range():
    with pytest.raises(ValueError):
        quality_summary_dict(1.5, 0.5, 0.5)

def test_summary_raises_on_non_numeric():
    with pytest.raises(TypeError):
        quality_summary_dict("0.5", 0.5, 0.5)
