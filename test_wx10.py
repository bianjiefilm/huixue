"""WX10 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx10 import (
    merge_inner_by_key,
    merge_left_by_key,
    dedup_dicts_by_key,
    compute_merge_size,
)


# F1: merge_inner_by_key
def test_inner_basic():
    left = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    right = [{"id": 1, "age": 10}, {"id": 3, "age": 30}]
    r = merge_inner_by_key(left, right, "id")
    assert r == [{"id": 1, "name": "a", "age": 10}]

def test_inner_two_matches():
    left = [{"id": 1}, {"id": 2}]
    right = [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]
    r = merge_inner_by_key(left, right, "id")
    assert r == [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]

def test_inner_no_match():
    left = [{"id": 1}]
    right = [{"id": 2}]
    r = merge_inner_by_key(left, right, "id")
    assert r == []

def test_inner_field_merge():
    """字段合并, 右覆盖左"""
    left = [{"id": 1, "name": "alice", "x": 0}]
    right = [{"id": 1, "x": 99}]
    r = merge_inner_by_key(left, right, "id")
    assert r == [{"id": 1, "name": "alice", "x": 99}]

def test_inner_raises_on_missing_key():
    with pytest.raises(ValueError):
        merge_inner_by_key([{"id": 1}], [{"foo": 1}], "id")

def test_inner_raises_on_non_list():
    with pytest.raises(TypeError):
        merge_inner_by_key("left", [], "id")


# F2: merge_left_by_key
def test_left_with_match():
    left = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}]
    right = [{"id": 1, "v": 10}]
    r = merge_left_by_key(left, right, "id")
    assert r == [{"id": 1, "n": "a", "v": 10}, {"id": 2, "n": "b"}]

def test_left_no_match_at_all():
    """无匹配 → 全部保留左"""
    left = [{"id": 1}, {"id": 2}]
    right = [{"id": 99}]
    r = merge_left_by_key(left, right, "id")
    assert r == [{"id": 1}, {"id": 2}]

def test_left_one_to_many():
    """1:N: 左 1 条匹配右 2 条 → 2 条结果"""
    left = [{"id": 1}]
    right = [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}]
    r = merge_left_by_key(left, right, "id")
    assert r == [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}]

def test_left_mixed():
    left = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}, {"id": 3, "n": "c"}]
    right = [{"id": 1, "v": 10}, {"id": 3, "v": 30}]
    r = merge_left_by_key(left, right, "id")
    assert r == [
        {"id": 1, "n": "a", "v": 10},
        {"id": 2, "n": "b"},
        {"id": 3, "n": "c", "v": 30},
    ]

def test_left_raises_on_missing_key():
    with pytest.raises(ValueError):
        merge_left_by_key([{"foo": 1}], [{"id": 1}], "id")


# F3: dedup_dicts_by_key
def test_dedup_one_dup():
    rows = [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}, {"id": 1, "v": "x2"}]
    r = dedup_dicts_by_key(rows, "id")
    assert r == [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]

def test_dedup_keeps_first():
    """保留首次"""
    rows = [{"id": 1, "v": "first"}, {"id": 1, "v": "second"}]
    r = dedup_dicts_by_key(rows, "id")
    assert r == [{"id": 1, "v": "first"}]

def test_dedup_no_duplicates():
    rows = [{"id": 1}, {"id": 2}, {"id": 3}]
    r = dedup_dicts_by_key(rows, "id")
    assert r == [{"id": 1}, {"id": 2}, {"id": 3}]

def test_dedup_all_same_key():
    rows = [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}, {"id": 1, "v": "c"}]
    r = dedup_dicts_by_key(rows, "id")
    assert r == [{"id": 1, "v": "a"}]

def test_dedup_raises_on_missing_key():
    with pytest.raises(ValueError):
        dedup_dicts_by_key([{"foo": 1}], "id")


# F4: compute_merge_size
def test_size_inner_basic():
    """common_n=5"""
    assert compute_merge_size(10, 8, 5, "inner") == 5

def test_size_left_basic():
    assert compute_merge_size(10, 8, 5, "left") == 10

def test_size_right_basic():
    assert compute_merge_size(10, 8, 5, "right") == 8

def test_size_outer_basic():
    """outer = 10 + 8 - 5 = 13"""
    assert compute_merge_size(10, 8, 5, "outer") == 13

def test_size_inner_no_common():
    """common=0"""
    assert compute_merge_size(10, 8, 0, "inner") == 0

def test_size_outer_full_overlap():
    """common = min(L, R), outer = max(L, R)"""
    assert compute_merge_size(10, 8, 8, "outer") == 10

def test_size_raises_on_unknown_mode():
    with pytest.raises(ValueError):
        compute_merge_size(10, 8, 5, "weird")

def test_size_raises_on_negative():
    with pytest.raises(ValueError):
        compute_merge_size(-1, 8, 5, "inner")

def test_size_raises_on_common_too_large():
    """common > min(L, R)"""
    with pytest.raises(ValueError):
        compute_merge_size(5, 3, 10, "inner")

def test_size_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_merge_size(10.0, 8, 5, "inner")
