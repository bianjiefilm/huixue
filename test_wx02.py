"""WX02 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx02 import (
    is_missing,
    count_missing,
    fill_missing_with_mean,
    fill_missing_with_constant,
)

TOL = 1e-6


# F1: is_missing (default markers: None, "", "NA", "null", "NaN")
def test_im_none():
    assert is_missing(None) is True

def test_im_empty_string():
    assert is_missing("") is True

def test_im_real_number_not_missing():
    """5 不是 missing"""
    assert is_missing(5) is False

def test_im_zero_not_missing():
    """0 不是 missing (重要边界)"""
    assert is_missing(0) is False

def test_im_normal_string_not_missing():
    """普通字符串不是 missing"""
    assert is_missing("hello") is False

def test_im_custom_markers():
    """自定义 markers 集合"""
    assert is_missing(-999, markers={-999, None}) is True
    assert is_missing(-1, markers={-999}) is False


# F2: count_missing
def test_cm_no_missing():
    """[1, 2, 3] → 0"""
    assert count_missing([1, 2, 3]) == 0

def test_cm_some_missing():
    """[1, None, 2, "NA", 3] → 2"""
    assert count_missing([1, None, 2, "NA", 3]) == 2

def test_cm_all_missing():
    """全 missing → len"""
    assert count_missing([None, "", "NA"]) == 3

def test_cm_zero_not_missing():
    """[0, 1, 2] → 0 (0 不是 missing)"""
    assert count_missing([0, 1, 2]) == 0

def test_cm_with_custom_markers():
    """[1, -999, 2, -999] markers={-999} → 2"""
    assert count_missing([1, -999, 2, -999], markers={-999}) == 2

def test_cm_raises_on_non_list():
    with pytest.raises(TypeError):
        count_missing("not a list")


# F3: fill_missing_with_mean
def test_fm_one_missing_middle():
    """[1, None, 3] → mean=2, → [1, 2, 3]"""
    r = fill_missing_with_mean([1.0, None, 3.0])
    expected = [1.0, 2.0, 3.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_fm_two_missing():
    """[1, None, 5, None, 3] → mean=(1+5+3)/3=3 → [1,3,5,3,3]"""
    r = fill_missing_with_mean([1.0, None, 5.0, None, 3.0])
    expected = [1.0, 3.0, 5.0, 3.0, 3.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_fm_string_marker():
    """[1, 'NA', 3, 5] → mean=3 → [1,3,3,5]"""
    r = fill_missing_with_mean([1.0, "NA", 3.0, 5.0])
    expected = [1.0, 3.0, 3.0, 5.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_fm_decimal_mean():
    """[1, None, 2] → mean=1.5 → [1,1.5,2]"""
    r = fill_missing_with_mean([1.0, None, 2.0])
    assert abs(r[0] - 1.0) < TOL
    assert abs(r[1] - 1.5) < TOL
    assert abs(r[2] - 2.0) < TOL

def test_fm_negative_values():
    """[-2, None, 4] → mean=1, → [-2, 1, 4]"""
    r = fill_missing_with_mean([-2.0, None, 4.0])
    assert abs(r[1] - 1.0) < TOL

def test_fm_raises_on_all_missing():
    with pytest.raises(ValueError):
        fill_missing_with_mean([None, "NA", None])

def test_fm_raises_on_empty():
    with pytest.raises(ValueError):
        fill_missing_with_mean([])

def test_fm_raises_on_non_list():
    with pytest.raises(TypeError):
        fill_missing_with_mean("1,2,3")


# F4: fill_missing_with_constant
def test_fc_basic():
    """[1, None, 3] const=0 → [1, 0, 3]"""
    r = fill_missing_with_constant([1, None, 3], 0)
    assert r == [1, 0, 3]

def test_fc_string_constant():
    """混合 None 与 'NA' const='unknown'"""
    r = fill_missing_with_constant([None, "x", "NA", "y"], "unknown")
    assert r == ["unknown", "x", "unknown", "y"]

def test_fc_zero_constant():
    """const=0, missing 全填 0"""
    r = fill_missing_with_constant([1, None, 2, "NA"], 0)
    assert r == [1, 0, 2, 0]

def test_fc_negative_constant():
    """const=-1, missing 全填 -1"""
    r = fill_missing_with_constant([None, 5], -1)
    assert r == [-1, 5]

def test_fc_raises_on_non_list():
    with pytest.raises(TypeError):
        fill_missing_with_constant("None", 0)
