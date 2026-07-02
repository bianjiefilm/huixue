import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK05_MODULE", "content_orchestrator.stages_config.spark.student_spark05"
)


def _student():
    return importlib.import_module(MODULE_NAME)


BASE_ROWS = [
    {"name": "Alice", "department": "HR", "salary": 5000},
    {"name": "Bob", "department": "IT", "salary": 8000},
    {"name": "Charlie", "department": "IT", "salary": 6000},
]


CASES = [
    (BASE_ROWS, "department_salary_sum_first", None, ["HR", 5000]),
    (BASE_ROWS, "uppercase_names", None, ["ALICE", "BOB", "CHARLIE"]),
    (BASE_ROWS, "order_by_salary_desc_names", None, ["Bob", "Charlie", "Alice"]),
    (BASE_ROWS, "filter_department_salary_count", ["IT", 6000], 1),
    ([{"name": "Ada", "department": "R&D", "salary": None}], "fill_missing_salary", None, [{"name": "Ada", "department": "R&D", "salary": 0}]),
    (BASE_ROWS, "avg_salary_by_department", "IT", 7000.0),
    (BASE_ROWS, "select_names_by_department", "IT", ["Bob", "Charlie"]),
    (BASE_ROWS, "top_salary", None, 8000),
    ([{"name": "A", "salary": None}, {"name": "B", "salary": 2}], "count_null_salary", None, 1),
    ([{"name": "A", "salary": None}, {"name": "B", "salary": 2}], "project_name_salary", None, [{"name": "A", "salary": 0}, {"name": "B", "salary": 2}]),
    ([], "top_salary", None, 0),
    (BASE_ROWS, "avg_salary_by_department", "Legal", 0),
    (BASE_ROWS, "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("rows,operation,param,expected", CASES)
def test_run_sql_query(rows, operation, param, expected):
    assert _student().run_sql_query(rows, operation, param) == expected


def test_rejects_non_list_rows():
    with pytest.raises(TypeError):
        _student().run_sql_query({"name": "Alice"}, "top_salary")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_sql_query([], None)
