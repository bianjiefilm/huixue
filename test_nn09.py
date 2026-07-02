"""NN09 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn09 import (
    conv1d_single_step,
    compute_output_shape,
    max_pool_2x2,
    count_conv_params,
)

TOL = 1e-6


# F1: conv1d_single_step
def test_c1d_textbook():
    assert abs(conv1d_single_step([1, 2, 3], [0.5, -0.3, 0.1], 0.2) - (0.5*1 + (-0.3)*2 + 0.1*3 + 0.2)) < TOL

def test_c1d_only_bias():
    assert abs(conv1d_single_step([0, 0, 0], [1, 2, 3], 5.0) - 5.0) < TOL

def test_c1d_unit_kernel():
    """kernel=[1,1,1] 求和"""
    assert abs(conv1d_single_step([2, 3, 4], [1, 1, 1], 0) - 9.0) < TOL

def test_c1d_negative():
    """全负 kernel"""
    assert abs(conv1d_single_step([1, 2, 3], [-1, -1, -1], 0) - (-6.0)) < TOL

def test_c1d_single_element():
    """单元素 kernel"""
    assert abs(conv1d_single_step([5], [2], 1.0) - 11.0) < TOL

def test_c1d_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        conv1d_single_step([1, 2], [1], 0)

def test_c1d_raises_on_empty():
    with pytest.raises(ValueError):
        conv1d_single_step([], [], 0)

def test_c1d_raises_on_non_list():
    with pytest.raises(TypeError):
        conv1d_single_step("ab", [1, 2], 0)


# F2: compute_output_shape
def test_cos_basic():
    """N=10 K=3 P=0 S=1 → 8"""
    assert compute_output_shape(10, 3, 0, 1) == 8

def test_cos_same_padding():
    """N=10 K=3 P=1 S=1 → 10"""
    assert compute_output_shape(10, 3, 1, 1) == 10

def test_cos_stride_2():
    """N=10 K=3 P=0 S=2 → 4"""
    assert compute_output_shape(10, 3, 0, 2) == 4

def test_cos_large_input():
    """N=224 K=7 P=3 S=2 → (224+6-7)/2 + 1 = 112"""
    assert compute_output_shape(224, 7, 3, 2) == 112

def test_cos_K_equals_N():
    """N=5 K=5 P=0 S=1 → 1"""
    assert compute_output_shape(5, 5, 0, 1) == 1

def test_cos_raises_on_invalid():
    """K > N+2P → 输出 ≤ 0"""
    with pytest.raises(ValueError):
        compute_output_shape(3, 5, 0, 1)

def test_cos_raises_on_zero_stride():
    with pytest.raises(ValueError):
        compute_output_shape(10, 3, 0, 0)

def test_cos_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_output_shape(10.5, 3, 0, 1)


# F3: max_pool_2x2 (transform 类)
def test_mp_simple_2x2():
    """[[1,2],[3,4]] → [[4]]"""
    r = max_pool_2x2([[1, 2], [3, 4]])
    assert r == [[4]]

def test_mp_4x4():
    """[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]] → [[6,8],[14,16]]"""
    M = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    r = max_pool_2x2(M)
    assert r == [[6, 8], [14, 16]]

def test_mp_negative_values():
    """[[−1,−2],[−3,−4]] → [[-1]]"""
    r = max_pool_2x2([[-1, -2], [-3, -4]])
    assert r == [[-1]]

def test_mp_2x4():
    """[[1,2,3,4],[5,6,7,8]] → [[6,8]]"""
    r = max_pool_2x2([[1, 2, 3, 4], [5, 6, 7, 8]])
    assert r == [[6, 8]]

def test_mp_4x2():
    """[[1,2],[3,4],[5,6],[7,8]] → [[4],[8]]"""
    r = max_pool_2x2([[1, 2], [3, 4], [5, 6], [7, 8]])
    assert r == [[4], [8]]

def test_mp_raises_on_odd_size():
    with pytest.raises(ValueError):
        max_pool_2x2([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

def test_mp_raises_on_empty():
    with pytest.raises(ValueError):
        max_pool_2x2([])

def test_mp_raises_on_non_list():
    with pytest.raises(TypeError):
        max_pool_2x2("abc")


# F4: count_conv_params
def test_ccp_basic():
    """64 → 128, K=3 → 64*128*9 + 128 = 73856"""
    assert count_conv_params(64, 128, 3) == 73856

def test_ccp_first_conv():
    """3 → 32, K=3 → 3*32*9 + 32 = 896"""
    assert count_conv_params(3, 32, 3) == 896

def test_ccp_5x5_kernel():
    """3 → 16, K=5 → 3*16*25 + 16 = 1216"""
    assert count_conv_params(3, 16, 5) == 1216

def test_ccp_1x1_kernel():
    """64 → 32, K=1 → 64*32 + 32 = 2080"""
    assert count_conv_params(64, 32, 1) == 2080

def test_ccp_large_layer():
    """256 → 512, K=3 → 256*512*9 + 512 = 1180160"""
    assert count_conv_params(256, 512, 3) == 1180160

def test_ccp_raises_on_zero():
    with pytest.raises(ValueError):
        count_conv_params(0, 32, 3)

def test_ccp_raises_on_negative():
    with pytest.raises(ValueError):
        count_conv_params(3, -1, 3)

def test_ccp_raises_on_non_int():
    with pytest.raises(TypeError):
        count_conv_params(3.5, 32, 3)
