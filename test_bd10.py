"""BD10 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd10 import (
    compute_split_size,
    is_incremental_import_valid,
    compute_migration_time_seconds,
    select_split_column_strategy,
)

TOL = 1e-6


# F1: compute_split_size (ceil)
def test_split_typical():
    """100 GB / 16 → ceil(100*1024/16) = 6400 MB"""
    assert compute_split_size(100 * 1024, 16) == 6400

def test_split_partial_ceil():
    """100 / 3 → 34 (ceil 33.33)"""
    assert compute_split_size(100, 3) == 34

def test_split_default_mappers():
    """1000 / 4 → 250"""
    assert compute_split_size(1000, 4) == 250

def test_split_small_table():
    """10 MB / 4 → 3 (ceil 2.5)"""
    assert compute_split_size(10, 4) == 3

def test_split_raises_on_zero_mappers():
    with pytest.raises(ValueError):
        compute_split_size(100, 0)

def test_split_raises_on_zero_table():
    with pytest.raises(ValueError):
        compute_split_size(0, 4)

def test_split_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_split_size(100.0, 4)


# F2: is_incremental_import_valid
def test_inc_valid():
    """1500 > 1000 → True"""
    assert is_incremental_import_valid(1000, 1500) is True

def test_inc_no_new():
    """current == last → False"""
    assert is_incremental_import_valid(1000, 1000) is False

def test_inc_decreased():
    """current < last → False"""
    assert is_incremental_import_valid(1000, 999) is False

def test_inc_raises_on_negative():
    with pytest.raises(ValueError):
        is_incremental_import_valid(-1, 100)

def test_inc_raises_on_non_int():
    with pytest.raises(TypeError):
        is_incremental_import_valid(100.0, 200)


# F3: compute_migration_time_seconds
def test_mig_1m_default():
    """1M / 10000 = 100 秒"""
    assert abs(compute_migration_time_seconds(1000000) - 100.0) < TOL

def test_mig_partial():
    """1500 / 10000 = 0.15"""
    assert abs(compute_migration_time_seconds(1500) - 0.15) < TOL

def test_mig_custom_throughput():
    """100000 / 50000 = 2"""
    assert abs(compute_migration_time_seconds(100000, 50000) - 2.0) < TOL

def test_mig_zero_rows():
    """0 行 → 0 秒"""
    assert abs(compute_migration_time_seconds(0) - 0.0) < TOL

def test_mig_large():
    """1 亿 / 10000 = 10000"""
    assert abs(compute_migration_time_seconds(100000000) - 10000.0) < TOL

def test_mig_raises_on_zero_throughput():
    with pytest.raises(ValueError):
        compute_migration_time_seconds(100, 0)

def test_mig_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_migration_time_seconds(100.0)


# F4: select_split_column_strategy
def test_sel_one_col():
    assert select_split_column_strategy(1) == "numeric_pk"

def test_sel_no_cols():
    assert select_split_column_strategy(0) == "manual"

def test_sel_raises_on_negative():
    with pytest.raises(ValueError):
        select_split_column_strategy(-1)

def test_sel_raises_on_non_int():
    with pytest.raises(TypeError):
        select_split_column_strategy(1.0)
