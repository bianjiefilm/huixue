"""CV08 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv08 import (
    template_match_ssd,
    find_max_correlation,
    non_max_suppression_1d,
    sliding_window_count,
)

TOL = 1e-6


# F1: template_match_ssd: sum((t_i - p_i)^2)
def test_ssd_identical():
    """完全相同 → 0"""
    r = template_match_ssd([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert abs(r - 0.0) < TOL

def test_ssd_off_by_two():
    """每个元素差 2, 长度 3 → (4*3) = 12 (SAD 会给 6 不同)"""
    r = template_match_ssd([1.0, 2.0, 3.0], [3.0, 4.0, 5.0])
    assert abs(r - 12.0) < TOL

def test_ssd_general():
    """[1,2,3] vs [4,5,6]: (3²+3²+3²) = 27"""
    r = template_match_ssd([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert abs(r - 27.0) < TOL

def test_ssd_negative_diff():
    """[5,5] vs [3,2]: (4+9) = 13"""
    r = template_match_ssd([5.0, 5.0], [3.0, 2.0])
    assert abs(r - 13.0) < TOL

def test_ssd_single_element():
    """[10] vs [3]: 49 (boundary 单元素)"""
    r = template_match_ssd([10.0], [3.0])
    assert abs(r - 49.0) < TOL

def test_ssd_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        template_match_ssd([1.0, 2.0], [1.0, 2.0, 3.0])

def test_ssd_raises_on_non_list():
    with pytest.raises(TypeError):
        template_match_ssd("abc", [1.0, 2.0, 3.0])


# F2: find_max_correlation (argmax, ties → smallest index)
def test_argmax_simple():
    """[1, 5, 3] → 1"""
    assert find_max_correlation([1.0, 5.0, 3.0]) == 1

def test_argmax_at_start():
    """[10, 5, 3, 1] → 0"""
    assert find_max_correlation([10.0, 5.0, 3.0, 1.0]) == 0

def test_argmax_at_end():
    """[1, 2, 3, 10] → 3"""
    assert find_max_correlation([1.0, 2.0, 3.0, 10.0]) == 3

def test_argmax_with_negatives():
    """[-5, -1, -3] → 1"""
    assert find_max_correlation([-5.0, -1.0, -3.0]) == 1

def test_argmax_ties_first():
    """[5, 5, 3] → 0 (ties returns smallest index)"""
    assert find_max_correlation([5.0, 5.0, 3.0]) == 0

def test_argmax_single():
    """[42] → 0 (boundary)"""
    assert find_max_correlation([42.0]) == 0

def test_argmax_raises_on_empty():
    with pytest.raises(ValueError):
        find_max_correlation([])

def test_argmax_raises_on_non_list():
    with pytest.raises(TypeError):
        find_max_correlation(123)


# F3: non_max_suppression_1d
def test_nms_radius_1_simple():
    """[1, 5, 1, 3, 1] r=1: 取 idx 1 (val 5), 抑制 0,2; 剩 [_, _, _, 3, 1], 取 idx 3 (val 3), 抑制 2,4; → [1, 3]"""
    assert non_max_suppression_1d([1.0, 5.0, 1.0, 3.0, 1.0], 1) == [1, 3]

def test_nms_radius_2():
    """[1, 5, 1, 3, 1] r=2: 取 idx 1 抑制 [-1,3]即0,1,2,3; 剩 [_,_,_,_,1] 取 idx 4. → [1, 4]"""
    assert non_max_suppression_1d([1.0, 5.0, 1.0, 3.0, 1.0], 2) == [1, 4]

def test_nms_single_peak():
    """[1, 1, 10, 1, 1] r=1: idx 2 抑制 1,3; 剩 0,4 → [0,2,4]"""
    assert non_max_suppression_1d([1.0, 1.0, 10.0, 1.0, 1.0], 1) == [0, 2, 4]

def test_nms_all_same():
    """全同值, r=1: 取 idx 0 抑制 1; 取 idx 2 抑制 3; 取 idx 4. → [0, 2, 4]"""
    assert non_max_suppression_1d([3.0, 3.0, 3.0, 3.0, 3.0], 1) == [0, 2, 4]

def test_nms_large_radius_kills_others():
    """r=10 大于 list len, 只剩 argmax: [1, 5, 1, 3, 1] → [1]"""
    assert non_max_suppression_1d([1.0, 5.0, 1.0, 3.0, 1.0], 10) == [1]

def test_nms_raises_on_empty():
    with pytest.raises(ValueError):
        non_max_suppression_1d([], 1)

def test_nms_raises_on_non_list():
    with pytest.raises(TypeError):
        non_max_suppression_1d("abc", 1)


# F4: sliding_window_count
def test_sw_simple():
    """img=10, win=3, stride=1 → (10-3)/1+1 = 8"""
    assert sliding_window_count(10, 3, 1) == 8

def test_sw_stride_2():
    """img=10, win=3, stride=2 → (10-3)/2+1 = 4 (floor 7/2=3, +1=4)"""
    assert sliding_window_count(10, 3, 2) == 4

def test_sw_stride_3():
    """img=15, win=4, stride=3 → (15-4)/3+1 = floor(11/3)+1 = 3+1 = 4 (SAD: 15//3=5 不同)"""
    assert sliding_window_count(15, 4, 3) == 4

def test_sw_window_equals_image():
    """img=5, win=5, stride=1 → 1 (boundary)"""
    assert sliding_window_count(5, 5, 1) == 1

def test_sw_large_image():
    """img=100, win=10, stride=5 → (100-10)/5+1 = 19"""
    assert sliding_window_count(100, 10, 5) == 19

def test_sw_stride_5():
    """img=20, win=5, stride=4 → (20-5)/4+1 = floor(15/4)+1 = 3+1 = 4 (SAD: 20//4=5 不同)"""
    assert sliding_window_count(20, 5, 4) == 4

def test_sw_raises_on_window_gt_image():
    with pytest.raises(ValueError):
        sliding_window_count(3, 10, 1)

def test_sw_raises_on_zero_stride():
    with pytest.raises(ValueError):
        sliding_window_count(10, 3, 0)

def test_sw_raises_on_non_int():
    with pytest.raises(TypeError):
        sliding_window_count(10.0, 3, 1)
