import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK08_MODULE", "content_orchestrator.stages_config.spark.student_spark08"
)


def _student():
    return importlib.import_module(MODULE_NAME)


EVENTS = [
    {"id": 1, "key": "a", "value": 10, "minute": 1},
    {"id": 2, "key": "a", "value": 20, "minute": 12},
    {"id": 3, "key": "b", "value": 30, "minute": 15},
]


CASES = [
    (EVENTS, "is_streaming", None, True),
    (EVENTS, "watermark_count_by_key", 10, {"a": 1, "b": 1}),
    (EVENTS, "start_query", {"format": "parquet", "mode": "append"}, {"format": "parquet", "mode": "append", "started": True}),
    (EVENTS, "trigger_interval", 5, "ProcessingTime(5 seconds)"),
    (EVENTS, "await_status", True, "TERMINATED"),
    (EVENTS, "left_outer_join_streaming", [{"id": 1}, {"id": 9}], [{"id": 1, "matched": True}, {"id": 9, "matched": False}]),
    (EVENTS, "query_status_message", None, "ACTIVE"),
    (EVENTS, "output_mode", "complete", "complete mode set"),
    (EVENTS, "kafka_source", "orders", {"source": "kafka", "topic": "orders", "loaded": True}),
    (EVENTS, "checkpoint_enabled", "/tmp/ckpt", True),
    (EVENTS, "stop_is_active", None, False),
    (EVENTS, "append_recent_values", 10, [20, 30]),
    (EVENTS, "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("events,operation,param,expected", CASES)
def test_run_structured_streaming_operation(events, operation, param, expected):
    assert _student().run_structured_streaming_operation(events, operation, param) == expected


def test_rejects_non_list_events():
    with pytest.raises(TypeError):
        _student().run_structured_streaming_operation("events", "is_streaming")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_structured_streaming_operation([], None)
