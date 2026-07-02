"""CV05 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv05 import (
    compute_sobel_x_kernel,
    compute_sobel_y_kernel,
    compute_gradient_magnitude,
    canny_threshold_classify,
)

TOL = 1e-6


# F1: compute_sobel_x_kernel
def test_sx_shape():
    k = compute_sobel_x_kernel()
    assert isinstance(k, list)
    assert len(k) == 3
    for row in k:
        assert isinstance(row, list)
        assert len(row) == 3

def test_sx_full_kernel():
    """Sobel-x 完整匹配"""
    k = compute_sobel_x_kernel()
    expected = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    for i in range(3):
        for j in range(3):
            assert k[i][j] == expected[i][j], f"k[{i}][{j}] expected {expected[i][j]}, got {k[i][j]}"

def test_sx_left_column_negative():
    """左列 [-1, -2, -1]"""
    k = compute_sobel_x_kernel()
    assert k[0][0] == -1
    assert k[1][0] == -2
    assert k[2][0] == -1

def test_sx_right_column_positive():
    """右列 [1, 2, 1]"""
    k = compute_sobel_x_kernel()
    assert k[0][2] == 1
    assert k[1][2] == 2
    assert k[2][2] == 1

def test_sx_middle_row_max_abs():
    """中间行权重绝对值更大: |k[1][0]|=2 > |k[0][0]|=1"""
    k = compute_sobel_x_kernel()
    assert abs(k[1][0]) == 2
    assert abs(k[1][2]) == 2


# F2: compute_sobel_y_kernel
def test_sy_shape():
    k = compute_sobel_y_kernel()
    assert isinstance(k, list)
    assert len(k) == 3
    for row in k:
        assert isinstance(row, list)
        assert len(row) == 3

def test_sy_full_kernel():
    """Sobel-y 完整匹配"""
    k = compute_sobel_y_kernel()
    expected = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    for i in range(3):
        for j in range(3):
            assert k[i][j] == expected[i][j], f"k[{i}][{j}] expected {expected[i][j]}, got {k[i][j]}"

def test_sy_top_row_negative():
    """顶行 [-1, -2, -1]"""
    k = compute_sobel_y_kernel()
    assert k[0][0] == -1
    assert k[0][1] == -2
    assert k[0][2] == -1

def test_sy_bottom_row_positive():
    """底行 [1, 2, 1]"""
    k = compute_sobel_y_kernel()
    assert k[2][0] == 1
    assert k[2][1] == 2
    assert k[2][2] == 1

def test_sy_middle_column_max_abs():
    """中间列权重绝对值更大"""
    k = compute_sobel_y_kernel()
    assert abs(k[0][1]) == 2
    assert abs(k[2][1]) == 2


# F3: compute_gradient_magnitude
def test_gm_pythagoras_3_4():
    """3, 4 → 5"""
    r = compute_gradient_magnitude(3.0, 4.0)
    assert abs(r - 5.0) < TOL

def test_gm_pythagoras_5_12():
    """5, 12 → 13"""
    r = compute_gradient_magnitude(5.0, 12.0)
    assert abs(r - 13.0) < TOL

def test_gm_pythagoras_8_15():
    """8, 15 → 17"""
    r = compute_gradient_magnitude(8.0, 15.0)
    assert abs(r - 17.0) < TOL

def test_gm_negative_pythagoras():
    """-3, -4 → 5 (平方消符号)"""
    r = compute_gradient_magnitude(-3.0, -4.0)
    assert abs(r - 5.0) < TOL

def test_gm_general_1_2():
    """1, 2 → sqrt(5) ≈ 2.2361"""
    r = compute_gradient_magnitude(1.0, 2.0)
    assert abs(r - math.sqrt(5.0)) < TOL

def test_gm_general_2_3():
    """2, 3 → sqrt(13) ≈ 3.6056"""
    r = compute_gradient_magnitude(2.0, 3.0)
    assert abs(r - math.sqrt(13.0)) < TOL

def test_gm_small_values():
    """0.0001, 0.0002 → sqrt(5e-8) (极小值边界)"""
    r = compute_gradient_magnitude(0.0001, 0.0002)
    assert abs(r - math.sqrt(5e-8)) < TOL

def test_gm_raises_on_string():
    with pytest.raises(TypeError):
        compute_gradient_magnitude("3", 4.0)


# F4: canny_threshold_classify
def test_cc_strong_above_high():
    """200, low=50, high=150 → strong"""
    assert canny_threshold_classify(200.0, 50.0, 150.0) == "strong"

def test_cc_strong_at_high():
    """150, low=50, high=150 → strong (>= 高阈值)"""
    assert canny_threshold_classify(150.0, 50.0, 150.0) == "strong"

def test_cc_strong_far_above():
    """500, low=50, high=150 → strong"""
    assert canny_threshold_classify(500.0, 50.0, 150.0) == "strong"

def test_cc_weak_between():
    """100, low=50, high=150 → weak"""
    assert canny_threshold_classify(100.0, 50.0, 150.0) == "weak"

def test_cc_weak_at_low():
    """50, low=50, high=150 → weak (>= 低阈值, 边界)"""
    assert canny_threshold_classify(50.0, 50.0, 150.0) == "weak"

def test_cc_non_edge_below_low():
    """30, low=50, high=150 → non_edge"""
    assert canny_threshold_classify(30.0, 50.0, 150.0) == "non_edge"

def test_cc_non_edge_zero():
    """0, low=50, high=150 → non_edge (boundary)"""
    assert canny_threshold_classify(0.0, 50.0, 150.0) == "non_edge"

def test_cc_non_edge_just_below_low():
    """49.999, low=50, high=150 → non_edge"""
    assert canny_threshold_classify(49.999, 50.0, 150.0) == "non_edge"

def test_cc_raises_on_low_ge_high():
    with pytest.raises(ValueError):
        canny_threshold_classify(100.0, 150.0, 100.0)

def test_cc_raises_on_negative_magnitude():
    with pytest.raises(ValueError):
        canny_threshold_classify(-10.0, 50.0, 150.0)

def test_cc_raises_on_string():
    with pytest.raises(TypeError):
        canny_threshold_classify("100", 50.0, 150.0)
