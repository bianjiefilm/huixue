"""MJ01 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj01 import (
    map_activity_to_phase,
    classify_learning_type,
    compute_accuracy,
    is_overfit,
)

TOL = 1e-9


# ============================================================
# F1: map_activity_to_phase  (6 个测试)
# ============================================================

def test_phase_business_understanding():
    assert map_activity_to_phase("明确业务目标和成功标准") == "业务理解"

def test_phase_data_preparation():
    assert map_activity_to_phase("缺失值填充与特征编码") == "数据准备"

def test_phase_modeling():
    assert map_activity_to_phase("调整随机森林超参数") == "建模"

def test_phase_deployment():
    assert map_activity_to_phase("将模型上线监控线上指标") == "部署"

def test_phase_unknown_for_empty_string():
    """边界: 空字符串 → 未知"""
    assert map_activity_to_phase("") == "未知"

def test_phase_raises_on_non_string():
    """负例: 非字符串输入 → TypeError"""
    with pytest.raises(TypeError):
        map_activity_to_phase(123)


# ============================================================
# F2: classify_learning_type  (5 个测试)
# ============================================================

def test_lt_supervised():
    assert classify_learning_type(True, True) == "supervised"

def test_lt_unsupervised_when_no_labels():
    assert classify_learning_type(False, False) == "unsupervised"

def test_lt_semi_supervised_when_partial():
    assert classify_learning_type(True, False) == "semi-supervised"

def test_lt_unsupervised_dominates_when_no_labels_even_if_all_labeled_true():
    """边界: has_labels=False 时 all_labeled 取何值都是 unsupervised"""
    assert classify_learning_type(False, True) == "unsupervised"

def test_lt_raises_on_non_bool():
    """负例: 非 bool 输入 → TypeError"""
    with pytest.raises(TypeError):
        classify_learning_type("yes", True)


# ============================================================
# F3: compute_accuracy  (7 个测试)
# ============================================================

def test_acc_all_correct():
    assert abs(compute_accuracy([1, 1, 0, 0], [1, 1, 0, 0]) - 1.0) < TOL

def test_acc_all_wrong():
    assert abs(compute_accuracy([1, 1, 0, 0], [0, 0, 1, 1]) - 0.0) < TOL

def test_acc_partial():
    assert abs(compute_accuracy([1, 1, 0, 0], [1, 0, 0, 0]) - 0.75) < TOL

def test_acc_multiclass():
    assert abs(compute_accuracy([0, 1, 2, 3], [0, 1, 2, 3]) - 1.0) < TOL

def test_acc_single_sample_correct():
    """边界: 单样本"""
    assert abs(compute_accuracy([1], [1]) - 1.0) < TOL

def test_acc_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        compute_accuracy([], [])

def test_acc_raises_on_length_mismatch():
    """负例: 长度不一致 → ValueError"""
    with pytest.raises(ValueError):
        compute_accuracy([1, 1, 0], [1, 1])


# ============================================================
# F4: is_overfit  (6 个测试)
# ============================================================

def test_of_clearly_overfit():
    r = is_overfit(0.99, 0.60, 0.1)
    assert r["is_overfitting"] is True
    assert abs(r["gap"] - 0.39) < TOL

def test_of_not_overfit_small_gap():
    r = is_overfit(0.85, 0.83, 0.1)
    assert r["is_overfitting"] is False
    assert abs(r["gap"] - 0.02) < TOL

def test_of_not_overfit_zero_gap():
    r = is_overfit(0.70, 0.70, 0.1)
    assert r["is_overfitting"] is False
    assert abs(r["gap"] - 0.0) < TOL

def test_of_threshold_strict_greater():
    """边界: gap 等于 threshold 不算过拟合 (严格 >)"""
    r = is_overfit(0.5, 0.4, 0.1)
    assert r["is_overfitting"] is False
    assert abs(r["gap"] - 0.1) < TOL

def test_of_extreme_gap():
    """边界: 极值 gap=1.0"""
    r = is_overfit(1.0, 0.0, 0.1)
    assert r["is_overfitting"] is True
    assert abs(r["gap"] - 1.0) < TOL

def test_of_raises_on_non_numeric():
    """负例: 非数值 → TypeError"""
    with pytest.raises(TypeError):
        is_overfit("0.9", 0.5)
