import importlib

import pytest


CASES = [
    ("hello", {"h": 1, "e": 1, "l": 2, "o": 1}),
    ("Python", {"p": 1, "y": 1, "t": 1, "h": 1, "o": 1, "n": 1}),
    ("a", {"a": 1}),
    ("AbCdEf", {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1, "f": 1}),
    ("zzz AAA", {"z": 3, "a": 3}),
    ("Hello, Tempo 2026!", {"h": 1, "e": 2, "l": 2, "o": 2, "t": 1, "m": 1, "p": 1}),
    ("Data-Driven AI", {"d": 2, "a": 3, "t": 1, "r": 1, "i": 2, "v": 1, "e": 1, "n": 1}),
    ("", {}),
    ("123 !!!", {}),
    ("Mississippi", {"m": 1, "i": 4, "s": 4, "p": 2}),
    ("banana bread", {"b": 2, "a": 4, "n": 2, "r": 1, "e": 1, "d": 1}),
    ("Code Review", {"c": 1, "o": 1, "d": 1, "e": 3, "r": 1, "v": 1, "i": 1, "w": 1}),
]


def _student():
    return importlib.import_module("student_py04")


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_count_letters(text, expected):
    assert _student().count_letters(text) == expected


def test_count_letters_rejects_non_string():
    with pytest.raises(TypeError):
        _student().count_letters(["hello"])


def test_count_letters_rejects_none():
    with pytest.raises(TypeError):
        _student().count_letters(None)
