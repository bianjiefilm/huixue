"""CV07 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv07 import (
    harris_response_single,
    sift_block_descriptor_dim,
    extrema_check_3x3,
    hessian_2x2_eigenvalues,
)

TOL = 1e-6


# F1: harris_response_single. R = (Ixx*Iyy - Ixy²) - k*(Ixx + Iyy)²
def test_harris_corner_strong():
    """Ixx=10, Iyy=10, Ixy=0, k=0.04 → det=100, trace=20, R = 100 - 0.04*400 = 84"""
    r = harris_response_single(10.0, 10.0, 0.0, 0.04)
    assert abs(r - 84.0) < TOL

def test_harris_flat_region():
    """全 0 → R = 0"""
    r = harris_response_single(0.0, 0.0, 0.0, 0.04)
    assert abs(r - 0.0) < TOL

def test_harris_edge_one_direction():
    """Ixx=100, Iyy=0.01, Ixy=0, k=0.04 → det=1, trace=100.01, R = 1 - 0.04*10002 ≈ -399.08"""
    r = harris_response_single(100.0, 0.01, 0.0, 0.04)
    expected = 1.0 - 0.04 * (100.01 ** 2)
    assert abs(r - expected) < TOL

def test_harris_with_cross_term():
    """Ixx=5, Iyy=5, Ixy=2, k=0.04 → det = 25 - 4 = 21, trace = 10, R = 21 - 0.04*100 = 17"""
    r = harris_response_single(5.0, 5.0, 2.0, 0.04)
    assert abs(r - 17.0) < TOL

def test_harris_default_k():
    """k 默认应该是 0.04: Ixx=Iyy=2, Ixy=0 → det=4, trace=4, R = 4 - 0.04*16 = 3.36"""
    r = harris_response_single(2.0, 2.0, 0.0)
    assert abs(r - 3.36) < TOL

def test_harris_custom_k():
    """k=0.06: Ixx=Iyy=2, Ixy=0 → R = 4 - 0.06*16 = 3.04"""
    r = harris_response_single(2.0, 2.0, 0.0, 0.06)
    assert abs(r - 3.04) < TOL

def test_harris_raises_on_string():
    with pytest.raises(TypeError):
        harris_response_single("10", 10.0, 0.0, 0.04)


# F2: sift_block_descriptor_dim (num_orientations * num_blocks)
def test_sift_standard_8x16():
    """标准 SIFT (8, 16) → 128"""
    assert sift_block_descriptor_dim(8, 16) == 128

def test_sift_smaller_4x16():
    """(4, 16) → 64"""
    assert sift_block_descriptor_dim(4, 16) == 64

def test_sift_8x8():
    """(8, 8) → 64"""
    assert sift_block_descriptor_dim(8, 8) == 64

def test_sift_larger_16x16():
    """(16, 16) → 256"""
    assert sift_block_descriptor_dim(16, 16) == 256

def test_sift_minimum():
    """(1, 1) → 1 (boundary)"""
    assert sift_block_descriptor_dim(1, 1) == 1

def test_sift_raises_on_zero():
    with pytest.raises(ValueError):
        sift_block_descriptor_dim(0, 16)

def test_sift_raises_on_negative():
    with pytest.raises(ValueError):
        sift_block_descriptor_dim(8, -1)

def test_sift_raises_on_non_int():
    with pytest.raises(TypeError):
        sift_block_descriptor_dim(8.0, 16)


# F3: extrema_check_3x3 (strictly > all 8 neighbors → max, strictly < → min, else neither)
def test_extrema_max():
    """中心最大: 中心=10, 邻居都 < 10"""
    w = [[1, 2, 3], [4, 10, 5], [6, 7, 8]]
    assert extrema_check_3x3(w) == "max"

def test_extrema_min():
    """中心最小: 中心=-1, 邻居都 > -1"""
    w = [[1, 2, 3], [4, -1, 5], [6, 7, 8]]
    assert extrema_check_3x3(w) == "min"

def test_extrema_neither_tied_max():
    """中心 = 一个邻居 (不严格 > ): neither"""
    w = [[1, 2, 3], [4, 5, 5], [6, 7, 8]]
    assert extrema_check_3x3(w) == "neither"

def test_extrema_neither_tied_min():
    """中心 = 邻居 (相等不算 strict min)"""
    w = [[1, 1, 3], [4, 1, 5], [6, 7, 8]]
    assert extrema_check_3x3(w) == "neither"

def test_extrema_neither_middle():
    """中心既不最大也不最小"""
    w = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert extrema_check_3x3(w) == "neither"

def test_extrema_max_negative():
    """中心 -1 是最大 (其他更小)"""
    w = [[-2, -3, -4], [-5, -1, -6], [-7, -8, -9]]
    assert extrema_check_3x3(w) == "max"

def test_extrema_raises_on_wrong_shape():
    with pytest.raises(ValueError):
        extrema_check_3x3([[1, 2], [3, 4]])  # 2x2

def test_extrema_raises_on_non_list():
    with pytest.raises(TypeError):
        extrema_check_3x3("not a list")


# F4: hessian_2x2_eigenvalues. λ = ((a+d) ± sqrt((a-d)² + 4b²)) / 2, big first
def test_hessian_with_offdiag_symmetric():
    """a=2, b=1, d=2 → ((4) ± sqrt(0+4))/2 = (4±2)/2 = 3, 1"""
    l1, l2 = hessian_2x2_eigenvalues(2.0, 1.0, 2.0)
    assert abs(l1 - 3.0) < TOL
    assert abs(l2 - 1.0) < TOL

def test_hessian_with_offdiag_general():
    """a=4, b=2, d=1 → trace=5, sqrt((4-1)²+4·4)=sqrt(25)=5 → (5±5)/2 = 5, 0 (boundary 0 特征值)"""
    l1, l2 = hessian_2x2_eigenvalues(4.0, 2.0, 1.0)
    assert abs(l1 - 5.0) < TOL
    assert abs(l2 - 0.0) < TOL

def test_hessian_offdiag_3():
    """a=5, b=2, d=2 → trace=7, sqrt(9+16)=5 → (7±5)/2 = 6, 1"""
    l1, l2 = hessian_2x2_eigenvalues(5.0, 2.0, 2.0)
    assert abs(l1 - 6.0) < TOL
    assert abs(l2 - 1.0) < TOL

def test_hessian_ordering():
    """大值在前: a=1, b=2, d=4 → trace=5, sqrt(9+16)=5 → (5±5)/2 = 5, 0"""
    l1, l2 = hessian_2x2_eigenvalues(1.0, 2.0, 4.0)
    assert abs(l1 - 5.0) < TOL
    assert abs(l2 - 0.0) < TOL

def test_hessian_negative_eigenvalues():
    """a=-1, b=2, d=-4 → trace=-5, sqrt(9+16)=5 → (-5±5)/2 = 0, -5"""
    l1, l2 = hessian_2x2_eigenvalues(-1.0, 2.0, -4.0)
    assert abs(l1 - 0.0) < TOL
    assert abs(l2 - (-5.0)) < TOL

def test_hessian_raises_on_string():
    with pytest.raises(TypeError):
        hessian_2x2_eigenvalues("1", 0.0, 1.0)
