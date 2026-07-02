"""WX03 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx03 import (
    is_exact_duplicate,
    count_duplicate_rows,
    dedup_preserve_first,
    dedup_keep_last,
)


# F1: is_exact_duplicate. Many "lengths equal but content different" cases to kill shape attack.
def test_dup_identical_3():
    assert is_exact_duplicate([1, 2, 3], [1, 2, 3]) is True

def test_dup_eq_len_diff_one_value():
    """长度相同但值不同 → False (kills 'len equal == True' shape)"""
    assert is_exact_duplicate([1, 2, 3], [1, 2, 4]) is False

def test_dup_eq_len_diff_first():
    assert is_exact_duplicate([5, 2, 3], [1, 2, 3]) is False

def test_dup_eq_len_diff_strings():
    assert is_exact_duplicate(["a", "b"], ["a", "c"]) is False

def test_dup_eq_len_case_sensitive():
    assert is_exact_duplicate(["A", "b"], ["a", "b"]) is False

def test_dup_eq_len_zero_vs_one():
    assert is_exact_duplicate([0, 0], [1, 1]) is False

def test_dup_empty_lists():
    """boundary 空 list"""
    assert is_exact_duplicate([], []) is True

def test_dup_raises_on_non_list():
    with pytest.raises(TypeError):
        is_exact_duplicate("123", [1, 2, 3])


# F2: count_duplicate_rows
def test_cdr_one_pair():
    """[A, A, B] → 1"""
    assert count_duplicate_rows([[1], [1], [2]]) == 1

def test_cdr_three_of_one():
    """[A, A, A, B, C] → 5 - 3 = 2"""
    assert count_duplicate_rows([[1], [1], [1], [2], [3]]) == 2

def test_cdr_all_same():
    """[A, A, A] → 3 - 1 = 2"""
    assert count_duplicate_rows([[1], [1], [1]]) == 2

def test_cdr_complex():
    """[A,A,B,C,A] → 2"""
    assert count_duplicate_rows([["x"], ["x"], ["y"], ["z"], ["x"]]) == 2

def test_cdr_multi_field():
    """多字段: [[1,a], [1,a], [1,b]] → 1"""
    assert count_duplicate_rows([[1, "a"], [1, "a"], [1, "b"]]) == 1

def test_cdr_two_pairs():
    """[A, A, B, B, C] → 5 - 3 = 2"""
    assert count_duplicate_rows([[1], [1], [2], [2], [3]]) == 2

def test_cdr_raises_on_non_list():
    with pytest.raises(TypeError):
        count_duplicate_rows("rows")


# F3: dedup_preserve_first
def test_dpf_simple():
    """[A, A, B] → [A, B]"""
    assert dedup_preserve_first([[1], [1], [2]]) == [[1], [2]]

def test_dpf_repeated():
    """[A, B, A, C, A] → [A, B, C]"""
    assert dedup_preserve_first([[1], [2], [1], [3], [1]]) == [[1], [2], [3]]

def test_dpf_complex():
    rows = [["a"], ["b"], ["c"], ["a"], ["b"], ["d"]]
    assert dedup_preserve_first(rows) == [["a"], ["b"], ["c"], ["d"]]

def test_dpf_multi_field():
    rows = [[1, "x"], [1, "y"], [1, "x"], [2, "z"]]
    assert dedup_preserve_first(rows) == [[1, "x"], [1, "y"], [2, "z"]]

def test_dpf_all_same():
    """[A, A, A] → [A]"""
    assert dedup_preserve_first([[1], [1], [1]]) == [[1]]


# F4: dedup_keep_last — focus on cases where keep_first ≠ keep_last
def test_dkl_repeated_three():
    """[A, B, A, C, B] → [A, C, B] (A末次=2, C=3, B=4)"""
    rows = [["a"], ["b"], ["a"], ["c"], ["b"]]
    assert dedup_keep_last(rows) == [["a"], ["c"], ["b"]]

def test_dkl_two_groups():
    """[A, B, A] → [B, A] (A末次=2 在 B 之后)"""
    assert dedup_keep_last([[1], [2], [1]]) == [[2], [1]]

def test_dkl_back_and_forth():
    """[B, A, B] → [A, B] (B末次=2, A末次=1)"""
    assert dedup_keep_last([[2], [1], [2]]) == [[1], [2]]

def test_dkl_complex():
    """[A, B, C, A, B] → [C, A, B]"""
    rows = [["a"], ["b"], ["c"], ["a"], ["b"]]
    assert dedup_keep_last(rows) == [["c"], ["a"], ["b"]]

def test_dkl_raises_on_non_list():
    with pytest.raises(TypeError):
        dedup_keep_last("rows")
