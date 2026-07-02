"""MJ04 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj04 import (
    sigmoid,
    compute_confusion_matrix,
    compute_metrics,
    classify_by_threshold,
)

TOL = 1e-4


# ============================================================
# F1: sigmoid (transform 类, 多元独特期望防 hardcode 0.5)
# ============================================================

def test_sig_positive_two():
    """sigmoid(2) ≈ 0.8808 (避免 0 这种被 hardcode 0.5 命中的输入)"""
    r = sigmoid([2])
    assert len(r) == 1
    assert abs(r[0] - 0.8807970779) < TOL

def test_sig_three_values():
    """[0, 1, -1] → [0.5, 0.7311, 0.2689]"""
    r = sigmoid([0, 1, -1])
    expected = [0.5, 0.7310585786, 0.2689414214]
    assert len(r) == 3
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sig_extreme_values():
    """[10, -10] → 接近 (1, 0)"""
    r = sigmoid([10, -10])
    assert abs(r[0] - 0.9999546021) < TOL
    assert abs(r[1] - 0.0000453979) < TOL

def test_sig_half_values():
    """[0.5, -0.5] → [~0.622, ~0.378]"""
    r = sigmoid([0.5, -0.5])
    assert abs(r[0] - 0.6224593312) < TOL
    assert abs(r[1] - 0.3775406688) < TOL

def test_sig_empty():
    """边界: 空列表 → 空列表"""
    assert sigmoid([]) == []

def test_sig_negative_extreme():
    """边界: 单个极小值 → 接近 0"""
    r = sigmoid([-100])
    assert len(r) == 1
    assert abs(r[0] - 0.0) < TOL

def test_sig_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        sigmoid("abc")

def test_sig_raises_on_non_numeric():
    """负例: 含非数值元素 → TypeError"""
    with pytest.raises(TypeError):
        sigmoid([1, "a", 2])


# ============================================================
# F2: compute_confusion_matrix (8 测试, 4 键全验)
# ============================================================

def test_cm_all_correct():
    r = compute_confusion_matrix([1, 1, 0, 0], [1, 1, 0, 0])
    assert r == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}

def test_cm_all_wrong():
    r = compute_confusion_matrix([1, 1, 0, 0], [0, 0, 1, 1])
    assert r == {"tp": 0, "fp": 2, "tn": 0, "fn": 2}

def test_cm_mixed():
    r = compute_confusion_matrix([1, 1, 0, 0], [1, 0, 1, 0])
    assert r == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}

def test_cm_unbalanced():
    """y_true=[1]*5+[0]*5, y_pred=[1]*8+[0]*2"""
    r = compute_confusion_matrix([1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
                                  [1, 1, 1, 1, 1, 1, 1, 1, 0, 0])
    assert r == {"tp": 5, "fp": 3, "tn": 2, "fn": 0}

def test_cm_all_negative():
    r = compute_confusion_matrix([0, 0, 0], [0, 0, 0])
    assert r == {"tp": 0, "fp": 0, "tn": 3, "fn": 0}

def test_cm_raises_on_empty():
    """边界: 空 → ValueError"""
    with pytest.raises(ValueError):
        compute_confusion_matrix([], [])

def test_cm_raises_on_length_mismatch():
    """边界: 长度不一致 → ValueError"""
    with pytest.raises(ValueError):
        compute_confusion_matrix([1, 0, 1], [1, 0])

def test_cm_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        compute_confusion_matrix("01", "01")


# ============================================================
# F3: compute_metrics (7 测试, 4 键全验, 多组独特期望)
# ============================================================

def test_m_typical():
    """tp=50, fp=10, tn=30, fn=10: acc=0.8, p≈0.833, r≈0.833, f1≈0.833"""
    r = compute_metrics(50, 10, 30, 10)
    assert abs(r["accuracy"] - 0.8) < TOL
    assert abs(r["precision"] - 50 / 60) < TOL
    assert abs(r["recall"] - 50 / 60) < TOL
    assert abs(r["f1"] - 50 / 60) < TOL

def test_m_perfect():
    """tp=10, fp=0, tn=90, fn=0: 全 1.0"""
    r = compute_metrics(10, 0, 90, 0)
    assert abs(r["accuracy"] - 1.0) < TOL
    assert abs(r["precision"] - 1.0) < TOL
    assert abs(r["recall"] - 1.0) < TOL
    assert abs(r["f1"] - 1.0) < TOL

def test_m_zero_tp_with_fp():
    """tp=0, fp=100, tn=0, fn=0: acc=0, p=0, r 除零应为 0"""
    r = compute_metrics(0, 100, 0, 0)
    assert abs(r["accuracy"] - 0.0) < TOL
    assert abs(r["precision"] - 0.0) < TOL
    assert abs(r["recall"] - 0.0) < TOL
    assert abs(r["f1"] - 0.0) < TOL

def test_m_balanced_half():
    """tp=fp=tn=fn=5: 全 0.5"""
    r = compute_metrics(5, 5, 5, 5)
    assert abs(r["accuracy"] - 0.5) < TOL
    assert abs(r["precision"] - 0.5) < TOL
    assert abs(r["recall"] - 0.5) < TOL
    assert abs(r["f1"] - 0.5) < TOL

def test_m_raises_on_all_zero():
    """边界: 全 0 → ValueError"""
    with pytest.raises(ValueError):
        compute_metrics(0, 0, 0, 0)

def test_m_raises_on_negative():
    """边界: 负数 → ValueError"""
    with pytest.raises(ValueError):
        compute_metrics(-1, 0, 0, 0)

def test_m_raises_on_non_int():
    """负例: 非整数 → TypeError"""
    with pytest.raises(TypeError):
        compute_metrics(1.5, 0, 0, 0)


# ============================================================
# F4: classify_by_threshold (transform 类, 8 测试)
# ============================================================

def test_cbt_basic():
    """[0.1, 0.5, 0.9], threshold=0.5 → [0, 1, 1] (>= 边界判 1)"""
    assert classify_by_threshold([0.1, 0.5, 0.9], 0.5) == [0, 1, 1]

def test_cbt_near_extremes():
    """[0.05, 0.95], threshold=0.5 → [0, 1] (避免 0.0/1.0 与整数 0/1 等值的 D 巧合)"""
    assert classify_by_threshold([0.05, 0.95], 0.5) == [0, 1]

def test_cbt_at_boundary():
    """[0.5, 0.5], threshold=0.5 → [1, 1] (>= 严格大于等于)"""
    assert classify_by_threshold([0.5, 0.5], 0.5) == [1, 1]

def test_cbt_around_threshold():
    """[0.4, 0.6], threshold=0.5 → [0, 1]"""
    assert classify_by_threshold([0.4, 0.6], 0.5) == [0, 1]

def test_cbt_high_threshold():
    """[0.1, 0.5, 0.9], threshold=0.95 → [0, 0, 0]"""
    assert classify_by_threshold([0.1, 0.5, 0.9], 0.95) == [0, 0, 0]

def test_cbt_negative_with_zero_threshold():
    """[-0.5, 0.5], threshold=0.0 → [0, 1]"""
    assert classify_by_threshold([-0.5, 0.5], 0.0) == [0, 1]

def test_cbt_empty():
    """边界: 空列表 → 空列表"""
    assert classify_by_threshold([], 0.5) == []

def test_cbt_raises_on_non_list():
    """负例: scores 非 list → TypeError"""
    with pytest.raises(TypeError):
        classify_by_threshold("abc", 0.5)
