"""WX09 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx09 import (
    find_orphan_keys,
    has_unique_keys,
    count_referential_violations,
    is_one_to_one_mapping,
)


# F1: find_orphan_keys
def test_orphan_some_orphans():
    """child=[1,2,3,4], parent=[1,2,3] → [4]"""
    assert find_orphan_keys([1, 2, 3, 4], [1, 2, 3]) == [4]

def test_orphan_multiple():
    """child=[1,2,5,7], parent=[1,2] → [5, 7]"""
    assert find_orphan_keys([1, 2, 5, 7], [1, 2]) == [5, 7]

def test_orphan_strings():
    """child=['a','b','c'], parent=['a','c'] → ['b']"""
    assert find_orphan_keys(["a", "b", "c"], ["a", "c"]) == ["b"]

def test_orphan_with_duplicates():
    """重复孤儿都保留: [4,4,5], parent=[1] → [4,4,5]"""
    assert find_orphan_keys([4, 4, 5], [1]) == [4, 4, 5]

def test_orphan_no_orphans():
    """无孤儿 → []"""
    assert find_orphan_keys([1, 2, 3], [1, 2, 3, 4]) == []

def test_orphan_raises_on_non_list():
    with pytest.raises(TypeError):
        find_orphan_keys("123", [1, 2, 3])


# F2: has_unique_keys
def test_unique_with_duplicate():
    assert has_unique_keys([1, 2, 3, 2]) is False

def test_unique_strings():
    assert has_unique_keys(["a", "b", "c"]) is True

def test_unique_strings_dup():
    assert has_unique_keys(["a", "b", "a"]) is False

def test_unique_all_same():
    assert has_unique_keys([1, 1, 1]) is False

def test_unique_raises_on_non_list():
    with pytest.raises(TypeError):
        has_unique_keys("123")


# F3: count_referential_violations
def test_crv_two_violations():
    """[1,2,5,7] vs parent=[1,2] → 2"""
    assert count_referential_violations([1, 2, 5, 7], [1, 2]) == 2

def test_crv_three_violations():
    """[1,2,3,99,100,101] vs parent=[1,2,3] → 3"""
    assert count_referential_violations([1, 2, 3, 99, 100, 101], [1, 2, 3]) == 3

def test_crv_one_violation():
    """[1,2,3,4] vs parent=[1,2,3] → 1"""
    assert count_referential_violations([1, 2, 3, 4], [1, 2, 3]) == 1

def test_crv_with_duplicate_violations():
    """[4,4,5] vs parent=[1] → 3"""
    assert count_referential_violations([4, 4, 5], [1]) == 3

def test_crv_no_violations():
    """全在 parent → 0"""
    assert count_referential_violations([1, 2], [1, 2, 3, 4]) == 0

def test_crv_raises_on_non_list():
    with pytest.raises(TypeError):
        count_referential_violations(123, [1, 2])


# F4: is_one_to_one_mapping
def test_one_to_one_left_dup():
    """left 有重复 → 非 1-1"""
    assert is_one_to_one_mapping([1, 1, 2], ["a", "b", "c"]) is False

def test_one_to_one_right_dup():
    """right 有重复 → 非 1-1"""
    assert is_one_to_one_mapping([1, 2, 3], ["a", "a", "c"]) is False

def test_one_to_one_unequal_length():
    """长度不等 → 非 1-1"""
    assert is_one_to_one_mapping([1, 2, 3], ["a", "b"]) is False

def test_one_to_one_both_dup():
    """两边都有重复 → 非 1-1"""
    assert is_one_to_one_mapping([1, 1], ["a", "a"]) is False

def test_one_to_one_single_pair():
    """boundary: 单对 → True"""
    assert is_one_to_one_mapping([1], ["a"]) is True

def test_one_to_one_raises_on_non_list():
    with pytest.raises(TypeError):
        is_one_to_one_mapping("123", [1, 2, 3])
