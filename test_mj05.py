"""MJ05 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj05 import (
    majority_vote,
    compute_feature_importance,
    gini_impurity,
    compute_boosting_residual,
)

TOL = 1e-6


# ============================================================
# F1: majority_vote (transform 类, 含平票边界)
# ============================================================

def test_mv_simple_binary():
    """[[1,0,0],[0,1,1],[1,0,0]] 各行 row[0] 故意与多数不一致 → [0, 1, 0]"""
    assert majority_vote([[1, 0, 0], [0, 1, 1], [1, 0, 0]]) == [0, 1, 0]

def test_mv_tie_smaller():
    """[[1,0,0,1]] 平票 tie_break='smaller' → [0] (row[0]=1 与结果不一致)"""
    assert majority_vote([[1, 0, 0, 1]], tie_break="smaller") == [0]

def test_mv_three_classes():
    """[[0,1,2,2,2]] 类 2 多数 → [2]; row[0]=0 ≠ 2"""
    assert majority_vote([[0, 1, 2, 2, 2]]) == [2]

def test_mv_first_disagrees():
    """[[1,0,0,0]] row[0]=1 但多数 0 → [0]"""
    assert majority_vote([[1, 0, 0, 0]]) == [0]

def test_mv_first_is_minority():
    """[[2,1,1,1,1]] row[0]=2 是少数, 多数 1 → [1]"""
    assert majority_vote([[2, 1, 1, 1, 1]]) == [1]

def test_mv_raises_on_empty_outer():
    """边界: 外层空 → ValueError"""
    with pytest.raises(ValueError):
        majority_vote([])

def test_mv_raises_on_empty_inner():
    """边界: 内层空 → ValueError"""
    with pytest.raises(ValueError):
        majority_vote([[], []])

def test_mv_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        majority_vote("abc")


# ============================================================
# F2: compute_feature_importance (transform 类归一化)
# ============================================================

def test_fi_basic():
    """[10, 5, 5] → [0.5, 0.25, 0.25]"""
    r = compute_feature_importance([10, 5, 5])
    expected = [0.5, 0.25, 0.25]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_fi_uniform():
    """[1,1,1,1] → [0.25]*4"""
    r = compute_feature_importance([1, 1, 1, 1])
    for v in r:
        assert abs(v - 0.25) < TOL

def test_fi_all_one_feature():
    """[100, 0, 0] → [1.0, 0.0, 0.0]"""
    r = compute_feature_importance([100, 0, 0])
    assert abs(r[0] - 1.0) < TOL
    assert abs(r[1] - 0.0) < TOL
    assert abs(r[2] - 0.0) < TOL

def test_fi_proportional():
    """[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]"""
    r = compute_feature_importance([2, 4, 6, 8])
    expected = [0.1, 0.2, 0.3, 0.4]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_fi_raises_on_all_zero():
    """边界: 全 0 → ValueError"""
    with pytest.raises(ValueError):
        compute_feature_importance([0, 0, 0])

def test_fi_raises_on_empty():
    with pytest.raises(ValueError):
        compute_feature_importance([])

def test_fi_raises_on_negative():
    with pytest.raises(ValueError):
        compute_feature_importance([1, -1, 2])

def test_fi_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_feature_importance("abc")


# ============================================================
# F3: gini_impurity (多组独特期望防 hardcode)
# ============================================================

def test_gini_pure():
    """单类 → 0.0"""
    assert abs(gini_impurity([0, 0, 0, 0]) - 0.0) < TOL

def test_gini_balanced_binary():
    """[0,0,1,1] → 0.5"""
    assert abs(gini_impurity([0, 0, 1, 1]) - 0.5) < TOL

def test_gini_three_one():
    """[0,0,0,1] p0=0.75 p1=0.25 → 1 - 0.5625 - 0.0625 = 0.375"""
    assert abs(gini_impurity([0, 0, 0, 1]) - 0.375) < TOL

def test_gini_three_classes_equal():
    """[0,1,2] → 1 - 3*(1/3)^2 = 2/3"""
    assert abs(gini_impurity([0, 1, 2]) - 2 / 3) < TOL

def test_gini_four_classes_equal():
    """[0,1,2,3] → 1 - 4*0.25^2 = 0.75"""
    assert abs(gini_impurity([0, 1, 2, 3]) - 0.75) < TOL

def test_gini_unbalanced():
    """[0,0,0,1,1] p0=0.6 p1=0.4 → 1 - 0.36 - 0.16 = 0.48"""
    assert abs(gini_impurity([0, 0, 0, 1, 1]) - 0.48) < TOL

def test_gini_raises_on_empty():
    with pytest.raises(ValueError):
        gini_impurity([])

def test_gini_raises_on_non_list():
    with pytest.raises(TypeError):
        gini_impurity("abc")


# ============================================================
# F4: compute_boosting_residual (transform 类)
# ============================================================

def test_residual_perfect_fit():
    """[1,2,3], [1,2,3] → [0,0,0]"""
    r = compute_boosting_residual([1, 2, 3], [1, 2, 3])
    expected = [0.0, 0.0, 0.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_residual_constant_diff():
    """[10,20,30], [5,15,25] → [5,5,5]"""
    r = compute_boosting_residual([10, 20, 30], [5, 15, 25])
    for v in r:
        assert abs(v - 5.0) < TOL

def test_residual_signed():
    """[1,2,3], [3,2,1] → [-2, 0, 2]"""
    r = compute_boosting_residual([1, 2, 3], [3, 2, 1])
    expected = [-2.0, 0.0, 2.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_residual_floats():
    """[1.5, 2.5], [1.0, 2.0] → [0.5, 0.5]"""
    r = compute_boosting_residual([1.5, 2.5], [1.0, 2.0])
    for v in r:
        assert abs(v - 0.5) < TOL

def test_residual_y_pred_zeros():
    """[5,7,11], [0,0,0] → [5,7,11] (boundary: pred 全 0, residual = y_true)"""
    r = compute_boosting_residual([5, 7, 11], [0, 0, 0])
    expected = [5.0, 7.0, 11.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_residual_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        compute_boosting_residual([1, 2, 3], [1, 2])

def test_residual_raises_on_empty():
    with pytest.raises(ValueError):
        compute_boosting_residual([], [])

def test_residual_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_boosting_residual("abc", "def")
