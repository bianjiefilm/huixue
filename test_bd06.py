"""BD06 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd06 import (
    compute_yarn_container_count,
    is_resource_request_valid,
    assign_yarn_queue,
    compute_fair_share_for_job,
)


# F1: compute_yarn_container_count (floor)
def test_cont_8tb_8gb():
    """8000 GB / 8 GB = 1000"""
    assert compute_yarn_container_count(8000, 8) == 1000

def test_cont_partial():
    """100 GB / 8 GB = floor(12.5) = 12"""
    assert compute_yarn_container_count(100, 8) == 12

def test_cont_exact():
    """64 GB / 16 GB = 4"""
    assert compute_yarn_container_count(64, 16) == 4

def test_cont_uneven():
    """50 GB / 4 GB = floor(12.5) = 12"""
    assert compute_yarn_container_count(50, 4) == 12

def test_cont_raises_on_zero_total():
    with pytest.raises(ValueError):
        compute_yarn_container_count(0, 8)

def test_cont_raises_on_zero_container():
    with pytest.raises(ValueError):
        compute_yarn_container_count(100, 0)

def test_cont_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_yarn_container_count(100.0, 8)


# F2: is_resource_request_valid
def test_req_too_much_mem():
    """req mem 50 > max 32 → False"""
    assert is_resource_request_valid(50, 4) is False

def test_req_too_much_cpu():
    """req cpu 20 > max 16 → False"""
    assert is_resource_request_valid(8, 20) is False

def test_req_zero_mem():
    """req mem = 0 → False"""
    assert is_resource_request_valid(0, 4) is False

def test_req_at_max_boundary():
    """req == max → True (boundary)"""
    assert is_resource_request_valid(32, 16) is True

def test_req_custom_limits():
    """custom: max=(16, 8), req=(10, 6) → True"""
    assert is_resource_request_valid(10, 6, 16, 8) is True

def test_req_raises_on_non_int():
    with pytest.raises(TypeError):
        is_resource_request_valid(8.0, 4)


# F3: assign_yarn_queue
def test_queue_production_high():
    """priority=10 → production"""
    assert assign_yarn_queue(10) == "production"

def test_queue_production_at_8():
    """priority=8 → production (boundary)"""
    assert assign_yarn_queue(8) == "production"

def test_queue_default_at_4():
    """priority=4 → default"""
    assert assign_yarn_queue(4) == "default"

def test_queue_default_at_7():
    """priority=7 → default"""
    assert assign_yarn_queue(7) == "default"

def test_queue_low_at_3():
    """priority=3 → low"""
    assert assign_yarn_queue(3) == "low"

def test_queue_low_at_0():
    """priority=0 → low"""
    assert assign_yarn_queue(0) == "low"

def test_queue_low_negative():
    """priority=-5 → low"""
    assert assign_yarn_queue(-5) == "low"

def test_queue_raises_on_non_int():
    with pytest.raises(TypeError):
        assign_yarn_queue(5.0)


# F4: compute_fair_share_for_job
def test_share_third():
    """w=10, total_w=30, R=8000 → 8000*10/30 = 2666.67 → 2666"""
    assert compute_fair_share_for_job(10, 30, 8000) == 2666

def test_share_quarter():
    """w=2, total_w=8, R=1000 → 250"""
    assert compute_fair_share_for_job(2, 8, 1000) == 250

def test_share_half():
    """w=5, total_w=10, R=100 → 50"""
    assert compute_fair_share_for_job(5, 10, 100) == 50

def test_share_full():
    """w=10, total_w=10, R=500 → 500 (单一 job 占全部)"""
    assert compute_fair_share_for_job(10, 10, 500) == 500

def test_share_floor_truncate():
    """w=1, total_w=3, R=100 → 33 (floor 33.33)"""
    assert compute_fair_share_for_job(1, 3, 100) == 33

def test_share_zero_resources():
    """R=0 → 0"""
    assert compute_fair_share_for_job(5, 10, 0) == 0

def test_share_raises_on_zero_weight():
    with pytest.raises(ValueError):
        compute_fair_share_for_job(0, 10, 100)

def test_share_raises_on_zero_total():
    with pytest.raises(ValueError):
        compute_fair_share_for_job(5, 0, 100)

def test_share_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_fair_share_for_job(5.0, 10, 100)
