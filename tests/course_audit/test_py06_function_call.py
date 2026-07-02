import importlib
import os

import pytest


CASES = [
    ("hello world hello", {"hello": 2, "world": 1}),
    ("apple banana apple", {"apple": 2, "banana": 1}),
    ("a", {"a": 1}),
    ("dog cat bird dog cat", {"bird": 1, "cat": 2, "dog": 2}),
    ("x x x y z", {"x": 3, "y": 1, "z": 1}),
    ("one two three one two", {"one": 2, "three": 1, "two": 2}),
    ("tempo talents tempo", {"talents": 1, "tempo": 2}),
    ("data ai data bi ai", {"ai": 2, "bi": 1, "data": 2}),
    ("", {}),
    ("   ", {}),
    ("Python python Python", {"Python": 2, "python": 1}),
    ("red blue green blue red red", {"blue": 2, "green": 1, "red": 3}),
    ("v2 fc v2 pytest fc", {"fc": 2, "pytest": 1, "v2": 2}),
]


def _student():
    return importlib.import_module(os.environ.get("PY06_MODULE", "student_py06"))


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_count_words(text, expected):
    assert _student().count_words(text) == expected


def test_count_words_rejects_list():
    with pytest.raises(TypeError):
        _student().count_words(["hello", "world"])


def test_count_words_rejects_none():
    with pytest.raises(TypeError):
        _student().count_words(None)
