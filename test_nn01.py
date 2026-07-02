"""NN01 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn01 import (
    count_dense_parameters,
    classify_input_modality,
    compute_data_split_sizes,
    estimate_param_size_mb,
)

TOL = 1e-4


# ============================================================
# F1: count_dense_parameters (多组独特 expected)
# ============================================================

def test_dp_two_layers():
    """[3, 4] → 3*4 + 4 = 16"""
    assert count_dense_parameters([3, 4]) == 16

def test_dp_three_layers():
    """[3, 4, 2] → 16 + (4*2+2) = 26"""
    assert count_dense_parameters([3, 4, 2]) == 26

def test_dp_typical_mnist():
    """[784, 128, 10] → 784*128+128 + 128*10+10 = 100480 + 1290 = 101770"""
    assert count_dense_parameters([784, 128, 10]) == 101770

def test_dp_minimal():
    """[1, 1] → 1*1+1 = 2"""
    assert count_dense_parameters([1, 1]) == 2

def test_dp_four_layers():
    """[100, 50, 25, 10] → 5050 + 1275 + 260 = 6585"""
    assert count_dense_parameters([100, 50, 25, 10]) == 6585

def test_dp_single_layer():
    """边界: [5] 单层无连接 → 0"""
    assert count_dense_parameters([5]) == 0

def test_dp_raises_on_empty():
    """边界: 空列表 → ValueError"""
    with pytest.raises(ValueError):
        count_dense_parameters([])

def test_dp_raises_on_non_list():
    """负例: 非 list → TypeError"""
    with pytest.raises(TypeError):
        count_dense_parameters("abc")


# ============================================================
# F2: classify_input_modality (5 不同模态)
# ============================================================

def test_cim_tabular():
    """(1000,) → 'tabular'"""
    assert classify_input_modality((1000,)) == "tabular"

def test_cim_sequence():
    """(50, 64) → 'sequence'"""
    assert classify_input_modality((50, 64)) == "sequence"

def test_cim_image():
    """(224, 224, 3) → 'image'"""
    assert classify_input_modality((224, 224, 3)) == "image"

def test_cim_video():
    """(16, 224, 224, 3) → 'video'"""
    assert classify_input_modality((16, 224, 224, 3)) == "video"

def test_cim_short_tabular():
    """(5,) → 'tabular'"""
    assert classify_input_modality((5,)) == "tabular"

def test_cim_long_video():
    """(32, 96, 128, 3) → 'video'"""
    assert classify_input_modality((32, 96, 128, 3)) == "video"

def test_cim_raises_on_empty_tuple():
    """边界: () → ValueError"""
    with pytest.raises(ValueError):
        classify_input_modality(())

def test_cim_raises_on_5d():
    """边界: 5D 不支持 → ValueError"""
    with pytest.raises(ValueError):
        classify_input_modality((10, 16, 224, 224, 3))

# test_cim_raises_on_non_tuple 删除: fc 协议 P1 决策 — list 与 tuple 等价


# ============================================================
# F3: compute_data_split_sizes (transform 类)
# ============================================================

def test_cdss_70_15_15():
    """100, [0.7, 0.15, 0.15] → [70, 15, 15]"""
    assert compute_data_split_sizes(100, [0.7, 0.15, 0.15]) == [70, 15, 15]

def test_cdss_50_50():
    """10, [0.5, 0.5] → [5, 5]"""
    assert compute_data_split_sizes(10, [0.5, 0.5]) == [5, 5]

def test_cdss_remainder_to_last():
    """99, [0.6, 0.2, 0.2] → [59, 19, 21] (余数 21 给最后)
    int(99*0.6)=59, int(99*0.2)=19, 99-59-19=21"""
    assert compute_data_split_sizes(99, [0.6, 0.2, 0.2]) == [59, 19, 21]

def test_cdss_8_2_split():
    """4, [0.8, 0.2] → [3, 1] (int(4*0.8)=3, 4-3=1)"""
    assert compute_data_split_sizes(4, [0.8, 0.2]) == [3, 1]

def test_cdss_large():
    """1000, [0.6, 0.2, 0.2] → [600, 200, 200]"""
    assert compute_data_split_sizes(1000, [0.6, 0.2, 0.2]) == [600, 200, 200]

def test_cdss_zero_total():
    """边界: total=0, ratios=[0.5,0.5] → [0, 0]"""
    assert compute_data_split_sizes(0, [0.5, 0.5]) == [0, 0]

def test_cdss_raises_on_bad_ratios():
    """边界: ratios sum != 1.0 → ValueError"""
    with pytest.raises(ValueError):
        compute_data_split_sizes(100, [0.5, 0.4])

def test_cdss_raises_on_negative_total():
    """边界: total 负 → ValueError"""
    with pytest.raises(ValueError):
        compute_data_split_sizes(-10, [0.5, 0.5])

def test_cdss_raises_on_non_list():
    """负例: ratios 非 list → TypeError"""
    with pytest.raises(TypeError):
        compute_data_split_sizes(100, "abc")


# ============================================================
# F4: estimate_param_size_mb (多组独特 expected)
# ============================================================

def test_espm_one_million():
    """1M params → 4M bytes / 1024^2 ≈ 3.8147 MB"""
    r = estimate_param_size_mb(1_000_000)
    assert abs(r - 3.8147) < TOL

def test_espm_zero():
    """0 params → 0 MB"""
    r = estimate_param_size_mb(0)
    assert abs(r - 0.0) < TOL

def test_espm_small_thousand():
    """1000 params → 0.0038 MB"""
    r = estimate_param_size_mb(1_000)
    assert abs(r - 0.003814697) < TOL

def test_espm_resnet50():
    """25M params (ResNet-50 量级) → ~95.37 MB"""
    r = estimate_param_size_mb(25_000_000)
    assert abs(r - 95.367) < 0.01

def test_espm_hundred_million():
    """100M params → ~381.47 MB"""
    r = estimate_param_size_mb(100_000_000)
    assert abs(r - 381.4697) < 0.01

def test_espm_mobilenet():
    """3.5M params (MobileNet 量级) → ~13.35 MB"""
    r = estimate_param_size_mb(3_500_000)
    assert abs(r - 13.3514) < 0.01

def test_espm_raises_on_negative():
    """边界: 负 → ValueError"""
    with pytest.raises(ValueError):
        estimate_param_size_mb(-1)

def test_espm_raises_on_non_int():
    """负例: 非 int → TypeError"""
    with pytest.raises(TypeError):
        estimate_param_size_mb(1.5)
