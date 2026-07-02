import importlib
import os

import pytest


CASES = [
    (32, 0.0),
    (212, 100.0),
    (98.6, 37.0),
    (0, -17.77777777777778),
    (-40, -40.0),
    (50, 10.0),
    (68, 20.0),
    (77, 25.0),
    (104, 40.0),
    (14, -10.0),
    (451, 232.77777777777777),
    (15.8, -9.0),
]


def _student():
    return importlib.import_module(os.environ.get("PY08_MODULE", "student_py08"))


@pytest.mark.parametrize(("fahrenheit", "expected"), CASES)
def test_fahrenheit_to_celsius(fahrenheit, expected):
    assert abs(_student().fahrenheit_to_celsius(fahrenheit) - expected) < 1e-9


def test_fahrenheit_to_celsius_rejects_string():
    with pytest.raises(TypeError):
        _student().fahrenheit_to_celsius("32")


def test_fahrenheit_to_celsius_rejects_none():
    with pytest.raises(TypeError):
        _student().fahrenheit_to_celsius(None)


def test_fahrenheit_to_celsius_rejects_bool():
    with pytest.raises(TypeError):
        _student().fahrenheit_to_celsius(True)
