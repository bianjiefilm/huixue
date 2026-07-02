"""CV10 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv10 import (
    bbox_area,
    compute_iou,
    confidence_threshold_filter,
    nms_2d,
)

TOL = 1e-6


# F1: bbox_area
def test_bbox_area_unit():
    """[0,0,1,1] → 1"""
    assert abs(bbox_area([0.0, 0.0, 1.0, 1.0]) - 1.0) < TOL

def test_bbox_area_2x3():
    """[0,0,2,3] → 6"""
    assert abs(bbox_area([0.0, 0.0, 2.0, 3.0]) - 6.0) < TOL

def test_bbox_area_offset():
    """[10,20,30,50] → 20*30 = 600"""
    assert abs(bbox_area([10.0, 20.0, 30.0, 50.0]) - 600.0) < TOL

def test_bbox_area_small():
    """[0,0,0.5,0.5] → 0.25"""
    assert abs(bbox_area([0.0, 0.0, 0.5, 0.5]) - 0.25) < TOL

def test_bbox_area_negative_corner():
    """[-1,-2,3,4] → 4*6 = 24"""
    assert abs(bbox_area([-1.0, -2.0, 3.0, 4.0]) - 24.0) < TOL

def test_bbox_area_minimal():
    """[0, 0, 0.001, 0.001] → 1e-6 (boundary 极小)"""
    assert abs(bbox_area([0.0, 0.0, 0.001, 0.001]) - 1e-6) < 1e-9

def test_bbox_area_raises_on_x1_ge_x2():
    with pytest.raises(ValueError):
        bbox_area([3.0, 0.0, 1.0, 1.0])

def test_bbox_area_raises_on_wrong_length():
    with pytest.raises(ValueError):
        bbox_area([1.0, 2.0, 3.0])

def test_bbox_area_raises_on_non_list():
    with pytest.raises(TypeError):
        bbox_area("0,0,1,1")


# F2: compute_iou
def test_iou_b_contained_in_a_2():
    """A=[0,0,4,4] B=[0,0,2,2]: inter=4, A=16, B=4, IoU=4/16=0.25 (IoMin=1.0 不同)"""
    a = [0.0, 0.0, 4.0, 4.0]
    b = [0.0, 0.0, 2.0, 2.0]
    r = compute_iou(a, b)
    assert abs(r - 0.25) < TOL

def test_iou_no_overlap():
    """完全不重叠 → IoU = 0"""
    a = [0.0, 0.0, 1.0, 1.0]
    b = [10.0, 10.0, 11.0, 11.0]
    r = compute_iou(a, b)
    assert abs(r - 0.0) < TOL

def test_iou_half_overlap_x():
    """[0,0,2,2] 与 [1,0,3,2]: 交=1*2=2, A=4, B=4, 并=4+4-2=6, IoU=2/6=1/3"""
    a = [0.0, 0.0, 2.0, 2.0]
    b = [1.0, 0.0, 3.0, 2.0]
    r = compute_iou(a, b)
    assert abs(r - 1.0/3) < TOL

def test_iou_quarter_overlap():
    """[0,0,2,2] 与 [1,1,3,3]: 交=1*1=1, A=4, B=4, 并=7, IoU=1/7"""
    a = [0.0, 0.0, 2.0, 2.0]
    b = [1.0, 1.0, 3.0, 3.0]
    r = compute_iou(a, b)
    assert abs(r - 1.0/7) < TOL

def test_iou_b_contained_in_a():
    """A 包含 B: A=[0,0,4,4], B=[1,1,2,2], 交=1, A=16, B=1, 并=16, IoU=1/16"""
    a = [0.0, 0.0, 4.0, 4.0]
    b = [1.0, 1.0, 2.0, 2.0]
    r = compute_iou(a, b)
    assert abs(r - 1.0/16) < TOL

def test_iou_touching_edge():
    """边界接触不算重叠: A=[0,0,1,1], B=[1,0,2,1], 交=0 (x_overlap=0), IoU=0 (boundary)"""
    a = [0.0, 0.0, 1.0, 1.0]
    b = [1.0, 0.0, 2.0, 1.0]
    r = compute_iou(a, b)
    assert abs(r - 0.0) < TOL

def test_iou_raises_on_wrong_box_length():
    with pytest.raises(ValueError):
        compute_iou([0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0])

def test_iou_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_iou("0,0,1,1", [0.0, 0.0, 1.0, 1.0])


# F3: confidence_threshold_filter (>= thresh)
def test_filter_simple():
    """[0.1, 0.6, 0.3, 0.8], thresh=0.5 → [1, 3]"""
    assert confidence_threshold_filter([0.1, 0.6, 0.3, 0.8], 0.5) == [1, 3]

def test_filter_at_threshold_partial():
    """[0.4, 0.5, 0.6] thresh=0.5 → [1, 2] (>= 测试)"""
    assert confidence_threshold_filter([0.4, 0.5, 0.6], 0.5) == [1, 2]

def test_filter_first_only():
    """[0.9, 0.2, 0.1] thresh=0.5 → [0]"""
    assert confidence_threshold_filter([0.9, 0.2, 0.1], 0.5) == [0]

def test_filter_all_below():
    """thresh=0.99, 全过低 → [] (boundary 全 reject)"""
    assert confidence_threshold_filter([0.3, 0.5, 0.7], 0.99) == []

def test_filter_just_one():
    """[0.1, 0.2, 0.9], thresh=0.5 → [2]"""
    assert confidence_threshold_filter([0.1, 0.2, 0.9], 0.5) == [2]

def test_filter_two_kept():
    """[0.6, 0.3, 0.7] thresh=0.5 → [0, 2]"""
    assert confidence_threshold_filter([0.6, 0.3, 0.7], 0.5) == [0, 2]

def test_filter_raises_on_empty():
    with pytest.raises(ValueError):
        confidence_threshold_filter([], 0.5)

def test_filter_raises_on_non_list():
    with pytest.raises(TypeError):
        confidence_threshold_filter("0.5,0.6", 0.5)


# F4: nms_2d
def test_nms_full_overlap_kill_lower():
    """两 BBox 完全相同 → 保留高分"""
    boxes = [[0.0, 0.0, 2.0, 2.0], [0.0, 0.0, 2.0, 2.0]]
    scores = [0.5, 0.9]
    assert nms_2d(boxes, scores, 0.5) == [1]

def test_nms_two_separate_kill():
    """4 个框 2 对重叠 → 各保留高分"""
    boxes = [
        [0.0, 0.0, 2.0, 2.0],
        [0.05, 0.05, 2.05, 2.05],   # 与 0 高 IoU
        [10.0, 10.0, 12.0, 12.0],
        [10.05, 10.05, 12.05, 12.05],  # 与 2 高 IoU
    ]
    scores = [0.9, 0.5, 0.7, 0.6]
    # 高分 0 抑制 1; 高分 2 抑制 3 → 保留 [0, 2]
    assert nms_2d(boxes, scores, 0.5) == [0, 2]

def test_nms_high_iou_kill():
    """A B 高重叠 → 保留高分 A"""
    boxes = [
        [0.0, 0.0, 2.0, 2.0],
        [0.1, 0.1, 2.1, 2.1],  # 与 A 交集很大, IoU 接近 1
        [10.0, 10.0, 12.0, 12.0],
    ]
    scores = [0.9, 0.85, 0.7]
    assert nms_2d(boxes, scores, 0.5) == [0, 2]

def test_nms_single_box():
    """单 BBox → 保留 (boundary)"""
    assert nms_2d([[0.0, 0.0, 1.0, 1.0]], [0.5], 0.5) == [0]

def test_nms_strict_threshold():
    """阈值 0.3 (激进): 三个相邻 BBox 中两个被抑制"""
    boxes = [
        [0.0, 0.0, 2.0, 2.0],
        [0.5, 0.5, 2.5, 2.5],   # IoU 与 A ≈ 0.391, 比 0.3 大 → 抑制
        [10.0, 10.0, 12.0, 12.0],
    ]
    scores = [0.9, 0.8, 0.7]
    assert nms_2d(boxes, scores, 0.3) == [0, 2]

def test_nms_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        nms_2d([[0.0, 0.0, 1.0, 1.0]], [0.5, 0.6], 0.5)

def test_nms_raises_on_invalid_threshold():
    with pytest.raises(ValueError):
        nms_2d([[0.0, 0.0, 1.0, 1.0]], [0.5], 2.0)

def test_nms_raises_on_non_list():
    with pytest.raises(TypeError):
        nms_2d("not a list", [0.5], 0.5)
