"""NN04 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn04 import (
    sigmoid_derivative,
    compute_mse_gradient,
    linear_backward_single,
    gradient_descent_step,
)

TOL = 1e-4


# ============================================================
# F1: sigmoid_derivative (transform 类)
# ============================================================

def test_sd_zero_max():
    """σ'(0) = 0.5*0.5 = 0.25 (最大值)"""
    r = sigmoid_derivative([0])
    assert abs(r[0] - 0.25) < TOL

def test_sd_diverse():
    """[0, 1, -1, 2, -2] 多组独特"""
    r = sigmoid_derivative([0, 1, -1, 2, -2])
    # σ(0)=0.5, σ'(0)=0.25
    # σ(1)≈0.7311, σ'(1)≈0.7311*0.2689≈0.1966
    # σ(-1)≈0.2689, σ'(-1)≈0.2689*0.7311≈0.1966
    # σ(2)≈0.8808, σ'(2)≈0.1050
    # σ(-2)≈0.1192, σ'(-2)≈0.1050
    expected = [0.25, 0.19661193, 0.19661193, 0.10499359, 0.10499359]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sd_extreme_saturation():
    """[10, -10] 饱和区 σ' 接近 0"""
    r = sigmoid_derivative([10, -10])
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 0.0) < TOL

def test_sd_half_values():
    """[0.5, -0.5]"""
    r = sigmoid_derivative([0.5, -0.5])
    # σ(0.5)≈0.6225, σ'≈0.2350
    expected = [0.23500371, 0.23500371]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sd_empty():
    assert sigmoid_derivative([]) == []

def test_sd_raises_on_non_list():
    with pytest.raises(TypeError):
        sigmoid_derivative("abc")

def test_sd_raises_on_non_numeric():
    with pytest.raises(TypeError):
        sigmoid_derivative([1, "a"])


# ============================================================
# F2: compute_mse_gradient (transform 类)
# ============================================================

def test_mg_perfect():
    """y_pred = y_true → 梯度 = 0"""
    r = compute_mse_gradient([1, 2, 3], [1, 2, 3])
    for v in r:
        assert abs(v - 0.0) < TOL

def test_mg_known():
    """y_true=[3,5], y_pred=[5,3] → 2(y_pred-y_true)/2 = (2, -2)"""
    r = compute_mse_gradient([3, 5], [5, 3])
    assert abs(r[0] - 2.0) < TOL
    assert abs(r[1] - (-2.0)) < TOL

