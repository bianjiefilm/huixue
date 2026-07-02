"""BD07 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd07 import (
    compute_partition_count,
    is_partition_pruning_helpful,
    compute_data_warehouse_size,
    get_hive_storage_format,
)

TOL = 1e-6


# F1: compute_partition_count (ceil)
def test_part_typical():
    """100M 行 / 1M 每分区 → 100"""
    assert compute_partition_count(100000000, 1000000) == 100

def test_part_partial_ceil():
    """1.5M / 1M → 2 (ceil)"""
    assert compute_partition_count(1500000, 1000000) == 2

def test_part_just_one():
    """500K / 1M → 1"""
    assert compute_partition_count(500000, 1000000) == 1

def test_part_zero_rows():
    """boundary: 0 行 → 0"""
    assert compute_partition_count(0, 1000) == 0

def test_part_exact():
    """3M / 1M → 3"""
    assert compute_partition_count(3000000, 1000000) == 3

def test_part_raises_on_zero_per_partition():
    with pytest.raises(ValueError):
        compute_partition_count(100, 0)

def test_part_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_partition_count(100.0, 10)


# F2: is_partition_pruning_helpful (q/total < threshold → True)
def test_prune_helpful_1_of_90():
    """1/90 < 0.5 → True"""
    assert is_partition_pruning_helpful(1, 90) is True

def test_prune_not_helpful_60_of_90():
    """60/90 = 0.66 > 0.5 → False"""
    assert is_partition_pruning_helpful(60, 90) is False

def test_prune_at_threshold():
    """45/90 = 0.5 == threshold → False (严格 <)"""
    assert is_partition_pruning_helpful(45, 90) is False

def test_prune_custom_threshold_03():
    """20/100 = 0.2 < 0.3 → True"""
    assert is_partition_pruning_helpful(20, 100, 0.3) is True

def test_prune_raises_on_zero_total():
    with pytest.raises(ValueError):
        is_partition_pruning_helpful(0, 0)


# F3: compute_data_warehouse_size
def test_dw_default_orc():
    """1000 × 3 × 0.2 = 600"""
    assert abs(compute_data_warehouse_size(1000, 3, 0.2) - 600.0) < TOL

def test_dw_no_compression():
    """1000 × 3 × 1.0 = 3000"""
    assert abs(compute_data_warehouse_size(1000, 3, 1.0) - 3000.0) < TOL

def test_dw_replication_1():
    """500 × 1 × 0.5 = 250"""
    assert abs(compute_data_warehouse_size(500, 1, 0.5) - 250.0) < TOL

def test_dw_zero_size():
    """0 × * × * = 0"""
    assert abs(compute_data_warehouse_size(0, 3, 0.5) - 0.0) < TOL

def test_dw_decimal_compression():
    """100 × 3 × 0.25 = 75"""
    assert abs(compute_data_warehouse_size(100, 3, 0.25) - 75.0) < TOL

def test_dw_raises_on_negative_size():
    with pytest.raises(ValueError):
        compute_data_warehouse_size(-1, 3, 0.5)

def test_dw_raises_on_zero_replication():
    with pytest.raises(ValueError):
        compute_data_warehouse_size(100, 0, 0.5)

def test_dw_raises_on_zero_compression():
    with pytest.raises(ValueError):
        compute_data_warehouse_size(100, 3, 0)


# F4: get_hive_storage_format
def test_format_analytical():
    assert get_hive_storage_format("analytical") == "orc"

def test_format_compatibility():
    assert get_hive_storage_format("compatibility") == "parquet"

def test_format_simple():
    assert get_hive_storage_format("simple") == "textfile"

def test_format_raises_on_unknown():
    with pytest.raises(ValueError):
        get_hive_storage_format("unknown")

def test_format_raises_on_empty():
    with pytest.raises(ValueError):
        get_hive_storage_format("")

def test_format_raises_on_non_string():
    with pytest.raises(TypeError):
        get_hive_storage_format(123)
