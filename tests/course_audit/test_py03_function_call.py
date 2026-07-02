import importlib
import pytest


CASES = [
    (5, 120),
    (3, 6),
    (0, 1),
    (10, 3628800),
    (7, 5040),
    (12, 479001600),
    (1, 1),
    (8, 40320),
    (2, 2),
]


def _student():
    return importlib.import_module("student_py03")


@pytest.mark.parametrize(("n", "expected"), CASES)
def test_factorial(n, expected):
    assert _student().factorial(n) == expected


def test_factorial_rejects_negative():
    with pytest.raises(ValueError):
        _student().factorial(-5)


def test_factorial_rejects_string():
    with pytest.raises(TypeError):
        _student().factorial("5")


def test_factorial_rejects_bool():
    with pytest.raises(TypeError):
        _student().factorial(False)


def test_factorial_rejects_float():
    with pytest.raises(TypeError):
        _student().factorial(3.5)
