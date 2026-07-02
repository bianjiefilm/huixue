"""BD05 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd05 import (
    word_count,
    inverted_index,
    top_k_frequent,
    compute_co_occurrence,
)


# F1: word_count
def test_wc_basic():
    """['the cat', 'cat sat'] → {'the':1, 'cat':2, 'sat':1}"""
    assert word_count(["the cat", "cat sat"]) == {"the": 1, "cat": 2, "sat": 1}

def test_wc_three_words_same():
    """['a a a'] → {'a': 3}"""
    assert word_count(["a a a"]) == {"a": 3}

def test_wc_case_sensitive():
    """['Hello hello'] → {'Hello': 1, 'hello': 1}"""
    assert word_count(["Hello hello"]) == {"Hello": 1, "hello": 1}

def test_wc_three_docs():
    """['x y z', 'x y', 'x'] → {'x':3, 'y':2, 'z':1}"""
    assert word_count(["x y z", "x y", "x"]) == {"x": 3, "y": 2, "z": 1}

def test_wc_empty_doc():
    """['', 'a b'] → {'a':1, 'b':1}"""
    assert word_count(["", "a b"]) == {"a": 1, "b": 1}

def test_wc_raises_on_non_list():
    with pytest.raises(TypeError):
        word_count("not a list")


# F2: inverted_index
def test_ii_basic():
    """[[a,b], [b,c]] → {'a':[0], 'b':[0,1], 'c':[1]}"""
    docs = [["a", "b"], ["b", "c"]]
    r = inverted_index(docs)
    assert r == {"a": [0], "b": [0, 1], "c": [1]}

def test_ii_dedup_within_doc():
    """[[a,a,b]] → {'a':[0], 'b':[0]} (a 在 doc 0 多次, 只算一次)"""
    docs = [["a", "a", "b"]]
    r = inverted_index(docs)
    assert r == {"a": [0], "b": [0]}

def test_ii_three_docs():
    """[[x],[x,y],[y,z]] → {'x':[0,1], 'y':[1,2], 'z':[2]}"""
    docs = [["x"], ["x", "y"], ["y", "z"]]
    r = inverted_index(docs)
    assert r == {"x": [0, 1], "y": [1, 2], "z": [2]}

def test_ii_empty_doc():
    """[[a], [], [a]] → {'a': [0, 2]}"""
    docs = [["a"], [], ["a"]]
    r = inverted_index(docs)
    assert r == {"a": [0, 2]}

def test_ii_raises_on_non_list():
    with pytest.raises(TypeError):
        inverted_index("not a list")


# F3: top_k_frequent
def test_tk_basic():
    """{'a':3, 'b':2, 'c':1} k=2 → ['a', 'b']"""
    assert top_k_frequent({"a": 3, "b": 2, "c": 1}, 2) == ["a", "b"]

def test_tk_tie_alphabetical():
    """{'b':2, 'a':2, 'c':1} k=2 → ['a', 'b'] (同频按字母升序)"""
    assert top_k_frequent({"b": 2, "a": 2, "c": 1}, 2) == ["a", "b"]

def test_tk_k_equals_size():
    """k = len, 全返回排序"""
    assert top_k_frequent({"a": 3, "b": 1, "c": 2}, 3) == ["a", "c", "b"]

def test_tk_k_larger_than_size():
    """k > len, 返回全部"""
    assert top_k_frequent({"a": 3, "b": 2}, 10) == ["a", "b"]

def test_tk_all_same_freq():
    """全同频, 字母升序"""
    assert top_k_frequent({"c": 1, "a": 1, "b": 1}, 2) == ["a", "b"]

def test_tk_raises_on_negative_k():
    with pytest.raises(ValueError):
        top_k_frequent({"a": 1}, -1)

def test_tk_raises_on_negative_count():
    with pytest.raises(ValueError):
        top_k_frequent({"a": -1}, 1)

def test_tk_raises_on_non_dict():
    with pytest.raises(TypeError):
        top_k_frequent([("a", 1)], 1)


# F4: compute_co_occurrence
def test_co_basic():
    """[['a','b']] → {('a','b'):1, ('b','a'):1}"""
    r = compute_co_occurrence([["a", "b"]])
    assert r == {("a", "b"): 1, ("b", "a"): 1}

def test_co_three_words():
    """[['a','b','c']] → 6 对各 1 (有序对)"""
    r = compute_co_occurrence([["a", "b", "c"]])
    expected = {
        ("a", "b"): 1, ("b", "a"): 1,
        ("a", "c"): 1, ("c", "a"): 1,
        ("b", "c"): 1, ("c", "b"): 1,
    }
    assert r == expected

def test_co_two_docs_accumulate():
    """[['a','b'], ['a','b']] → ('a','b'):2 ('b','a'):2"""
    r = compute_co_occurrence([["a", "b"], ["a", "b"]])
    assert r == {("a", "b"): 2, ("b", "a"): 2}

def test_co_repeated_word():
    """[['a','a','b']] → 不同位置算 (i!=j): (a,a) 来自 idx 0 与 1, 1 与 0 → 2 次. (a,b),(b,a)各 2 次 (a 出现 2 次)"""
    r = compute_co_occurrence([["a", "a", "b"]])
    expected = {
        ("a", "a"): 2,
        ("a", "b"): 2, ("b", "a"): 2,
    }
    assert r == expected

def test_co_single_word_doc():
    """[['a']] → {} (没有 i != j)"""
    r = compute_co_occurrence([["a"]])
    assert r == {}

def test_co_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_co_occurrence("not a list")
