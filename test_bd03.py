"""BD03 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd03 import (
    compute_data_locality_score,
    is_replication_factor_valid,
    count_blocks_to_re_replicate,
    assign_replicas_round_robin,
)

TOL = 1e-6


# F1: compute_data_locality_score
def test_loc_one_third():
    """1 / 3 = 0.333..."""
    assert abs(compute_data_locality_score(1, 3) - 1.0/3) < TOL

def test_loc_two_thirds():
    """2 / 3 = 0.666..."""
    assert abs(compute_data_locality_score(2, 3) - 2.0/3) < TOL

def test_loc_three_in_5():
    """3 / 5 = 0.6"""
    assert abs(compute_data_locality_score(3, 5) - 0.6) < TOL

def test_loc_perfect():
    """3 / 3 = 1.0 (boundary)"""
    assert abs(compute_data_locality_score(3, 3) - 1.0) < TOL

def test_loc_raises_on_zero_total():
    with pytest.raises(ValueError):
        compute_data_locality_score(0, 0)

def test_loc_raises_on_local_gt_total():
    with pytest.raises(ValueError):
        compute_data_locality_score(5, 3)

def test_loc_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_data_locality_score(1.0, 3)


# F2: is_replication_factor_valid
def test_repl_too_many():
    """5 副本, 3 DataNode → False"""
    assert is_replication_factor_valid(5, 3) is False

def test_repl_zero():
    """0 副本 → False"""
    assert is_replication_factor_valid(0, 10) is False

def test_repl_raises_on_negative():
    with pytest.raises(ValueError):
        is_replication_factor_valid(-1, 10)

def test_repl_raises_on_non_int():
    with pytest.raises(TypeError):
        is_replication_factor_valid(3.0, 10)


# F3: count_blocks_to_re_replicate (count r < target)
def test_re_repl_one_under():
    """[3, 2, 3] target=3 → 1"""
    assert count_blocks_to_re_replicate([3, 2, 3], 3) == 1

def test_re_repl_three_under():
    """[1, 2, 3, 1, 4] target=3 → 3 (1, 2, 1 都 < 3)"""
    assert count_blocks_to_re_replicate([1, 2, 3, 1, 4], 3) == 3

def test_re_repl_default_target():
    """default target=3"""
    assert count_blocks_to_re_replicate([3, 4, 5]) == 0

def test_re_repl_custom_target_5():
    """target=5: [3, 4, 5, 6] → 2 (3, 4 < 5)"""
    assert count_blocks_to_re_replicate([3, 4, 5, 6], 5) == 2

def test_re_repl_raises_on_negative_count():
    with pytest.raises(ValueError):
        count_blocks_to_re_replicate([3, -1, 3])

def test_re_repl_raises_on_non_list():
    with pytest.raises(TypeError):
        count_blocks_to_re_replicate("123")


# F4: assign_replicas_round_robin
def test_rr_3_replicas_3_racks():
    """3 副本 3 机架 → [0, 1, 2]"""
    assert assign_replicas_round_robin(3, 3) == [0, 1, 2]

def test_rr_4_replicas_3_racks():
    """4 副本 3 机架 → [0, 1, 2, 0]"""
    assert assign_replicas_round_robin(4, 3) == [0, 1, 2, 0]

def test_rr_2_replicas_4_racks():
    """2 副本 4 机架 → [0, 1]"""
    assert assign_replicas_round_robin(2, 4) == [0, 1]

def test_rr_5_replicas_2_racks():
    """5 副本 2 机架 → [0, 1, 0, 1, 0]"""
    assert assign_replicas_round_robin(5, 2) == [0, 1, 0, 1, 0]

def test_rr_raises_on_zero_racks():
    with pytest.raises(ValueError):
        assign_replicas_round_robin(3, 0)

def test_rr_raises_on_negative_replicas():
    with pytest.raises(ValueError):
        assign_replicas_round_robin(-1, 3)

def test_rr_raises_on_non_int():
    with pytest.raises(TypeError):
        assign_replicas_round_robin(3.0, 3)
