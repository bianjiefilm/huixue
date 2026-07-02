import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK04_MODULE", "content_orchestrator.stages_config.spark.student_spark04"
)


def _student():
    return importlib.import_module(MODULE_NAME)


CASES = [
    ([1, 2, 3], "broadcast_add_first", [1, 2, 3], 7),
    ([1, 2, 3, 4], "accumulator_sum", None, 10.0),
    (["a", "b"], "broadcast_lookup_first", {"a": 1, "b": 2}, ["a", 1]),
    ([1, 2, 3, 4], "accumulator_filter_sum_gt", 2, 7),
    ([1, 2, 3, 4, 5], "broadcast_set_count", [1, 3, 5], 3),
    ([1, 2, 3, 4], "accumulator_double_sum", None, 20),
    ([1, 2, 3, 4], "broadcast_add_sum", 100, 410),
    ([1, 2, 3, 4], "accumulator_count_lt", 3, 2),
    ([1, 2, 3, 4, 5], "accumulator_half_sum", None, 7.5),
    (["b", "c"], "broadcast_lookup_first", {"b": 2}, ["b", 2]),
    ([9], "broadcast_add_first", [10, 20], 39),
    ([3, 6, 9], "accumulator_filter_sum_gt", 20, 0),
    ([1, 2, 3], "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("data,operation,shared,expected", CASES)
def test_run_shared_variable_operation(data, operation, shared, expected):
    assert _student().run_shared_variable_operation(data, operation, shared) == expected


def test_rejects_non_list_data():
    with pytest.raises(TypeError):
        _student().run_shared_variable_operation("1,2,3", "accumulator_sum")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_shared_variable_operation([], None)
