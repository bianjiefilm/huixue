import importlib
import os

import pytest


CASES = [
    ({"a": 1, "b": 2}, {"a": 10, "c": 3}, {"a": 10, "b": 2, "c": 3}),
    ({"x": 5, "y": 3}, {"x": 1, "z": 9}, {"x": 1, "y": 3, "z": 9}),
    ({"p": 1}, {}, {"p": 1}),
    ({"p": 1, "q": 2}, {"x": 5}, {"p": 1, "q": 2, "x": 5}),
    ({"k": 99, "v": 88}, {"k": 1}, {"k": 1, "v": 88}),
    ({"m": 3, "n": 5}, {"o": 7}, {"m": 3, "n": 5, "o": 7}),
    ({}, {"a": 1}, {"a": 1}),
    ({}, {}, {}),
    ({"b": 2, "a": 1}, {"c": 3}, {"a": 1, "b": 2, "c": 3}),
    ({"score": 80}, {"score": 95}, {"score": 95}),
    ({"neg": -1, "zero": 0}, {"pos": 1}, {"neg": -1, "pos": 1, "zero": 0}),
    ({"aa": 1}, {"a": 2, "aaa": 3}, {"a": 2, "aa": 1, "aaa": 3}),
]


def _student():
    return importlib.import_module(os.environ.get("PY07_MODULE", "student_py07"))


@pytest.mark.parametrize(("base", "updates", "expected"), CASES)
def test_merge_records(base, updates, expected):
    assert _student().merge_records(base, updates) == expected


def test_merge_records_rejects_non_dict_base():
    with pytest.raises(TypeError):
        _student().merge_records([("a", 1)], {"b": 2})


def test_merge_records_rejects_non_string_key():
    with pytest.raises(TypeError):
        _student().merge_records({1: 2}, {"b": 3})


def test_merge_records_rejects_non_int_value():
    with pytest.raises(TypeError):
        _student().merge_records({"a": "1"}, {"b": 2})
