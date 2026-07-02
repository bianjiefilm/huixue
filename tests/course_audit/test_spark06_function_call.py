import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK06_MODULE", "content_orchestrator.stages_config.spark.student_spark06"
)


def _student():
    return importlib.import_module(MODULE_NAME)


ROWS = [
    {"id": 1, "date": "2023-01-01", "text": "spark sql", "name": "a,b", "score": 90, "category": "A", "amount": 10, "profile": {"city": "BJ"}},
    {"id": 2, "date": "2023-05-02", "text": "spark ml", "name": "c,d,e", "score": 95, "category": "B", "amount": 7, "profile": {"city": "SH"}},
    {"id": 3, "date": "2024-03-03", "text": "data", "name": "f", "score": 80, "category": "A", "amount": 5, "profile": {"city": "GZ"}},
]


CASES = [
    (ROWS, "broadcast_join_count", [{"id": 1}, {"id": 3}, {"id": 9}], 2),
    (ROWS, "count_by_year_first", None, ["2023", 2]),
    ([{"text": "spark sql"}], "regexp_replace_first", ["spark", "SPARK"], "SPARK sql"),
    (ROWS, "explode_name_count", ",", 6),
    (ROWS, "partition_write_summary", None, ["2023", "2024"]),
    (ROWS, "window_rank", None, [{"name": "c,d,e", "rank": 1}, {"name": "a,b", "rank": 2}, {"name": "f", "rank": 3}]),
    (ROWS, "drop_duplicates_count", "category", 2),
    (ROWS, "pivot_sum", None, {"A": 15, "B": 7}),
    (ROWS, "nested_field_select", "city", ["BJ", "SH", "GZ"]),
    ([{"id": None}, {"id": 4}, {"id": 5}], "null_safe_join_count", [{"id": None}, {"id": 5}], 1),
    ([], "count_by_year_first", None, []),
    ([{"text": "no match"}], "regexp_replace_first", ["spark", "SPARK"], "no match"),
    (ROWS, "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("rows,operation,extra,expected", CASES)
def test_run_dataframe_operation(rows, operation, extra, expected):
    assert _student().run_dataframe_operation(rows, operation, extra) == expected


def test_rejects_non_list_rows():
    with pytest.raises(TypeError):
        _student().run_dataframe_operation({"id": 1}, "broadcast_join_count", [])


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_dataframe_operation([], None)
