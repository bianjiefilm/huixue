import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK07_MODULE", "content_orchestrator.stages_config.spark.student_spark07"
)


def _student():
    return importlib.import_module(MODULE_NAME)


CASES = [
    ([[1], [2]], "init_status", True, "stream processing initiated"),
    ([["a", "b"], ["c"], ["d", "e", "f"]], "window_count", 2, 4),
    ([["u1", "u2"], ["u1"], ["u3", "u2"]], "stateful_count_by_key", None, {"u1": 2, "u2": 2, "u3": 1}),
    ([["a", ""], ["b", ""], ["c"]], "transform_non_empty_count", None, 3),
    ([["a"], ["b"]], "checkpoint_status", "hdfs://path", {"checkpoint": True, "batches": 2}),
    ([["a", "b"], [], ["c"]], "foreach_batch_sizes", None, [2, 0, 1]),
    ([[1], [2], [3]], "batch_count", None, 3),
    ([[1, 2], [3, 4, 5]], "latest_batch_count", None, 3),
    ([["a"], ["b", "c"]], "flat_events", None, ["a", "b", "c"]),
    ([["error:1", "ok"], ["error:2"]], "filter_keyword_count", "error", 2),
    ([[1, 2], [3], [4]], "running_total", None, [3, 6, 10]),
    ([], "latest_batch_count", None, 0),
    ([["a"]], "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("batches,operation,param,expected", CASES)
def test_run_streaming_operation(batches, operation, param, expected):
    assert _student().run_streaming_operation(batches, operation, param) == expected


def test_rejects_non_list_batches():
    with pytest.raises(TypeError):
        _student().run_streaming_operation("a,b", "batch_count")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_streaming_operation([], None)
