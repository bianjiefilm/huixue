import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("SPARK02_MODULE", "content_orchestrator.stages_config.spark.student_spark02"))


CASES = [
    (["a", "a", "b", "b", "c"], "word_count", 0, {"a": 2, "b": 2, "c": 1}),
    ([1, 2, 3, 4], "filter_gt", 2, [3, 4]),
    (["hello", "hello", "spark"], "flat_chars", 0, list("hellohellospark")),
    ([1, 2, 3, 4], "collect_even_times10", 0, [20, 40]),
    (["a", "b", "a", "c", "a", "b"], "group_count", 0, {"a": 3, "b": 2, "c": 1}),
    ([3, 1, 3, 2, 1], "distinct", 0, [3, 1, 2]),
    ([], "word_count", 0, {}),
    ([-2, -1, 0, 1], "filter_gt", -1, [0, 1]),
    ([""], "flat_chars", 0, []),
    ([2, 4, 6], "collect_even_times10", 0, [20, 40, 60]),
    ([1, 2, 3], "unknown", 0, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize(("data", "operation", "threshold", "expected"), CASES)
def test_run_rdd_operation(data, operation, threshold, expected):
    assert _student().run_rdd_operation(data, operation, threshold) == expected


def test_rejects_non_list_data():
    with pytest.raises(TypeError):
        _student().run_rdd_operation("a,b,c", "word_count")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_rdd_operation([], None)
