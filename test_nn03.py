"""NN03 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn03 import (
    linear_forward,
    linear_forward_batch,
    binary_cross_entropy,
    categorical_cross_entropy,
)

TOL = 1e-4


# ============================================================
# F1: linear_forward (单神经元)
# ============================================================

def test_lf_textbook():
    """x=[1,2], w=[0.5,-0.3], b=0.1 → 0.5-0.6+0.1 = 0.0"""
    assert abs(linear_forward([1, 2], [0.5, -0.3], 0.1) - 0.0) < TOL

def test_lf_simple_doubling():
    """x=[3], w=[2.0], b=0 → 6"""
    assert abs(linear_forward([3], [2.0], 0.0) - 6.0) < TOL

def test_lf_only_bias():
    """x=[0,0], w=[1,2], b=5 → 5"""
    assert abs(linear_forward([0, 0], [1.0, 2.0], 5.0) - 5.0) < TOL

def test_lf_three_features():
    """x=[1,1,1], w=[0.5,0.5,0.5], b=0.5 → 2.0"""
    assert abs(linear_forward([1, 1, 1], [0.5, 0.5, 0.5], 0.5) - 2.0) < TOL

def test_lf_negative_result():
    """x=[2], w=[-1], b=0 → -2"""
    assert abs(linear_forward([2], [-1.0], 0.0) - (-2.0)) < TOL

def test_lf_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        linear_forward([1, 2], [0.5], 0.0)

def test_lf_raises_on_empty():
    with pytest.raises(ValueError):
        linear_forward([], [], 0.0)

def test_lf_raises_on_non_list():
    with pytest.raises(TypeError):
        linear_forward("ab", [0.5, 0.5], 0.0)


# ============================================================
# F2: linear_forward_batch (transform 类)
# ============================================================

def test_lfb_textbook():
    """X=[[1,2]], W=[[3],[4]], b=[5] → [[1*3+2*4+5]] = [[16]]"""
    r = linear_forward_batch([[1, 2]], [[3], [4]], [5])
    assert len(r) == 1 and len(r[0]) == 1
    assert abs(r[0][0] - 16.0) < TOL

def test_lfb_two_samples_two_outputs():
    """X=[[1,0],[0,1]], W=[[1,2],[3,4]], b=[0,0] → [[1,2],[3,4]]"""
    r = linear_forward_batch([[1, 0], [0, 1]], [[1, 2], [3, 4]], [0, 0])
    assert abs(r[0][0] - 1.0) < TOL
    assert abs(r[0][1] - 2.0) < TOL
    assert abs(r[1][0] - 3.0) < TOL
    assert abs(r[1][1] - 4.0) < TOL

def test_lfb_with_bias_broadcast():
    """X=[[1,1]], W=[[1],[1]], b=[10] → [[12]]"""
    r = linear_forward_batch([[1, 1]], [[1], [1]], [10])
    assert abs(r[0][0] - 12.0) < TOL

def test_lfb_three_samples_one_output():
    """X=[[1],[2],[3]], W=[[2]], b=[1] → [[3],[5],[7]]"""
    r = linear_forward_batch([[1], [2], [3]], [[2]], [1])
    expected = [[3.0], [5.0], [7.0]]
    for i in range(3):
        assert abs(r[i][0] - expected[i][0]) < TOL

def test_lfb_zero_input():
    """X=[[0,0,0]], W=[[1],[2],[3]], b=[7] → [[7]]"""
    r = linear_forward_batch([[0, 0, 0]], [[1], [2], [3]], [7])
    assert abs(r[0][0] - 7.0) < TOL

def test_lfb_raises_on_dim_mismatch():
    """X 列数 ≠ W 行数"""
    with pytest.raises(ValueError):
        linear_forward_batch([[1, 2]], [[1]], [0])

def test_lfb_raises_on_empty():
    with pytest.raises(ValueError):
        linear_forward_batch([], [[1]], [0])

def test_lfb_raises_on_non_list():
    with pytest.raises(TypeError):
        linear_forward_batch("abc", [[1]], [0])


# ============================================================
# F3: binary_cross_entropy
# ============================================================

def test_bce_perfect():
    """y=[1,0], p=[1,0] → ~0 (concept: log(1)=0)"""
    r = binary_cross_entropy([1, 0], [0.99999999, 0.00000001])
    assert abs(r - 0.0) < TOL

def test_bce_uniform_half():
    """y=[1,0], p=[0.5,0.5] → -mean(log(0.5)+log(0.5)) = -log(0.5) = log(2) ≈ 0.6931"""
    r = binary_cross_entropy([1, 0], [0.5, 0.5])
    assert abs(r - 0.6931472) < TOL

def test_bce_known_specific():
    """y=[1,0,1,0], p=[0.9,0.1,0.8,0.2] → -mean(log0.9+log0.9+log0.8+log0.8)/4
    = -mean(-0.10536-0.10536-0.22314-0.22314)/4 = 0.16425"""
    r = binary_cross_entropy([1, 0, 1, 0], [0.9, 0.1, 0.8, 0.2])
    expected = -((math.log(0.9) + math.log(0.9) + math.log(0.8) + math.log(0.8)) / 4)
    assert abs(r - expected) < TOL

def test_bce_all_correct_high_conf():
    """y=[1,1,0,0], p=[0.99,0.99,0.01,0.01] → 接近 0 但非 0"""
    r = binary_cross_entropy([1, 1, 0, 0], [0.99, 0.99, 0.01, 0.01])
    expected = -(math.log(0.99) * 2 + math.log(0.99) * 2) / 4
    assert abs(r - expected) < TOL

def test_bce_extreme_zero_clipped():
    """y=[1], p=[0.0] 应被 clip, 不应 inf/nan"""
    r = binary_cross_entropy([1], [0.0])
    assert math.isfinite(r) and r > 0

def test_bce_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        binary_cross_entropy([1, 0], [0.5])

def test_bce_raises_on_empty():
    with pytest.raises(ValueError):
        binary_cross_entropy([], [])

def test_bce_raises_on_non_list():
    with pytest.raises(TypeError):
        binary_cross_entropy("01", "01")


# ============================================================
# F4: categorical_cross_entropy
# ============================================================

def test_cce_perfect():
    """y=[0,1,2], p=[[1,0,0],[0,1,0],[0,0,1]] (one-hot 完美) → ~0"""
    r = categorical_cross_entropy(
        [0, 1, 2],
        [[0.99999999, 1e-9, 1e-9], [1e-9, 0.99999999, 1e-9], [1e-9, 1e-9, 0.99999999]],
    )
    assert abs(r - 0.0) < TOL

def test_cce_uniform_3class():
    """3 class 均匀概率: 真值任意 → -log(1/3) = log(3) ≈ 1.0986"""
    r = categorical_cross_entropy(
        [0, 1, 2],
        [[1 / 3, 1 / 3, 1 / 3], [1 / 3, 1 / 3, 1 / 3], [1 / 3, 1 / 3, 1 / 3]],
    )
    assert abs(r - math.log(3)) < TOL

def test_cce_two_class():
    """2 class 等价 BCE: y=[0,1], p=[[0.7,0.3],[0.4,0.6]] → -mean(log0.7+log0.6)"""
    r = categorical_cross_entropy([0, 1], [[0.7, 0.3], [0.4, 0.6]])
    expected = -(math.log(0.7) + math.log(0.6)) / 2
    assert abs(r - expected) < TOL

def test_cce_specific_known():
    """y=[1,2,0], p=[[0.1,0.8,0.1],[0.2,0.3,0.5],[0.6,0.3,0.1]]
    → -mean(log0.8 + log0.5 + log0.6) / 3"""
    r = categorical_cross_entropy(
        [1, 2, 0],
        [[0.1, 0.8, 0.1], [0.2, 0.3, 0.5], [0.6, 0.3, 0.1]],
    )
    expected = -(math.log(0.8) + math.log(0.5) + math.log(0.6)) / 3
    assert abs(r - expected) < TOL

def test_cce_zero_clipped():
    """真实类概率为 0 应 clip, 不 inf"""
    r = categorical_cross_entropy([0], [[0.0, 0.5, 0.5]])
    assert math.isfinite(r) and r > 0

def test_cce_raises_on_index_out_of_range():
    with pytest.raises(ValueError):
        categorical_cross_entropy([5], [[0.5, 0.5]])

def test_cce_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        categorical_cross_entropy([0, 1], [[0.5, 0.5]])

def test_cce_raises_on_non_list():
    with pytest.raises(TypeError):
        categorical_cross_entropy("01", [[0.5, 0.5]])
