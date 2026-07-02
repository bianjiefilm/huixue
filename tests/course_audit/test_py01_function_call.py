import importlib
import pytest


CASES = [
    (3, 5, 8),
    (10, 20, 30),
    (0, 0, 0),
    (-3, 7, 4),
    (7, 11, 18),
    (100, 50, 150),
    (999, 1, 1000),
    (-2, -3, -5),
    (1.5, 2.25, 3.75),
    (0, -8, -8),
]


def _student():
    return importlib.import_module("student_py01")


@pytest.mark.parametrize(("a", "b", "expected"), CASES)
def test_add_numbers(a, b, expected):
    assert _student().add_numbers(a, b) == expected


def test_add_numbers_rejects_non_numeric():
    with pytest.raises(TypeError):
        _student().add_numbers("3", 5)


def test_add_numbers_rejects_bool():
    with pytest.raises(TypeError):
        _student().add_numbers(True, 5)
