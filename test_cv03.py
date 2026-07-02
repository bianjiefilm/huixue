"""CV03 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv03 import (
    translate_point,
    rotate_point,
    scale_dimensions,
    apply_affine_transform,
)

TOL = 1e-6


# F1: translate_point
def test_t_basic():
    assert translate_point(1, 2, 3, 4) == (4, 6)

def test_t_zero():
    assert translate_point(5, 5, 0, 0) == (5, 5)

def test_t_negative():
    assert translate_point(10, 10, -5, -3) == (5, 7)

def test_t_floats():
    x, y = translate_point(1.5, 2.5, 0.5, 1.0)
    assert abs(x - 2.0) < TOL
    assert abs(y - 3.5) < TOL

def test_t_origin():
    assert translate_point(0, 0, 5, 7) == (5, 7)

def test_t_raises_on_non_numeric():
    with pytest.raises(TypeError):
        translate_point("1", 2, 3, 4)


# F2: rotate_point
def test_r_zero_angle():
    """0° 旋转 → 不变"""
    x, y = rotate_point(3, 4, 0)
    assert abs(x - 3) < TOL and abs(y - 4) < TOL

def test_r_90_around_origin():
    """点 (1, 0) 绕原点顺时针 90° → (0, -1)"""
    x, y = rotate_point(1, 0, 90)
    assert abs(x - 0) < TOL and abs(y - (-1)) < TOL

def test_r_180_around_origin():
    """点 (3, 4) 绕原点 180° → (-3, -4)"""
    x, y = rotate_point(3, 4, 180)
    assert abs(x - (-3)) < TOL and abs(y - (-4)) < TOL

def test_r_around_custom_center():
    """点 (2, 0) 绕 (1, 0) 旋转 180° → (0, 0)"""
    x, y = rotate_point(2, 0, 180, cx=1, cy=0)
    assert abs(x - 0) < TOL and abs(y - 0) < TOL

def test_r_360_returns():
    """360° → 不变 (含浮点精度容差)"""
    x, y = rotate_point(3, 4, 360)
    assert abs(x - 3) < 1e-9
    assert abs(y - 4) < 1e-9

def test_r_raises_on_non_numeric():
    with pytest.raises(TypeError):
        rotate_point("1", 0, 90)


# F3: scale_dimensions
def test_sd_basic():
    """100×50, fx=2.0, fy=3.0 → (200, 150)"""
    assert scale_dimensions(100, 50, 2.0, 3.0) == (200, 150)

def test_sd_half():
    """1920×1080, fx=fy=0.5 → (960, 540)"""
    assert scale_dimensions(1920, 1080, 0.5, 0.5) == (960, 540)

def test_sd_anisotropic():
    """100×100, fx=2.0, fy=0.5 → (200, 50)"""
    assert scale_dimensions(100, 100, 2.0, 0.5) == (200, 50)

def test_sd_floor():
    """101×201, fx=fy=0.5 → (50, 100) (向下取整)"""
    assert scale_dimensions(101, 201, 0.5, 0.5) == (50, 100)

def test_sd_no_change():
    """fx=fy=1 → 不变"""
    assert scale_dimensions(224, 224, 1.0, 1.0) == (224, 224)

def test_sd_raises_on_zero():
    with pytest.raises(ValueError):
        scale_dimensions(0, 100, 1.0, 1.0)

def test_sd_raises_on_negative_factor():
    with pytest.raises(ValueError):
        scale_dimensions(100, 100, -1.0, 1.0)

def test_sd_raises_on_non_int():
    with pytest.raises(TypeError):
        scale_dimensions(100.5, 100, 1.0, 1.0)


# F4: apply_affine_transform (transform 类)
def test_aff_identity():
    """单位矩阵 [[1,0,0],[0,1,0]] → (x, y) 不变"""
    x, y = apply_affine_transform(3, 4, [[1, 0, 0], [0, 1, 0]])
    assert abs(x - 3) < TOL and abs(y - 4) < TOL

def test_aff_translation():
    """平移矩阵 [[1,0,5],[0,1,7]] → (x+5, y+7)"""
    x, y = apply_affine_transform(3, 4, [[1, 0, 5], [0, 1, 7]])
    assert abs(x - 8) < TOL and abs(y - 11) < TOL

def test_aff_scale():
    """缩放矩阵 [[2,0,0],[0,3,0]] → (2x, 3y)"""
    x, y = apply_affine_transform(3, 4, [[2, 0, 0], [0, 3, 0]])
    assert abs(x - 6) < TOL and abs(y - 12) < TOL

def test_aff_rotation_90():
    """旋转 90° 矩阵 [[0,1,0],[-1,0,0]] → 点 (1, 0) → (0, -1)"""
    x, y = apply_affine_transform(1, 0, [[0, 1, 0], [-1, 0, 0]])
    assert abs(x - 0) < TOL and abs(y - (-1)) < TOL

def test_aff_complex():
    """复合: 缩放 + 平移 [[2,0,1],[0,3,2]]
    点 (1, 1) → (2*1+0+1, 0+3*1+2) = (3, 5)"""
    x, y = apply_affine_transform(1, 1, [[2, 0, 1], [0, 3, 2]])
    assert abs(x - 3) < TOL and abs(y - 5) < TOL

def test_aff_raises_on_wrong_shape():
    """matrix 不是 2×3 → ValueError"""
    with pytest.raises(ValueError):
        apply_affine_transform(1, 1, [[1, 0]])

def test_aff_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_affine_transform(1, 1, "abc")

def test_aff_negative_input():
    """点 (-2, -3) 缩放矩阵 [[2,0,0],[0,2,0]] → (-4, -6)"""
    x, y = apply_affine_transform(-2, -3, [[2, 0, 0], [0, 2, 0]])
    assert abs(x - (-4)) < TOL and abs(y - (-6)) < TOL
