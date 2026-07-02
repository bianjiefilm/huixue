import importlib
import pytest


CASES = [
    (5, 15),
    (10, 55),
    (1, 1),
    (100, 5050),
    (7, 28),
    (20, 210),
    (50, 1275),
    (4, 10),
    (2, 3),
    (99, 4950),
]


def _student():
    return importlib.import_module("student_py02")


@pytest.mark.parametrize(("n", "expected"), CASES)
def test_sum_to_n(n, expected):
    assert _student().sum_to_n(n) == expected


def test_sum_to_n_rejects_zero():
    with pytest.raises(ValueError):
        _student().sum_to_n(0)


def test_sum_to_n_rejects_non_integer():
    with pytest.raises(TypeError):
        _student().sum_to_n("5")


def test_sum_to_n_rejects_bool():
    with pytest.raises(TypeError):
        _student().sum_to_n(True)
