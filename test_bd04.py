"""BD04 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd04 import (
    compute_map_task_count,
    compute_reduce_task_count,
    partition_by_hash,
    is_combinable_operation,
)


# F1: compute_map_task_count
def test_map_single_file():
    """[300MB] / 128MB → ceil(300/128) = 3"""
    assert compute_map_task_count([300 * 1024 * 1024]) == 3

def test_map_two_files():
    """[100MB, 200MB] / 128MB → ceil(100/128)+ceil(200/128) = 1+2 = 3"""
    assert compute_map_task_count([100 * 1024 * 1024, 200 * 1024 * 1024]) == 3

def test_map_custom_split_64mb():
    """[300MB] / 64MB → 5"""
    assert compute_map_task_count([300 * 1024 * 1024], 64 * 1024 * 1024) == 5

def test_map_three_files_default():
    """[128MB, 256MB, 64MB] → 1+2+1 = 4"""
    sizes = [128 * 1024 * 1024, 256 * 1024 * 1024, 64 * 1024 * 1024]
    assert compute_map_task_count(sizes) == 4

def test_map_raises_on_zero_split():
    with pytest.raises(ValueError):
        compute_map_task_count([100], 0)

def test_map_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_map_task_count("100")


# F2: compute_reduce_task_count
def test_reduce_5gb_default():
    """5 GB / 1 GB → 5"""
    assert compute_reduce_task_count(5 * 1024) == 5

def test_reduce_partial_ceil():
    """1500 MB / 1024 MB → ceil = 2"""
    assert compute_reduce_task_count(1500) == 2

def test_reduce_custom_target_500mb():
    """5 GB / 500 MB → 11 (ceil 5120/500)"""
    assert compute_reduce_task_count(5 * 1024, 500) == 11

def test_reduce_raises_on_zero_data():
    with pytest.raises(ValueError):
        compute_reduce_task_count(0)

def test_reduce_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_reduce_task_count(100.0)


# F3: partition_by_hash. sum(ord(c)) % num_reducers
def test_part_simple():
    """'a' → ord('a')=97, 97 % 5 = 2"""
    assert partition_by_hash("a", 5) == 2

def test_part_word():
    """'hello' → 104+101+108+108+111 = 532, 532 % 7 = 525/7=75 余 7? 7*76=532 余 0"""
    assert partition_by_hash("hello", 7) == 532 % 7

def test_part_long_word():
    """'mapreduce' sum = 109+97+112+114+101+100+117+99+101 = 950, 950 % 10"""
    expected = sum(ord(c) for c in "mapreduce") % 10
    assert partition_by_hash("mapreduce", 10) == expected

def test_part_raises_on_empty_key():
    with pytest.raises(ValueError):
        partition_by_hash("", 5)

def test_part_raises_on_zero_reducers():
    with pytest.raises(ValueError):
        partition_by_hash("a", 0)

def test_part_raises_on_non_string():
    with pytest.raises(TypeError):
        partition_by_hash(123, 5)


# F4: is_combinable_operation
def test_comb_max():
    assert is_combinable_operation("max") is True

def test_comb_min():
    assert is_combinable_operation("min") is True

def test_comb_avg():
    """avg 不可 combine"""
    assert is_combinable_operation("avg") is False

def test_comb_median():
    assert is_combinable_operation("median") is False

def test_comb_distinct():
    assert is_combinable_operation("distinct") is False

def test_comb_raises_on_unknown():
    with pytest.raises(ValueError):
        is_combinable_operation("unknown_op")

def test_comb_raises_on_non_string():
    with pytest.raises(TypeError):
        is_combinable_operation(123)
