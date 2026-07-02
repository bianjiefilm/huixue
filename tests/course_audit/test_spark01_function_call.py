import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("SPARK01_MODULE", "content_orchestrator.stages_config.spark.student_spark01"))


CASES = [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 55),
    ([2, 5, 3], 10),
    (list(range(1, 101)), 5050),
    ([], 0),
    (list(range(-5, 6)), 0),
    ([1, 2, 3, 4, 5], 15),
    ([10, 20, 30], 60),
    ([7], 7),
    (list(range(1, 51)), 1275),
    ([100], 100),
    ([1, 1, 1, 1], 4),
    ([1.5, 2.5, -1.0], 3.0),
]


@pytest.mark.parametrize(("values", "expected"), CASES)
def test_parallelize_sum(values, expected):
    assert _student().parallelize_sum(values) == expected


def test_rejects_none_values():
    with pytest.raises(TypeError):
        _student().parallelize_sum(None)


def test_rejects_string_values():
    with pytest.raises(TypeError):
        _student().parallelize_sum("123")


def test_rejects_non_numeric_member():
    with pytest.raises(TypeError):
        _student().parallelize_sum([1, "2", 3])
