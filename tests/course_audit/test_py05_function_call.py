import importlib
import os

import pytest


CASES = [
    ([1, 2, 3, 4, 5, 6], [2, 4, 6]),
    ([7, 8, 9, 10], [8, 10]),
    ([2, 5, 7], [2]),
    ([2, 4, 6, 8], [2, 4, 6, 8]),
    ([5, 6, 7], [6]),
    ([1, 2, 3, 4, 5], [2, 4]),
    ([3, 5, 7, 9, 11], []),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [2, 4, 6, 8, 10]),
    ([11, 12, 13, 14, 15], [12, 14]),
    ([21, 22, 23, 24], [22, 24]),
    ([0, -2, -1, 3, 4], [0, -2, 4]),
    ([], []),
]


def _student():
    return importlib.import_module(os.environ.get("PY05_MODULE", "student_py05"))


@pytest.mark.parametrize(("numbers", "expected"), CASES)
def test_filter_even_numbers(numbers, expected):
    assert _student().filter_even_numbers(numbers) == expected


def test_filter_even_numbers_rejects_string():
    with pytest.raises(TypeError):
        _student().filter_even_numbers("1 2 3")


def test_filter_even_numbers_rejects_float_item():
    with pytest.raises(TypeError):
        _student().filter_even_numbers([1, 2.5, 4])


def test_filter_even_numbers_rejects_bool_item():
    with pytest.raises(TypeError):
        _student().filter_even_numbers([True, 2, 4])
