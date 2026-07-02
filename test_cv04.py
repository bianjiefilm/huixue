"""CV04 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv04 import (
    apply_mean_filter,
    apply_median_filter,
    compute_gaussian_kernel_1d,
    apply_filter_1d,
)

TOL = 1e-6


# F1: apply_mean_filter
def test_mean_basic():
    assert abs(apply_mean_filter([1, 2, 3, 4, 5]) - 3.0) < TOL

def test_mean_with_outlier():
    """含异常值: [10, 20, 200] mean=76.67"""
    assert abs(apply_mean_filter([10, 20, 200]) - 230 / 3) < TOL

def test_mean_zeros():
    assert abs(apply_mean_filter([0, 0, 0]) - 0.0) < TOL

def test_mean_two_distinct():
    """两元素 [42, 100] mean=71 (避 identity 单元素巧合)"""
    assert abs(apply_mean_filter([42, 100]) - 71.0) < TOL

def test_mean_negative():
    assert abs(apply_mean_filter([-1, 1, 0]) - 0.0) < TOL

def test_mean_raises_on_empty():
    with pytest.raises(ValueError):
        apply_mean_filter([])

def test_mean_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_mean_filter("abc")


# F2: apply_median_filter
def test_med_odd():
    """[1, 2, 3, 4, 5] → 3"""
    assert abs(apply_median_filter([1, 2, 3, 4, 5]) - 3.0) < TOL

def test_med_even():
    """[1, 2, 3, 4] → (2+3)/2 = 2.5"""
    assert abs(apply_median_filter([1, 2, 3, 4]) - 2.5) < TOL

def test_med_outlier_ignored():
    """[10, 20, 200] → 20 (与 mean 76.67 不同, 中值滤波鲁棒)"""
    assert abs(apply_median_filter([10, 20, 200]) - 20) < TOL

def test_med_unsorted():
    """[5, 1, 3, 2, 4] → 3 (中值)"""
    assert abs(apply_median_filter([5, 1, 3, 2, 4]) - 3.0) < TOL

def test_med_two_distinct():
    """两元素 [42, 100] median=71 (避 identity 单元素巧合)"""
    assert abs(apply_median_filter([42, 100]) - 71.0) < TOL

def test_med_raises_on_empty():
    with pytest.raises(ValueError):
        apply_median_filter([])

def test_med_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_median_filter("abc")


# F3: compute_gaussian_kernel_1d (transform 类)
def test_gauss_size3_sigma1():
    """size=3 sigma=1: G(-1)≈0.2420, G(0)≈0.3989, G(1)≈0.2420
    归一化: sum=0.8829, [0.2741, 0.4519, 0.2741]"""
    k = compute_gaussian_kernel_1d(3, 1.0)
    assert len(k) == 3
    assert abs(sum(k) - 1.0) < TOL
    # 中心权重最大, 对称
    assert abs(k[0] - k[2]) < TOL
    assert k[1] > k[0]

def test_gauss_size1():
    """size=1 → [1.0]"""
    k = compute_gaussian_kernel_1d(1, 1.0)
    assert k == [1.0]

def test_gauss_size5_sigma1():
    """size=5 sigma=1: 对称 + 总和 1"""
    k = compute_gaussian_kernel_1d(5, 1.0)
    assert len(k) == 5
    assert abs(sum(k) - 1.0) < TOL
    # 对称
    assert abs(k[0] - k[4]) < TOL
    assert abs(k[1] - k[3]) < TOL
    # 中心最大
    assert k[2] > k[1] > k[0]

def test_gauss_large_sigma():
    """大 sigma → 接近均匀"""
    k = compute_gaussian_kernel_1d(3, 10.0)
    assert abs(sum(k) - 1.0) < TOL
    # 接近均匀 [0.333, 0.333, 0.333]
    for v in k:
        assert abs(v - 1 / 3) < 0.05

def test_gauss_small_sigma():
    """小 sigma → 集中中心"""
    k = compute_gaussian_kernel_1d(3, 0.1)
    assert abs(sum(k) - 1.0) < TOL
    # 中心 ≈ 1, 两侧 ≈ 0
    assert k[1] > 0.99

def test_gauss_raises_on_even_size():
    with pytest.raises(ValueError):
        compute_gaussian_kernel_1d(4, 1.0)

def test_gauss_raises_on_zero_sigma():
    with pytest.raises(ValueError):
        compute_gaussian_kernel_1d(3, 0)

def test_gauss_raises_on_non_int_size():
    with pytest.raises(TypeError):
        compute_gaussian_kernel_1d(3.0, 1.0)


# F4: apply_filter_1d (transform 类)
def test_f1d_simple():
    """values=[1,2,3], kernel=[1,1] → [1+2, 2+3] = [3, 5]"""
    r = apply_filter_1d([1, 2, 3], [1, 1])
    assert r == [3, 5]

def test_f1d_identity_kernel():
    """kernel=[1] → 输出 = 输入"""
    r = apply_filter_1d([1, 2, 3], [1])
    assert r == [1, 2, 3]

def test_f1d_average_kernel():
    """values=[1,2,3,4,5], kernel=[1/3,1/3,1/3] → [2, 3, 4]"""
    r = apply_filter_1d([1, 2, 3, 4, 5], [1 / 3, 1 / 3, 1 / 3])
    assert len(r) == 3
    for i, e in enumerate([2.0, 3.0, 4.0]):
        assert abs(r[i] - e) < TOL

def test_f1d_kernel_equals_input():
    """kernel 长度 = values, 输出长度 1"""
    r = apply_filter_1d([1, 2, 3], [0.5, 0.5, 0.5])
    assert len(r) == 1
    assert abs(r[0] - 0.5 * (1 + 2 + 3)) < TOL

def test_f1d_negative_kernel():
    """kernel 含负值"""
    r = apply_filter_1d([1, 2, 3, 4], [1, -1])
    # y0 = 1*1 + (-1)*2 = -1
    # y1 = 1*2 + (-1)*3 = -1
    # y2 = 1*3 + (-1)*4 = -1
    assert r == [-1, -1, -1]

def test_f1d_raises_on_kernel_too_long():
    with pytest.raises(ValueError):
        apply_filter_1d([1, 2], [1, 1, 1])

def test_f1d_raises_on_empty():
    with pytest.raises(ValueError):
        apply_filter_1d([], [])

def test_f1d_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_filter_1d("ab", [1])
