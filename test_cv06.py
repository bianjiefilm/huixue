"""CV06 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv06 import (
    erode_1d,
    dilate_1d,
    get_morph_operation_order,
    get_cross_se_3x3,
)


# F1: erode_1d (1D erosion, AND of kernel_size window)
def test_erode_1d_one_zero_left():
    """[0,1,1,1,1] k=3 → [0,1,1]"""
    assert erode_1d([0, 1, 1, 1, 1], 3) == [0, 1, 1]

def test_erode_1d_one_zero_right():
    """[1,1,1,1,0] k=3 → [1,1,0]"""
    assert erode_1d([1, 1, 1, 1, 0], 3) == [1, 1, 0]

def test_erode_1d_long_mixed():
    """[1,1,1,0,1,1,1] k=3 → [1,0,0,0,1]"""
    assert erode_1d([1, 1, 1, 0, 1, 1, 1], 3) == [1, 0, 0, 0, 1]

def test_erode_1d_partial_5():
    """[1,1,1,1,0,1] k=3 → [1,1,0,0]"""
    assert erode_1d([1, 1, 1, 1, 0, 1], 3) == [1, 1, 0, 0]

def test_erode_1d_all_zeros():
    """全 0 → 全 0 (boundary)"""
    assert erode_1d([0, 0, 0, 0, 0], 3) == [0, 0, 0]

def test_erode_1d_kernel_5_mixed():
    """[1,0,1,1,1,1,1] k=5 → [0,0,1]"""
    assert erode_1d([1, 0, 1, 1, 1, 1, 1], 5) == [0, 0, 1]

def test_erode_1d_raises_on_even_kernel():
    with pytest.raises(ValueError):
        erode_1d([1, 1, 1, 1], 2)

def test_erode_1d_raises_on_invalid_value():
    with pytest.raises(ValueError):
        erode_1d([1, 2, 1, 1], 3)

def test_erode_1d_raises_on_non_list():
    with pytest.raises(TypeError):
        erode_1d("11011", 3)


# F2: dilate_1d (1D dilation, OR of kernel_size window)
def test_dilate_1d_one_one_left():
    """[1,0,0,0,0] k=3 → [1,0,0]"""
    assert dilate_1d([1, 0, 0, 0, 0], 3) == [1, 0, 0]

def test_dilate_1d_one_one_right():
    """[0,0,0,0,1] k=3 → [0,0,1]"""
    assert dilate_1d([0, 0, 0, 0, 1], 3) == [0, 0, 1]

def test_dilate_1d_long_sparse():
    """[0,0,0,1,0,0,0] k=3 → [0,1,1,1,0]"""
    assert dilate_1d([0, 0, 0, 1, 0, 0, 0], 3) == [0, 1, 1, 1, 0]

def test_dilate_1d_partial_5():
    """[0,0,1,0,0,1] k=3 → [1,1,1,1]"""
    assert dilate_1d([0, 0, 1, 0, 0, 1], 3) == [1, 1, 1, 1]

def test_dilate_1d_all_zeros():
    """全 0 → 全 0 (boundary)"""
    assert dilate_1d([0, 0, 0, 0, 0], 3) == [0, 0, 0]

def test_dilate_1d_kernel_5_mixed():
    """[0,0,1,0,0,0,1] k=5 → [1,1,1]"""
    assert dilate_1d([0, 0, 1, 0, 0, 0, 1], 5) == [1, 1, 1]

def test_dilate_1d_raises_on_even_kernel():
    with pytest.raises(ValueError):
        dilate_1d([1, 1, 1, 1], 2)

def test_dilate_1d_raises_on_invalid_value():
    with pytest.raises(ValueError):
        dilate_1d([0, 0, 3, 0, 0], 3)

def test_dilate_1d_raises_on_non_list():
    with pytest.raises(TypeError):
        dilate_1d(123, 3)


# F3: get_morph_operation_order
def test_order_erosion():
    assert get_morph_operation_order("erosion") == "erosion"

def test_order_dilation():
    assert get_morph_operation_order("dilation") == "dilation"

def test_order_opening():
    """开 = 先腐蚀再膨胀"""
    assert get_morph_operation_order("opening") == "erosion_then_dilation"

def test_order_closing():
    """闭 = 先膨胀再腐蚀"""
    assert get_morph_operation_order("closing") == "dilation_then_erosion"

def test_order_raises_on_unknown():
    with pytest.raises(ValueError):
        get_morph_operation_order("invalid_op")

def test_order_raises_on_empty():
    """空字符串边界"""
    with pytest.raises(ValueError):
        get_morph_operation_order("")

def test_order_raises_on_non_string():
    with pytest.raises(TypeError):
        get_morph_operation_order(123)


# F4: get_cross_se_3x3
def test_cross_shape():
    se = get_cross_se_3x3()
    assert isinstance(se, list)
    assert len(se) == 3
    for row in se:
        assert isinstance(row, list)
        assert len(row) == 3

def test_cross_full_match():
    """完整十字: [[0,1,0],[1,1,1],[0,1,0]]"""
    se = get_cross_se_3x3()
    expected = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    for i in range(3):
        for j in range(3):
            assert se[i][j] == expected[i][j]

def test_cross_corners_zero():
    """4 角必 0"""
    se = get_cross_se_3x3()
    assert se[0][0] == 0
    assert se[0][2] == 0
    assert se[2][0] == 0
    assert se[2][2] == 0

def test_cross_center_one():
    """中心必 1"""
    se = get_cross_se_3x3()
    assert se[1][1] == 1

def test_cross_edges_one():
    """4 个边中点必 1"""
    se = get_cross_se_3x3()
    assert se[0][1] == 1
    assert se[1][0] == 1
    assert se[1][2] == 1
    assert se[2][1] == 1
