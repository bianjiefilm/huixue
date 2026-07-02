"""MJ02 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj02 import (
    compute_correlation,
    find_outliers_iqr,
    summarize_distribution,
    compute_quartiles,
)

TOL = 1e-6


# ============================================================
# F1: compute_correlation  (8 测试, 5 个独特数值期望 + 3 raises)
# ============================================================

def test_corr_perfect_positive():
    assert abs(compute_correlation([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < TOL

def test_corr_perfect_negative():
    assert abs(compute_correlation([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < TOL

def test_corr_known_value_0_8():
    """x=[1,2,3,4], y=[1,3,2,4] 的 Pearson r = 0.8 (手算验证)"""
    assert abs(compute_correlation([1, 2, 3, 4], [1, 3, 2, 4]) - 0.8) < TOL

def test_corr_zero():
    """x=[1,2,3,4,5], y=[1,4,5,4,1] 对称分布, r = 0.0"""
    assert abs(compute_correlation([1, 2, 3, 4, 5], [1, 4, 5, 4, 1]) - 0.0) < TOL

def test_corr_linear_scaled():
    """y = 2x, 应得 r = 1.0"""
    assert abs(compute_correlation([1, 2, 3, 4, 5], [2, 4, 6, 8, 10]) - 1.0) < TOL

def test_corr_raises_on_zero_variance():
    """边界: x 方差为 0 (全相同) → ValueError"""
    with pytest.raises(ValueError):
        compute_correlation([5, 5, 5, 5], [1, 2, 3, 4])

def test_corr_raises_on_length_mismatch():
    """边界: 长度不一致 → ValueError"""
    with pytest.raises(ValueError):
        compute_correlation([1, 2, 3], [1, 2])

def test_corr_raises_on_non_list():
    """负例: 非 list 输入 → TypeError"""
    with pytest.raises(TypeError):
        compute_correlation("abc", "xyz")


# ============================================================
# F2: find_outliers_iqr  (8 测试, 索引随输入变, 仅 1 个 [] 期望)
# ============================================================

def test_iqr_high_outlier():
    """[1,2,3,4,5,100] 中 100 是异常值, 索引 5"""
    assert find_outliers_iqr([1, 2, 3, 4, 5, 100]) == [5]

def test_iqr_low_outlier():
    """[-100,1,2,3,4,5] 中 -100 是异常值, 索引 0"""
    assert find_outliers_iqr([-100, 1, 2, 3, 4, 5]) == [0]

def test_iqr_both_extremes():
    """[1,2,3,4,5,100,-50] 两端各一异常, 升序索引 [5,6]"""
    assert find_outliers_iqr([1, 2, 3, 4, 5, 100, -50]) == [5, 6]

def test_iqr_no_outliers():
    """无异常值 → 空列表"""
    assert find_outliers_iqr([1, 2, 3, 4, 5]) == []

def test_iqr_middle_extreme():
    """[10,20,1000,30,40] 中 1000 在索引 2"""
    assert find_outliers_iqr([10, 20, 1000, 30, 40]) == [2]

def test_iqr_two_high_outliers():
    """密集正常值+末尾两极端: 200 与 300 都是异常 (索引 9,10)"""
    assert find_outliers_iqr([1, 2, 2, 3, 3, 3, 4, 4, 5, 200, 300]) == [9, 10]

def test_iqr_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        find_outliers_iqr([])

def test_iqr_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        find_outliers_iqr("abc")


# ============================================================
# F3: summarize_distribution  (7 测试, dict 4 键全验)
# ============================================================

def test_summary_basic():
    r = summarize_distribution([1, 2, 3, 4, 5])
    assert abs(r["mean"] - 3.0) < TOL
    assert abs(r["median"] - 3.0) < TOL
    assert abs(r["std"] - 1.4142135) < 1e-4  # sqrt(2)
    assert abs(r["range"] - 4.0) < TOL

def test_summary_constant():
    """边界: 全相同值, std=0, range=0"""
    r = summarize_distribution([7, 7, 7, 7])
    assert abs(r["mean"] - 7.0) < TOL
    assert abs(r["median"] - 7.0) < TOL
    assert abs(r["std"] - 0.0) < TOL
    assert abs(r["range"] - 0.0) < TOL

def test_summary_signed():
    r = summarize_distribution([-5, -1, 0, 1, 5])
    assert abs(r["mean"] - 0.0) < TOL
    assert abs(r["median"] - 0.0) < TOL
    assert abs(r["range"] - 10.0) < TOL
    # std = sqrt(((-5)^2 + (-1)^2 + 0 + 1 + 25)/5) = sqrt(52/5) ≈ 3.2249
    assert abs(r["std"] - 3.22490309) < 1e-4

def test_summary_single_element():
    """边界: 单元素"""
    r = summarize_distribution([42])
    assert abs(r["mean"] - 42.0) < TOL
    assert abs(r["median"] - 42.0) < TOL
    assert abs(r["std"] - 0.0) < TOL
    assert abs(r["range"] - 0.0) < TOL

def test_summary_even_count_median():
    """偶数个元素, median 取中间两个的平均"""
    r = summarize_distribution([1, 2, 3, 4, 5, 6])
    assert abs(r["mean"] - 3.5) < TOL
    assert abs(r["median"] - 3.5) < TOL
    assert abs(r["range"] - 5.0) < TOL

def test_summary_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        summarize_distribution([])

def test_summary_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        summarize_distribution("abc")


# ============================================================
# F4: compute_quartiles (transform 类, 用未排序输入防 D 攻击巧合)
# ============================================================

def test_quartiles_unsorted_5():
    """未排序输入 [3,1,4,1,5] 的 5-num = [1,1,3,4,5]"""
    r = compute_quartiles([3, 1, 4, 1, 5])
    assert len(r) == 5
    expected = [1.0, 1.0, 3.0, 4.0, 5.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL, f"index {i}: expected {e}, got {r[i]}"

def test_quartiles_ten_values():
    """10 元素, numpy 默认线性插值"""
    r = compute_quartiles([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    assert len(r) == 5
    expected = [10.0, 32.5, 55.0, 77.5, 100.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_quartiles_single_element():
    """边界: 单元素 → 5 个值都等于该元素"""
    r = compute_quartiles([42])
    assert len(r) == 5
    for v in r:
        assert abs(v - 42.0) < TOL

def test_quartiles_constant():
    """边界: 全相同 → 5 个值全等"""
    r = compute_quartiles([3, 3, 3, 3])
    assert len(r) == 5
    for v in r:
        assert abs(v - 3.0) < TOL

def test_quartiles_two_values():
    """2 元素 [0, 100] → [0, 25, 50, 75, 100]"""
    r = compute_quartiles([0, 100])
    assert len(r) == 5
    expected = [0.0, 25.0, 50.0, 75.0, 100.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_quartiles_negative_values_unsorted():
    """未排序负值 [10, -10, 5, -5, 0] 的 5-num = [-10,-5,0,5,10] (防 D 攻击巧合)"""
    r = compute_quartiles([10, -10, 5, -5, 0])
    assert len(r) == 5
    expected = [-10.0, -5.0, 0.0, 5.0, 10.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_quartiles_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        compute_quartiles([])

def test_quartiles_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        compute_quartiles("abc")
