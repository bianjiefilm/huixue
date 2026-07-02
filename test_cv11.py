"""CV11 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv11 import (
    binary_threshold_segment,
    connected_components_count_1d,
    dice_coefficient,
    pixel_accuracy,
)

TOL = 1e-6


# F1: binary_threshold_segment (>= thresh → 1)
def test_seg_basic():
    """[0.1, 0.5, 0.9] thresh=0.5 → [0, 1, 1]"""
    assert binary_threshold_segment([0.1, 0.5, 0.9], 0.5) == [0, 1, 1]

def test_seg_at_threshold():
    """边界 == thresh → 1"""
    assert binary_threshold_segment([0.5, 0.4, 0.5, 0.6], 0.5) == [1, 0, 1, 1]

def test_seg_all_below():
    """全部 < thresh → 全 0"""
    assert binary_threshold_segment([0.1, 0.2, 0.3], 0.5) == [0, 0, 0]

def test_seg_all_above():
    """全部 >= thresh → 全 1"""
    assert binary_threshold_segment([0.6, 0.7, 0.8], 0.5) == [1, 1, 1]

def test_seg_negative_values():
    """[-0.1, -0.5, 0.5, 1.0] thresh=0.0 → [0, 0, 1, 1]"""
    assert binary_threshold_segment([-0.1, -0.5, 0.5, 1.0], 0.0) == [0, 0, 1, 1]

def test_seg_mixed_decimals():
    """[0.49, 0.51, 0.5, 0.4] thresh=0.5 → [0, 1, 1, 0]"""
    assert binary_threshold_segment([0.49, 0.51, 0.5, 0.4], 0.5) == [0, 1, 1, 0]

def test_seg_single_above():
    """[0.7] thresh=0.5 → [1] (boundary 单元素)"""
    assert binary_threshold_segment([0.7], 0.5) == [1]

def test_seg_raises_on_empty():
    with pytest.raises(ValueError):
        binary_threshold_segment([], 0.5)

def test_seg_raises_on_non_list():
    with pytest.raises(TypeError):
        binary_threshold_segment("0.5", 0.5)


# F2: connected_components_count_1d (number of runs of 1s)
def test_cc_no_ones():
    """全 0 → 0"""
    assert connected_components_count_1d([0, 0, 0]) == 0

def test_cc_all_ones():
    """全 1 → 1 (一个段)"""
    assert connected_components_count_1d([1, 1, 1, 1]) == 1

def test_cc_two_segments():
    """[1, 1, 0, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)"""
    assert connected_components_count_1d([1, 1, 0, 0, 1, 1]) == 2

def test_cc_alternating():
    """[1, 0, 1, 0, 1] → 3"""
    assert connected_components_count_1d([1, 0, 1, 0, 1]) == 3

def test_cc_start_with_one():
    """[1, 1, 0, 1] → 2"""
    assert connected_components_count_1d([1, 1, 0, 1]) == 2

def test_cc_two_long():
    """[1, 1, 1, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)"""
    assert connected_components_count_1d([1, 1, 1, 0, 1, 1]) == 2

def test_cc_single_one():
    """[0, 0, 1, 0] → 1 (boundary 单 1)"""
    assert connected_components_count_1d([0, 0, 1, 0]) == 1

def test_cc_raises_on_invalid_value():
    with pytest.raises(ValueError):
        connected_components_count_1d([0, 1, 2])

def test_cc_raises_on_non_list():
    with pytest.raises(TypeError):
        connected_components_count_1d("01001")


# F3: dice_coefficient
def test_dice_perfect():
    """完全相同 → 1"""
    p = [1, 0, 1, 1, 0]
    assert abs(dice_coefficient(p, p) - 1.0) < TOL

def test_dice_disjoint():
    """无交集 → 0"""
    pred = [1, 1, 0, 0]
    gt = [0, 0, 1, 1]
    assert abs(dice_coefficient(pred, gt) - 0.0) < TOL

def test_dice_partial():
    """[1,1,1,0] vs [1,1,0,0]: A∩B=2, |A|=3, |B|=2, Dice=4/5=0.8"""
    assert abs(dice_coefficient([1, 1, 1, 0], [1, 1, 0, 0]) - 0.8) < TOL

def test_dice_one_pred_three_gt():
    """[1,0,0,0] vs [1,1,1,0]: A∩B=1, |A|=1, |B|=3, Dice=2/4=0.5"""
    assert abs(dice_coefficient([1, 0, 0, 0], [1, 1, 1, 0]) - 0.5) < TOL

def test_dice_both_empty():
    """两者全 0 → 1.0 约定"""
    assert abs(dice_coefficient([0, 0, 0], [0, 0, 0]) - 1.0) < TOL

def test_dice_one_overlap_in_5():
    """[1,1,0,1,0] vs [0,1,1,0,1]: A∩B=1, |A|=3, |B|=3, Dice=2/6=1/3"""
    assert abs(dice_coefficient([1, 1, 0, 1, 0], [0, 1, 1, 0, 1]) - 1.0/3) < TOL

def test_dice_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        dice_coefficient([1, 0], [1, 0, 1])

def test_dice_raises_on_non_list():
    with pytest.raises(TypeError):
        dice_coefficient("10", [1, 0])


# F4: pixel_accuracy
def test_pa_perfect():
    """完全相同 → 1"""
    p = [1, 0, 1, 1, 0]
    assert abs(pixel_accuracy(p, p) - 1.0) < TOL

def test_pa_all_wrong():
    """全错 → 0"""
    pred = [1, 1, 1, 1]
    gt = [0, 0, 0, 0]
    assert abs(pixel_accuracy(pred, gt) - 0.0) < TOL

def test_pa_one_quarter():
    """[1,1,1,0] vs [1,0,0,0]: 正确 [✓,✗,✗,✓] = 2/4 = 0.5 — 不, 实际 [1=1,1≠0,1≠0,0=0] = 2/4=0.5
    改用: [1,1,1,1] vs [1,0,0,0]: 1/4 = 0.25 (1-PA = 0.75 不同)"""
    assert abs(pixel_accuracy([1, 1, 1, 1], [1, 0, 0, 0]) - 0.25) < TOL

def test_pa_three_of_four():
    """[1,1,0,1] vs [1,1,1,1]: 3/4 = 0.75"""
    assert abs(pixel_accuracy([1, 1, 0, 1], [1, 1, 1, 1]) - 0.75) < TOL

def test_pa_two_of_five():
    """[1,1,1,1,1] vs [1,0,0,0,1]: 2/5 = 0.4"""
    assert abs(pixel_accuracy([1, 1, 1, 1, 1], [1, 0, 0, 0, 1]) - 0.4) < TOL

def test_pa_imbalanced_class():
    """所有背景预测对: [0,0,0,0,1] vs [0,0,0,0,0]: 4/5 = 0.8 (boundary 类别不平衡)"""
    assert abs(pixel_accuracy([0, 0, 0, 0, 1], [0, 0, 0, 0, 0]) - 0.8) < TOL

def test_pa_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        pixel_accuracy([1, 0], [1])

def test_pa_raises_on_empty():
    with pytest.raises(ValueError):
        pixel_accuracy([], [])
