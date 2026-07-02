"""BD08 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd08 import (
    compute_partition_pruning_set,
    estimate_query_cost,
    should_use_broadcast_join,
    count_distinct_simple,
)


# F1: compute_partition_pruning_set
def test_pps_overlap_2():
    """filter=[a,b,c], avail=[b,c,d] → [b, c]"""
    assert compute_partition_pruning_set(["a", "b", "c"], ["b", "c", "d"]) == ["b", "c"]

def test_pps_no_overlap():
    """无交集 → []"""
    assert compute_partition_pruning_set(["x"], ["a", "b"]) == []

def test_pps_all_in_filter():
    """filter ⊂ available → filter (升序)"""
    assert compute_partition_pruning_set(["c", "a"], ["a", "b", "c"]) == ["a", "c"]

def test_pps_dedup_filter():
    """filter 含重复 → 输出去重"""
    assert compute_partition_pruning_set(["a", "a", "b"], ["a", "b", "c"]) == ["a", "b"]

def test_pps_dates():
    """日期分区交集"""
    f = ["2026-04-25", "2026-04-26", "2026-04-30"]
    a = ["2026-04-25", "2026-04-26", "2026-04-27", "2026-04-28"]
    assert compute_partition_pruning_set(f, a) == ["2026-04-25", "2026-04-26"]

def test_pps_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_partition_pruning_set("a,b", ["a"])


# F2: estimate_query_cost (rows * (joins + 1))
def test_cost_no_join():
    """1000 行, 0 join → 1000"""
    assert estimate_query_cost(1000, 0) == 1000

def test_cost_one_join():
    """1000 行, 1 join → 2000"""
    assert estimate_query_cost(1000, 1) == 2000

def test_cost_three_joins():
    """500 行, 3 join → 500 × 4 = 2000"""
    assert estimate_query_cost(500, 3) == 2000

def test_cost_large():
    """1M 行 1 join → 2M"""
    assert estimate_query_cost(1000000, 1) == 2000000

def test_cost_raises_on_negative_rows():
    with pytest.raises(ValueError):
        estimate_query_cost(-1, 1)

def test_cost_raises_on_negative_joins():
    with pytest.raises(ValueError):
        estimate_query_cost(100, -1)

def test_cost_raises_on_non_int():
    with pytest.raises(TypeError):
        estimate_query_cost(100.0, 1)


# F3: should_use_broadcast_join
def test_bcast_right_small():
    """左 10M, 右 1000 → broadcast"""
    assert should_use_broadcast_join(10000000, 1000) == "broadcast"

def test_bcast_both_large():
    """左 5M, 右 10M → shuffle"""
    assert should_use_broadcast_join(5000000, 10000000) == "shuffle"

def test_bcast_at_threshold():
    """1M == threshold → shuffle (严格 <)"""
    assert should_use_broadcast_join(1000000, 5000000) == "shuffle"

def test_bcast_custom_threshold():
    """threshold=100, 左 50 → broadcast"""
    assert should_use_broadcast_join(50, 1000, 100) == "broadcast"

def test_bcast_raises_on_zero():
    with pytest.raises(ValueError):
        should_use_broadcast_join(0, 100)

def test_bcast_raises_on_non_int():
    with pytest.raises(TypeError):
        should_use_broadcast_join(100.0, 200)


# F4: count_distinct_simple
def test_dist_typical():
    """[1, 2, 3, 2, 1] → 3"""
    assert count_distinct_simple([1, 2, 3, 2, 1]) == 3

def test_dist_all_same():
    """[1, 1, 1] → 1"""
    assert count_distinct_simple([1, 1, 1]) == 1

def test_dist_strings():
    """['a', 'b', 'a', 'c'] → 3"""
    assert count_distinct_simple(["a", "b", "a", "c"]) == 3

def test_dist_empty():
    """[] → 0 (boundary)"""
    assert count_distinct_simple([]) == 0

def test_dist_raises_on_non_list():
    with pytest.raises(TypeError):
        count_distinct_simple("abc")
