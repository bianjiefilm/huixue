"""MJ03 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj03 import (
    label_encode,
    z_score_standardize,
    fill_with_median,
    filter_low_variance,
)

TOL = 1e-6


# ============================================================
# F1: label_encode (8 测试, 双结构 list+dict 全验)
# ============================================================

def test_le_basic():
    encoded, mapping = label_encode(['cat', 'dog', 'cat', 'bird'])
    assert encoded == [1, 2, 1, 0]
    assert mapping == {'bird': 0, 'cat': 1, 'dog': 2}

def test_le_two_classes():
    encoded, mapping = label_encode(['x', 'y', 'x', 'y'])
    assert encoded == [0, 1, 0, 1]
    assert mapping == {'x': 0, 'y': 1}

def test_le_single_element():
    encoded, mapping = label_encode(['only'])
    assert encoded == [0]
    assert mapping == {'only': 0}

def test_le_all_same():
    encoded, mapping = label_encode(['a', 'a', 'a', 'a', 'a'])
    assert encoded == [0, 0, 0, 0, 0]
    assert mapping == {'a': 0}

def test_le_sorted_assignment():
    """关键: 编号基于去重排序"""
    encoded, mapping = label_encode(['z', 'a', 'm'])
    assert mapping == {'a': 0, 'm': 1, 'z': 2}
    assert encoded == [2, 0, 1]

def test_le_raises_on_empty():
    with pytest.raises(ValueError):
        label_encode([])

def test_le_raises_on_non_list():
    with pytest.raises(TypeError):
        label_encode("abc")

def test_le_raises_on_non_string_element():
    with pytest.raises(TypeError):
        label_encode(['a', 1, 'b'])


# ============================================================
# F2: z_score_standardize (8 测试)
# ============================================================

def test_zscore_basic():
    """[1,2,3,4,5] mean=3, std=sqrt(2), 中心元素 0.0"""
    r = z_score_standardize([1, 2, 3, 4, 5])
    expected = [-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356]
    assert len(r) == 5
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < 1e-4

def test_zscore_centered():
    """[-2,-1,0,1,2] 已中心化"""
    r = z_score_standardize([-2, -1, 0, 1, 2])
    expected = [-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356]
    assert len(r) == 5
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < 1e-4

def test_zscore_two_values():
    """[100, 200] mean=150 std=50 → [-1, 1]"""
    r = z_score_standardize([100, 200])
    assert abs(r[0] - (-1.0)) < TOL
    assert abs(r[1] - 1.0) < TOL

def test_zscore_known_4():
    """[1,3,5,7] mean=4 std=sqrt(5) → known"""
    r = z_score_standardize([1, 3, 5, 7])
    s5 = 5 ** 0.5
    expected = [-3 / s5, -1 / s5, 1 / s5, 3 / s5]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < 1e-4

def test_zscore_raises_on_constant():
    """边界: 全相同 std=0 → ValueError"""
    with pytest.raises(ValueError):
        z_score_standardize([10, 10, 10, 10])

def test_zscore_raises_on_single():
    """边界: 单元素 std=0 → ValueError"""
    with pytest.raises(ValueError):
        z_score_standardize([42])

def test_zscore_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        z_score_standardize([])

def test_zscore_raises_on_non_list():
    with pytest.raises(TypeError):
        z_score_standardize("abc")


# ============================================================
# F3: fill_with_median (全输入含 None 防 D 巧合, 8 测试)
# ============================================================

def test_fwm_replace_one():
    """[1,2,None,4,5] median=3 → [1,2,3,4,5]"""
    assert fill_with_median([1, 2, None, 4, 5]) == [1, 2, 3, 4, 5]

def test_fwm_two_nones():
    """[None,1,2,3,None] median=2 → [2,1,2,3,2]"""
    assert fill_with_median([None, 1, 2, 3, None]) == [2, 1, 2, 3, 2]

def test_fwm_one_none_three_values():
    """[10,None,20] median(of [10,20])=15 → [10,15,20]"""
    assert fill_with_median([10, None, 20]) == [10, 15, 20]

def test_fwm_constant_with_none():
    """[5,5,None,5,5] median=5 → [5,5,5,5,5]"""
    assert fill_with_median([5, 5, None, 5, 5]) == [5, 5, 5, 5, 5]

def test_fwm_known_median():
    """[10,20,None,40,50] median(of 4 even-count)=(20+40)/2=30 → [10,20,30,40,50]"""
    assert fill_with_median([10, 20, None, 40, 50]) == [10, 20, 30, 40, 50]

def test_fwm_all_none_raises():
    """边界: 全部 None → ValueError"""
    with pytest.raises(ValueError):
        fill_with_median([None, None, None])

def test_fwm_empty_raises():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        fill_with_median([])

def test_fwm_raises_on_non_list():
    with pytest.raises(TypeError):
        fill_with_median("abc")


# ============================================================
# F4: filter_low_variance (8 测试)
# ============================================================

def test_flv_remove_constant():
    """col 1 是常量 [2,2,2] var=0, threshold=0 严格大于, 删除"""
    M = [[1, 2, 3], [2, 2, 4], [3, 2, 5]]
    f, idx = filter_low_variance(M, threshold=0.0)
    assert idx == [0, 2]
    assert f == [[1, 3], [2, 4], [3, 5]]

def test_flv_high_threshold_keeps_high_var():
    """matrix var: col0≈13.56, col1=0, col2≈10.67. threshold=12.0 → 仅 col 0"""
    M = [[1, 2, 3], [5, 2, 7], [10, 2, 11]]
    f, idx = filter_low_variance(M, threshold=12.0)
    assert idx == [0]
    assert f == [[1], [5], [10]]

def test_flv_keep_all():
    """全 var > threshold, 全保留"""
    M = [[1, 2], [3, 4], [5, 6]]
    f, idx = filter_low_variance(M, threshold=0.5)
    assert idx == [0, 1]
    assert f == [[1, 2], [3, 4], [5, 6]]

def test_flv_three_kept_of_four():
    """4 列: col0 var=2/3, col1=0, col2≈0.222, col3 var=2/3, threshold=0.0 → 删 col1"""
    M = [[1, 1, 1, 1], [2, 1, 2, 2], [3, 1, 1, 3]]
    f, idx = filter_low_variance(M, threshold=0.0)
    assert idx == [0, 2, 3]
    assert f == [[1, 1, 1], [2, 2, 2], [3, 1, 3]]

def test_flv_threshold_excludes_some():
    """4 列, threshold=0.5: col0 var=2/3>0.5, col2 var≈0.222<0.5 → 删 col1+col2"""
    M = [[1, 1, 1, 1], [2, 1, 2, 2], [3, 1, 1, 3]]
    f, idx = filter_low_variance(M, threshold=0.5)
    assert idx == [0, 3]
    assert f == [[1, 1], [2, 2], [3, 3]]

def test_flv_raises_on_single_sample():
    """边界: 单样本无法算方差 → ValueError"""
    with pytest.raises(ValueError):
        filter_low_variance([[1, 2, 3]], threshold=0.0)

def test_flv_raises_on_empty():
    """边界: 空矩阵 → ValueError"""
    with pytest.raises(ValueError):
        filter_low_variance([], threshold=0.0)

def test_flv_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        filter_low_variance("abc", threshold=0.0)
