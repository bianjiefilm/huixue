"""CV01 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv01 import (
    classify_cv_task,
    compute_image_size_bytes,
    resize_aspect_ratio,
    normalize_pixel_array,
)

TOL = 1e-6


# F1: classify_cv_task
def test_cls_classification():
    assert classify_cv_task((224, 224, 3), "label") == "classification"

def test_cls_detection():
    assert classify_cv_task((224, 224, 3), "boxes") == "detection"

def test_cls_pixel_annotation():
    assert classify_cv_task((224, 224, 3), "mask") == "pixel_annotation"

def test_cls_recognition():
    assert classify_cv_task((224, 224, 3), "id") == "recognition"

def test_cls_different_size_image():
    """不同尺寸但仍是 3D"""
    assert classify_cv_task((128, 256, 3), "label") == "classification"

def test_cls_raises_on_wrong_shape_length():
    with pytest.raises(ValueError):
        classify_cv_task((224, 224), "label")

def test_cls_raises_on_invalid_output_type():
    with pytest.raises(ValueError):
        classify_cv_task((224, 224, 3), "unknown")

# test_cls_raises_on_non_tuple 删除: fc 协议 P1 决策 — list 与 tuple 等价


# F2: compute_image_size_bytes
def test_bytes_uint8_rgb():
    """1920×1080×3×1 = 6220800"""
    assert compute_image_size_bytes(1920, 1080, 3) == 6220800

def test_bytes_uint8_grayscale():
    """28×28×1×1 = 784"""
    assert compute_image_size_bytes(28, 28, 1) == 784

def test_bytes_fp32():
    """224×224×3×4 = 602112"""
    assert compute_image_size_bytes(224, 224, 3, 4) == 602112

def test_bytes_fp16():
    """512×512×3×2 = 1572864"""
    assert compute_image_size_bytes(512, 512, 3, 2) == 1572864

def test_bytes_minimal():
    """1×1×1×1 = 1"""
    assert compute_image_size_bytes(1, 1, 1) == 1

def test_bytes_raises_on_zero():
    with pytest.raises(ValueError):
        compute_image_size_bytes(0, 1080, 3)

def test_bytes_raises_on_negative():
    with pytest.raises(ValueError):
        compute_image_size_bytes(1920, -1, 3)

def test_bytes_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_image_size_bytes(1920.0, 1080, 3)


# F3: resize_aspect_ratio (transform 类)
def test_rar_landscape():
    """1920×1080 → max=224. ratio=224/1920≈0.1167. W'=224, H'=126"""
    w, h = resize_aspect_ratio(1920, 1080, 224)
    assert w == 224
    assert h == 126  # round(1080 * 224/1920) = round(126.0) = 126

def test_rar_portrait():
    """1080×1920 → max=224. ratio=224/1920. H'=224, W'=126"""
    w, h = resize_aspect_ratio(1080, 1920, 224)
    assert h == 224
    assert w == 126

def test_rar_square():
    """500×500 → max=300. W'=H'=300"""
    w, h = resize_aspect_ratio(500, 500, 300)
    assert w == 300 and h == 300

def test_rar_no_resize_needed():
    """100×50 → max=100. ratio=1, 不变"""
    w, h = resize_aspect_ratio(100, 50, 100)
    assert w == 100 and h == 50

def test_rar_2_to_1_ratio():
    """800×400 → max=200. ratio=0.25. W'=200, H'=100"""
    w, h = resize_aspect_ratio(800, 400, 200)
    assert w == 200 and h == 100

def test_rar_raises_on_zero():
    with pytest.raises(ValueError):
        resize_aspect_ratio(0, 1080, 224)

def test_rar_raises_on_negative_target():
    with pytest.raises(ValueError):
        resize_aspect_ratio(1920, 1080, -1)

def test_rar_raises_on_non_int():
    with pytest.raises(TypeError):
        resize_aspect_ratio("1920", 1080, 224)


# F4: normalize_pixel_array (transform 类)
def test_npa_basic():
    """[0, 127, 255] / 255 → [0, 0.498, 1.0]"""
    r = normalize_pixel_array([0, 127, 255])
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 127 / 255) < TOL
    assert abs(r[2] - 1.0) < TOL

def test_npa_all_zeros():
    """全 0 → 全 0"""
    r = normalize_pixel_array([0, 0, 0])
    for v in r:
        assert abs(v - 0.0) < TOL

def test_npa_all_max():
    """全 255 → 全 1.0"""
    r = normalize_pixel_array([255, 255, 255])
    for v in r:
        assert abs(v - 1.0) < TOL

def test_npa_custom_max():
    """[0, 8, 16] max_value=16 → [0, 0.5, 1.0] (sklearn.digits 风格)"""
    r = normalize_pixel_array([0, 8, 16], max_value=16)
    expected = [0.0, 0.5, 1.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_npa_intermediate():
    """[64, 128, 192] / 255"""
    r = normalize_pixel_array([64, 128, 192])
    expected = [64 / 255, 128 / 255, 192 / 255]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_npa_raises_on_empty():
    with pytest.raises(ValueError):
        normalize_pixel_array([])

def test_npa_raises_on_out_of_range():
    """超出 [0, max_value] 范围"""
    with pytest.raises(ValueError):
        normalize_pixel_array([0, 300])

def test_npa_raises_on_non_list():
    with pytest.raises(TypeError):
        normalize_pixel_array("abc")