def test_mg_four_samples():
    """y_true=[0,0,0,0], y_pred=[1,2,3,4] → 2(y_pred-0)/4 = (0.5,1,1.5,2)"""
    r = compute_mse_gradient([0, 0, 0, 0], [1, 2, 3, 4])
    expected = [0.5, 1.0, 1.5, 2.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_mg_negative_pred():
    """y_true=[5], y_pred=[3] → 2(3-5)/1 = -4"""
    r = compute_mse_gradient([5], [3])
    assert abs(r[0] - (-4.0)) < TOL

def test_mg_floats():
    """y_true=[1.5, 2.5], y_pred=[2.0, 2.0] → 2(0.5, -0.5)/2 = (0.5, -0.5)"""
    r = compute_mse_gradient([1.5, 2.5], [2.0, 2.0])
    assert abs(r[0] - 0.5) < TOL
    assert abs(r[1] - (-0.5)) < TOL

def test_mg_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        compute_mse_gradient([1, 2], [1])

def test_mg_raises_on_empty():
    with pytest.raises(ValueError):
        compute_mse_gradient([], [])

def test_mg_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_mse_gradient("abc", "def")


# ============================================================
# F3: linear_backward_single (transform 类, multi-output tuple)
# ============================================================

def test_lbs_textbook():
    """dz=2, x=[3,4], w=[1,1] → dw=[6,8], dx=[2,2], db=2"""
    dw, dx, db = linear_backward_single(2.0, [3, 4], [1, 1])
    assert abs(dw[0] - 6.0) < TOL and abs(dw[1] - 8.0) < TOL
    assert abs(dx[0] - 2.0) < TOL and abs(dx[1] - 2.0) < TOL
    assert abs(db - 2.0) < TOL

def test_lbs_unit_dz():
    """dz=1, x=[1,2,3], w=[0.5,0.5,0.5] → dw=[1,2,3], dx=[0.5,0.5,0.5], db=1"""
    dw, dx, db = linear_backward_single(1.0, [1, 2, 3], [0.5, 0.5, 0.5])
    expected_dw = [1.0, 2.0, 3.0]
    expected_dx = [0.5, 0.5, 0.5]
    for i in range(3):
        assert abs(dw[i] - expected_dw[i]) < TOL
        assert abs(dx[i] - expected_dx[i]) < TOL
    assert abs(db - 1.0) < TOL

def test_lbs_negative_dz():
    """dz=-3, x=[2], w=[5] → dw=[-6], dx=[-15], db=-3"""
    dw, dx, db = linear_backward_single(-3.0, [2], [5])
    assert abs(dw[0] - (-6.0)) < TOL
    assert abs(dx[0] - (-15.0)) < TOL
    assert abs(db - (-3.0)) < TOL

def test_lbs_zero_dz():
    """dz=0 → 所有梯度都是 0"""
    dw, dx, db = linear_backward_single(0.0, [1, 2, 3], [4, 5, 6])
    for v in dw:
        assert abs(v - 0.0) < TOL
    for v in dx:
        assert abs(v - 0.0) < TOL
    assert abs(db - 0.0) < TOL

def test_lbs_zero_x():
    """x=[0,0], w=[1,2] → dw=[0,0], dx=[dz,2dz], db=dz"""
    dw, dx, db = linear_backward_single(2.0, [0, 0], [1, 2])
    assert abs(dw[0] - 0.0) < TOL and abs(dw[1] - 0.0) < TOL
    assert abs(dx[0] - 2.0) < TOL and abs(dx[1] - 4.0) < TOL
    assert abs(db - 2.0) < TOL

def test_lbs_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        linear_backward_single(1.0, [1, 2], [3])

def test_lbs_raises_on_empty():
    with pytest.raises(ValueError):
        linear_backward_single(1.0, [], [])

def test_lbs_raises_on_non_list():
    with pytest.raises(TypeError):
        linear_backward_single(1.0, "abc", [1, 2])


# ============================================================
# F4: gradient_descent_step (transform 类)
# ============================================================

def test_gds_textbook():
    """params=[0.5, 1.0], grads=[-40, -4], lr=0.01 → [0.9, 1.04]"""
    r = gradient_descent_step([0.5, 1.0], [-40, -4], 0.01)
    assert abs(r[0] - 0.9) < TOL
    assert abs(r[1] - 1.04) < TOL

def test_gds_multiple_params():
    """params=[1,2,3], grads=[0.1,0.2,0.3], lr=10 → [0, 0, 0]"""
    r = gradient_descent_step([1, 2, 3], [0.1, 0.2, 0.3], 10.0)
    for i, e in enumerate([0.0, 0.0, 0.0]):
        assert abs(r[i] - e) < TOL

def test_gds_unit_step():
    """params=[10], grads=[5], lr=1 → [5]"""
    r = gradient_descent_step([10], [5], 1.0)
    assert abs(r[0] - 5.0) < TOL

def test_gds_negative_grad_increases():
    """grad 负 → param 增"""
    r = gradient_descent_step([5], [-2], 0.5)
    assert abs(r[0] - 6.0) < TOL  # 5 - 0.5*(-2) = 6

def test_gds_positive_grad_decreases():
    """grad 正 → param 减"""
    r = gradient_descent_step([5], [2], 0.5)
    assert abs(r[0] - 4.0) < TOL  # 5 - 0.5*2 = 4

def test_gds_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        gradient_descent_step([1, 2], [0.1], 0.01)

def test_gds_raises_on_empty():
    with pytest.raises(ValueError):
        gradient_descent_step([], [], 0.01)

def test_gds_raises_on_non_list():
    with pytest.raises(TypeError):
        gradient_descent_step("ab", [0.1, 0.2], 0.01)
