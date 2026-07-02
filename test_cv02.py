"""CV02 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv02 import (
    rgb_to_grayscale,
    rgb_to_hsv,
    apply_threshold,
    compute_histogram,
)

TOL = 1e-4


# F1: rgb_to_grayscale
def test_g_pure_red():
    """R=255 → 0.299*255 = 76.245"""
    assert abs(rgb_to_grayscale((255, 0, 0)) - 76.245) < TOL

def test_g_pure_green():
    """G=255 → 0.587*255 = 149.685"""
    assert abs(rgb_to_grayscale((0, 255, 0)) - 149.685) < TOL

def test_g_pure_blue():
    """B=255 → 0.114*255 = 29.07"""
    assert abs(rgb_to_grayscale((0, 0, 255)) - 29.07) < TOL

def test_g_white():
    """255,255,255 → 255"""
    assert abs(rgb_to_grayscale((255, 255, 255)) - 255.0) < TOL

def test_g_black():
    """0,0,0 → 0"""
    assert abs(rgb_to_grayscale((0, 0, 0)) - 0.0) < TOL

def test_g_raises_on_wrong_length():
    with pytest.raises(ValueError):
        rgb_to_grayscale((255, 0))

def test_g_raises_on_out_of_range():
    with pytest.raises(ValueError):
        rgb_to_grayscale((300, 0, 0))

# test_g_raises_on_non_tuple 删除: fc 协议 P1 决策 — list 与 tuple 等价


# F2: rgb_to_hsv
def test_hsv_pure_red():
    """(1,0,0) → H=0, S=1, V=1"""
    h, s, v = rgb_to_hsv((1.0, 0.0, 0.0))
    assert abs(h - 0.0) < TOL
    assert abs(s - 1.0) < TOL
    assert abs(v - 1.0) < TOL

def test_hsv_pure_green():
    """(0,1,0) → H=120, S=1, V=1"""
    h, s, v = rgb_to_hsv((0.0, 1.0, 0.0))
    assert abs(h - 120.0) < TOL
    assert abs(s - 1.0) < TOL

def test_hsv_pure_blue():
    """(0,0,1) → H=240, S=1, V=1"""
    h, s, v = rgb_to_hsv((0.0, 0.0, 1.0))
    assert abs(h - 240.0) < TOL

def test_hsv_white():
    """(1,1,1) → S=0, V=1, H 不重要 (灰色)"""
    h, s, v = rgb_to_hsv((1.0, 1.0, 1.0))
    assert abs(s - 0.0) < TOL
    assert abs(v - 1.0) < TOL

def test_hsv_black():
    """(0,0,0) → V=0, S=0"""
    h, s, v = rgb_to_hsv((0.0, 0.0, 0.0))
    assert abs(s - 0.0) < TOL
    assert abs(v - 0.0) < TOL

def test_hsv_raises_on_wrong_length():
    with pytest.raises(ValueError):
        rgb_to_hsv((1.0, 0.5))

def test_hsv_raises_on_out_of_range():
    with pytest.raises(ValueError):
        rgb_to_hsv((1.5, 0.5, 0.5))

# test_hsv_raises_on_non_tuple 删除: fc 协议 P1 决策 — list 与 tuple 等价


# F3: apply_threshold (transform 类)
def test_thresh_basic():
    """[100, 150, 200] T=128 → [0, 255, 255]"""
    assert apply_threshold([100, 150, 200], 128) == [0, 255, 255]

def test_thresh_at_boundary():
    """T=128: x=128 → 0 (>= 不算), x=129 → 255"""
    assert apply_threshold([127, 128, 129], 128) == [0, 0, 255]

def test_thresh_low_threshold():
    """T=10: 大部分都是 255"""
    assert apply_threshold([5, 50, 100, 200], 10) == [0, 255, 255, 255]

def test_thresh_high_threshold():
    """T=240: 大部分都是 0"""
    assert apply_threshold([100, 200, 250], 240) == [0, 0, 255]

def test_thresh_default_128():
    """默认 threshold=128"""
    assert apply_threshold([50, 200]) == [0, 255]

def test_thresh_raises_on_empty():
    with pytest.raises(ValueError):
        apply_threshold([])

def test_thresh_raises_on_invalid_threshold():
    with pytest.raises(ValueError):
        apply_threshold([100], 300)

def test_thresh_raises_on_non_list():
    with pytest.raises(TypeError):
        apply_threshold("abc")


# F4: compute_histogram (transform 类)
def test_hist_uniform():
    """[0, 50, 100, 150, 200, 255] n_bins=5: 每 bin 范围 ~51, 大致均匀"""
    r = compute_histogram([0, 50, 100, 150, 200, 255], n_bins=5)
    assert sum(r) == 6
    assert len(r) == 5

def test_hist_all_same():
    """[100]*10 n_bins=4 max=255: 全在一个 bin"""
    r = compute_histogram([100] * 10, n_bins=4, max_value=255)
    assert sum(r) == 10
    # 100 落在 bin 1 (64-127), n_bins=4, step=64
    assert r[1] == 10 or r.count(10) == 1

def test_hist_extremes():
    """[0, 0, 255, 255] n_bins=2 max=255: 各 bin 2 个"""
    r = compute_histogram([0, 0, 255, 255], n_bins=2, max_value=255)
    assert r == [2, 2]

def test_hist_max_value_inclusive():
    """max_value 必须落在最后 bin"""
    r = compute_histogram([255], n_bins=10, max_value=255)
    assert r[-1] == 1

def test_hist_smaller_max():
    """[0, 8, 16] n_bins=4 max=16: step=17/4≈4.25
    bin 0: 0-3, bin 1: 4-8, bin 2: 9-12, bin 3: 13-16"""
    r = compute_histogram([0, 8, 16], n_bins=4, max_value=16)
    assert sum(r) == 3

def test_hist_raises_on_empty():
    with pytest.raises(ValueError):
        compute_histogram([], n_bins=5)

def test_hist_raises_on_zero_bins():
    with pytest.raises(ValueError):
        compute_histogram([100], n_bins=0)

def test_hist_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_histogram("abc")
