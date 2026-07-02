"""NN08 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn08 import (
    l1_regularization,
    l2_regularization,
    apply_dropout,
    check_overfit_signal,
)

TOL = 1e-6


# ============================================================
# F1: l1_regularization
# ============================================================

def test_l1_basic():
    """[1, -2, 3] alpha=0.1 → 0.1 * (1+2+3) = 0.6"""
    assert abs(l1_regularization([1, -2, 3], 0.1) - 0.6) < TOL

def test_l1_zero_weights():
    """全 0 → 0"""
    assert abs(l1_regularization([0, 0, 0], 0.5) - 0.0) < TOL

def test_l1_zero_alpha():
    """alpha=0 → 0"""
    assert abs(l1_regularization([1, 2, 3], 0.0) - 0.0) < TOL

def test_l1_negative_weights():
    """[-1, -2, -3] alpha=1.0 → 1.0 * (1+2+3) = 6"""
    assert abs(l1_regularization([-1, -2, -3], 1.0) - 6.0) < TOL

def test_l1_decimals():
    """[0.5, -0.5, 0.25] alpha=2.0 → 2.0 * 1.25 = 2.5"""
    assert abs(l1_regularization([0.5, -0.5, 0.25], 2.0) - 2.5) < TOL

def test_l1_raises_on_empty():
    with pytest.raises(ValueError):
        l1_regularization([], 0.1)

def test_l1_raises_on_negative_alpha():
    with pytest.raises(ValueError):
        l1_regularization([1, 2], -0.1)

def test_l1_raises_on_non_list():
    with pytest.raises(TypeError):
        l1_regularization("ab", 0.1)


# ============================================================
# F2: l2_regularization
# ============================================================

def test_l2_basic():
    """[1, -2, 3] alpha=0.1 → 0.1 * (1+4+9) = 1.4"""
    assert abs(l2_regularization([1, -2, 3], 0.1) - 1.4) < TOL

def test_l2_zero_weights():
    assert abs(l2_regularization([0, 0, 0], 0.5) - 0.0) < TOL

def test_l2_zero_alpha():
    assert abs(l2_regularization([1, 2, 3], 0.0) - 0.0) < TOL

def test_l2_known_simple():
    """[2, 2] alpha=0.5 → 0.5 * (4+4) = 4"""
    assert abs(l2_regularization([2, 2], 0.5) - 4.0) < TOL

def test_l2_decimals():
    """[0.1, 0.2] alpha=10 → 10 * (0.01 + 0.04) = 0.5"""
    assert abs(l2_regularization([0.1, 0.2], 10.0) - 0.5) < TOL

def test_l2_raises_on_empty():
    with pytest.raises(ValueError):
        l2_regularization([], 0.1)

def test_l2_raises_on_negative_alpha():
    with pytest.raises(ValueError):
        l2_regularization([1], -0.5)

def test_l2_raises_on_non_list():
    with pytest.raises(TypeError):
        l2_regularization("a", 0.1)


# ============================================================
# F3: apply_dropout (transform 类)
# ============================================================

def test_dropout_zero_rate_identity():
    """drop_rate=0 → 输入不变 (除以 1)"""
    a = [1.0, 2.0, 3.0, 4.0]
    r = apply_dropout(a, 0.0, seed=42)
    for i, e in enumerate(a):
        assert abs(r[i] - e) < TOL

def test_dropout_deterministic_same_seed():
    """同 seed 同输出"""
    a = [1.0] * 100
    r1 = apply_dropout(a, 0.5, seed=42)
    r2 = apply_dropout(a, 0.5, seed=42)
    assert r1 == r2

def test_dropout_different_seeds_differ():
    """不同 seed 不同输出"""
    a = [1.0] * 100
    r1 = apply_dropout(a, 0.5, seed=42)
    r2 = apply_dropout(a, 0.5, seed=99)
    assert r1 != r2

def test_dropout_some_zeroed():
    """drop_rate=0.5 大输入下应有一部分置零"""
    a = [1.0] * 100
    r = apply_dropout(a, 0.5, seed=42)
    zeros = sum(1 for v in r if v == 0.0)
    # 期望约 50% 置零, 允许 20-80 范围
    assert 20 < zeros < 80

def test_dropout_kept_scaled():
    """被保留的元素乘 1/(1-drop_rate)"""
    a = [1.0] * 100
    r = apply_dropout(a, 0.5, seed=42)
    # 非零元素应该等于 1 / (1 - 0.5) = 2.0
    non_zeros = [v for v in r if v != 0.0]
    for v in non_zeros:
        assert abs(v - 2.0) < TOL

def test_dropout_raises_on_invalid_rate():
    with pytest.raises(ValueError):
        apply_dropout([1, 2], 1.0, seed=0)

def test_dropout_raises_on_empty():
    with pytest.raises(ValueError):
        apply_dropout([], 0.5, seed=0)

def test_dropout_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_dropout("ab", 0.5, seed=0)


# ============================================================
# F4: check_overfit_signal (4 键 dict)
# ============================================================

def test_cos_healthy():
    """train ↘ val ↘ → has_overfit=False, gap 小"""
    train = [0.8, 0.6, 0.4, 0.3, 0.25, 0.22, 0.20, 0.18, 0.17, 0.16]
    val = [0.85, 0.65, 0.45, 0.35, 0.30, 0.27, 0.25, 0.23, 0.22, 0.21]
    r = check_overfit_signal(train, val, patience=3)
    assert r["has_overfit"] is False
    assert r["best_val_epoch"] == 9
    assert r["is_diverging"] is False

def test_cos_overfit():
    """val 在 epoch 4 最低后开始上升, patience=3 → has_overfit=True"""
    train = [0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.10, 0.08, 0.06, 0.05]
    val = [0.85, 0.65, 0.45, 0.40, 0.38, 0.42, 0.45, 0.48, 0.50, 0.52]
    r = check_overfit_signal(train, val, patience=3)
    assert r["has_overfit"] is True
    assert r["best_val_epoch"] == 4
    assert r["is_diverging"] is True  # 0.52 / 0.38 - 1 ≈ 0.37 ≥ 10%

def test_cos_gap_signed():
    """gap = train[-1] - val[-1]"""
    train = [0.5, 0.3]
    val = [0.5, 0.4]
    r = check_overfit_signal(train, val, patience=2)
    assert abs(r["gap"] - (0.3 - 0.4)) < TOL

def test_cos_best_val_first():
    """val 第一个 epoch 就是最低 → best_val_epoch=0"""
    train = [0.5, 0.4, 0.3]
    val = [0.3, 0.4, 0.5]
    r = check_overfit_signal(train, val, patience=2)
    assert r["best_val_epoch"] == 0

def test_cos_diverging_false_small_uptick():
    """val 末尾仅小幅上升 (< 10%) → is_diverging=False"""
    train = [0.4, 0.3, 0.2]
    val = [0.35, 0.30, 0.31]  # 0.31 / 0.30 - 1 ≈ 3.3%
    r = check_overfit_signal(train, val, patience=2)
    assert r["is_diverging"] is False

def test_cos_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        check_overfit_signal([0.5, 0.3], [0.5], patience=2)

def test_cos_raises_on_empty():
    with pytest.raises(ValueError):
        check_overfit_signal([], [], patience=2)

def test_cos_raises_on_non_list():
    with pytest.raises(TypeError):
        check_overfit_signal("ab", [0.5, 0.4], patience=2)
