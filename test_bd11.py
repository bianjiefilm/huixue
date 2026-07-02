"""BD11 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd11 import (
    assign_consumer_partitions,
    compute_minimum_replication,
    is_message_lag_critical,
    compute_throughput_bytes_per_sec,
)


# F1: assign_consumer_partitions
def test_assign_3c_3p():
    """3 consumer / 3 partition → 1:1"""
    r = assign_consumer_partitions(["c1", "c2", "c3"], [0, 1, 2])
    assert r == {"c1": [0], "c2": [1], "c3": [2]}

def test_assign_2c_4p():
    """2 consumer / 4 partition: c1 → [0,2], c2 → [1,3]"""
    r = assign_consumer_partitions(["c1", "c2"], [0, 1, 2, 3])
    assert r == {"c1": [0, 2], "c2": [1, 3]}

def test_assign_3c_5p():
    """3c/5p: c1 → [0,3], c2 → [1,4], c3 → [2]"""
    r = assign_consumer_partitions(["c1", "c2", "c3"], [0, 1, 2, 3, 4])
    assert r == {"c1": [0, 3], "c2": [1, 4], "c3": [2]}

def test_assign_more_consumers_than_partitions():
    """4 consumer / 2 partition: c3, c4 没分配, 仍要在 dict 中"""
    r = assign_consumer_partitions(["c1", "c2", "c3", "c4"], [0, 1])
    assert r == {"c1": [0], "c2": [1], "c3": [], "c4": []}

def test_assign_one_consumer():
    """1c / 5p → 全给 c1"""
    r = assign_consumer_partitions(["c1"], [0, 1, 2, 3, 4])
    assert r == {"c1": [0, 1, 2, 3, 4]}

def test_assign_raises_on_empty_consumers():
    with pytest.raises(ValueError):
        assign_consumer_partitions([], [0, 1])

def test_assign_raises_on_non_list():
    with pytest.raises(TypeError):
        assign_consumer_partitions("c1,c2", [0, 1])


# F2: compute_minimum_replication
def test_repl_basic_3broker_ft2():
    """ft=2, broker=3 → min(3, 3) = 3"""
    assert compute_minimum_replication(2, 3) == 3

def test_repl_ft0():
    """ft=0, broker=5 → max(1, min(1, 5)) = 1"""
    assert compute_minimum_replication(0, 5) == 1

def test_repl_ft1():
    """ft=1, broker=3 → 2"""
    assert compute_minimum_replication(1, 3) == 2

def test_repl_more_brokers():
    """ft=2, broker=10 → 3"""
    assert compute_minimum_replication(2, 10) == 3

def test_repl_raises_when_insufficient_brokers():
    """ft=5, broker=3: ft+1=6 > 3 → ValueError"""
    with pytest.raises(ValueError):
        compute_minimum_replication(5, 3)

def test_repl_raises_on_negative_ft():
    with pytest.raises(ValueError):
        compute_minimum_replication(-1, 3)

def test_repl_raises_on_zero_brokers():
    with pytest.raises(ValueError):
        compute_minimum_replication(0, 0)

def test_repl_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_minimum_replication(2.0, 3)


# F3: is_message_lag_critical
def test_lag_normal():
    """offset=900, log_end=1000, lag=100 < 1000 → False"""
    assert is_message_lag_critical(900, 1000) is False

def test_lag_critical():
    """offset=0, log_end=2000, lag=2000 > 1000 → True"""
    assert is_message_lag_critical(0, 2000) is True

def test_lag_at_threshold():
    """lag=1000 == threshold → False (>, 严格)"""
    assert is_message_lag_critical(0, 1000) is False

def test_lag_just_above():
    """lag=1001 → True"""
    assert is_message_lag_critical(0, 1001) is True

def test_lag_zero():
    """offset == log_end → lag=0, False"""
    assert is_message_lag_critical(500, 500) is False

def test_lag_custom_threshold():
    """threshold=100, lag=200 → True"""
    assert is_message_lag_critical(0, 200, 100) is True

def test_lag_raises_on_consumer_gt_log_end():
    with pytest.raises(ValueError):
        is_message_lag_critical(100, 50)

def test_lag_raises_on_non_int():
    with pytest.raises(TypeError):
        is_message_lag_critical(100.0, 200)


# F4: compute_throughput_bytes_per_sec
def test_tput_typical():
    """1M msg/s × 200B = 200,000,000 = 200 MB/s"""
    assert compute_throughput_bytes_per_sec(1000000, 200) == 200000000

def test_tput_small():
    """1000 msg/s × 100B = 100,000"""
    assert compute_throughput_bytes_per_sec(1000, 100) == 100000

def test_tput_large_messages():
    """100 msg/s × 1MB = 100 MB/s"""
    assert compute_throughput_bytes_per_sec(100, 1024 * 1024) == 100 * 1024 * 1024

def test_tput_minimum():
    """1 msg/s × 1B = 1"""
    assert compute_throughput_bytes_per_sec(1, 1) == 1

def test_tput_raises_on_zero():
    with pytest.raises(ValueError):
        compute_throughput_bytes_per_sec(0, 100)

def test_tput_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_throughput_bytes_per_sec(1000.0, 100)
