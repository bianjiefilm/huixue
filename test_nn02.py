"""NN02 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn02 import (
    sigmoid_activation,
    tanh_activation,
    relu_activation,
    leaky_relu_activation,
)

TOL = 1e-4


# ============================================================
# F1: sigmoid (transform 类, 多元独特 + 极值 防 0.5 hardcode)
# ============================================================

def test_sig_five_diverse():
    """[0, 1, -1, 2, -2] → [0.5, 0.7311, 0.2689, 0.8808, 0.1192]"""
    r = sigmoid_activation([0, 1, -1, 2, -2])
    expected = [0.5, 0.7310585786, 0.2689414214, 0.8807970779, 0.1192029221]
    assert len(r) == 5
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sig_extreme_positive():
    """[10, 100] 极正值 → 接近 1.0"""
    r = sigmoid_activation([10, 100])
    assert abs(r[0] - 0.9999546) < TOL
    assert abs(r[1] - 1.0) < TOL

def test_sig_extreme_negative():
    """[-10, -100] 极负值 → 接近 0.0"""
    r = sigmoid_activation([-10, -100])
    assert abs(r[0] - 0.0000453979) < TOL
    assert abs(r[1] - 0.0) < TOL

def test_sig_half_values():
    """[0.5, -0.5, 1.5, -1.5] 非整数"""
    r = sigmoid_activation([0.5, -0.5, 1.5, -1.5])
    expected = [0.6224593312, 0.3775406688, 0.8175744762, 0.1824255238]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sig_empty():
    """边界: 空列表 → 空列表"""
    assert sigmoid_activation([]) == []

def test_sig_raises_on_non_list():
    with pytest.raises(TypeError):
        sigmoid_activation("abc")

def test_sig_raises_on_non_numeric():
    with pytest.raises(TypeError):
        sigmoid_activation([1, "a", 2])


# ============================================================
# F2: tanh (transform 类)
# ============================================================

def test_tanh_diverse():
    """[0, 1, -1, 2, -2] → [0, 0.7616, -0.7616, 0.9640, -0.9640]"""
    r = tanh_activation([0, 1, -1, 2, -2])
    expected = [0.0, 0.7615941560, -0.7615941560, 0.9640275801, -0.9640275801]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_tanh_one_nontrivial():
    """tanh(1) ≈ 0.7616 (避 tanh(0)=0 与 identity 巧合)"""
    r = tanh_activation([1])
    assert abs(r[0] - 0.7615941560) < TOL

def test_tanh_extreme():
    """[10, -10] → 接近 ±1"""
    r = tanh_activation([10, -10])
    assert abs(r[0] - 1.0) < TOL
    assert abs(r[1] - (-1.0)) < TOL

def test_tanh_symmetric():
    """tanh(z) = -tanh(-z): [0.5, -0.5] → [a, -a]"""
    r = tanh_activation([0.5, -0.5])
    assert abs(r[0] - 0.4621171573) < TOL
    assert abs(r[1] - (-0.4621171573)) < TOL

def test_tanh_empty():
    assert tanh_activation([]) == []

def test_tanh_raises_on_non_list():
    with pytest.raises(TypeError):
        tanh_activation("abc")

def test_tanh_raises_on_non_numeric():
    with pytest.raises(TypeError):
        tanh_activation([1, None, 2])


# ============================================================
# F3: ReLU (transform 类, 多元独特防 0 hardcode)
# ============================================================

def test_relu_mixed():
    """[-2, 0, 1, 5, -10, 0.5] → [0, 0, 1, 5, 0, 0.5]"""
    r = relu_activation([-2, 0, 1, 5, -10, 0.5])
    expected = [0.0, 0.0, 1.0, 5.0, 0.0, 0.5]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_relu_negatives_zeroed():
    """[-1, -2, -3] 全负 → [0, 0, 0] (identity 必失败)"""
    r = relu_activation([-1, -2, -3])
    for v in r:
        assert abs(v - 0.0) < TOL

def test_relu_zero_boundary():
    """边界: [0, -0.0001, 0.0001] → [0, 0, 0.0001]"""
    r = relu_activation([0.0, -0.0001, 0.0001])
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 0.0) < TOL
    assert abs(r[2] - 0.0001) < TOL

def test_relu_large_negative():
    """[-100, 100] → [0, 100] (含负, 防 identity)"""
    r = relu_activation([-100, 100])
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 100.0) < TOL

def test_relu_with_decimals():
    """[-0.5, 0.5] → [0, 0.5]"""
    r = relu_activation([-0.5, 0.5])
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 0.5) < TOL

def test_relu_empty():
    assert relu_activation([]) == []

def test_relu_raises_on_non_list():
    with pytest.raises(TypeError):
        relu_activation("abc")

def test_relu_raises_on_non_numeric():
    with pytest.raises(TypeError):
        relu_activation([1, "a"])


# ============================================================
# F4: Leaky ReLU (transform 类, alpha 参数化)
# ============================================================

def test_lrelu_default_alpha():
    """默认 alpha=0.01: [-10, 0, 10] → [-0.1, 0, 10]"""
    r = leaky_relu_activation([-10, 0, 10])
    expected = [-0.1, 0.0, 10.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_lrelu_alpha_01():
    """alpha=0.1: [-5, 5] → [-0.5, 5]"""
    r = leaky_relu_activation([-5, 5], alpha=0.1)
    assert abs(r[0] - (-0.5)) < TOL
    assert abs(r[1] - 5.0) < TOL

def test_lrelu_alpha_05():
    """alpha=0.5: [-2, 0, 2] → [-1, 0, 2]"""
    r = leaky_relu_activation([-2, 0, 2], alpha=0.5)
    expected = [-1.0, 0.0, 2.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_lrelu_alpha_zero_equals_relu():
    """alpha=0: 退化为 ReLU"""
    r = leaky_relu_activation([-3, -1, 0, 1, 3], alpha=0.0)
    expected = [0.0, 0.0, 0.0, 1.0, 3.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_lrelu_mixed_decimals():
    """alpha=0.01: [-100, -1, 0, 1, 100] → [-1.0, -0.01, 0, 1, 100]"""
    r = leaky_relu_activation([-100, -1, 0, 1, 100], alpha=0.01)
    expected = [-1.0, -0.01, 0.0, 1.0, 100.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_lrelu_empty():
    assert leaky_relu_activation([]) == []

def test_lrelu_raises_on_non_list():
    with pytest.raises(TypeError):
        leaky_relu_activation("abc")

def test_lrelu_raises_on_non_numeric_alpha():
    with pytest.raises(TypeError):
        leaky_relu_activation([1, 2], alpha="x")
