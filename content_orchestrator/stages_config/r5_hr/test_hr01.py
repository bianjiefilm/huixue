import importlib
import os

import pytest

MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_hr01")
student = importlib.import_module(MODULE_NAME)

EMPLOYEES = [
    {"employee_id": "E1", "department": "Tech", "salary": 32000},
    {"employee_id": "E2", "department": "Tech", "salary": "28000"},
    {"employee_id": "E3", "department": "Sales", "salary": 16000},
    {"employee_id": "E4", "department": "Sales", "salary": 22000},
    {"employee_id": "E5", "department": "HR", "salary": 15000},
]


def _result():
    return student.analyze_salary_structure(EMPLOYEES)


def test_sorted_by_avg_salary():
    assert [row["department"] for row in _result()] == ["Tech", "Sales", "HR"]


def test_core_fields_present():
    assert set(_result()[0]) == {"department", "employee_count", "avg_salary", "median_salary", "pay_gap", "salary_band"}


def test_tech_salary_metrics():
    tech = _result()[0]
    assert tech["employee_count"] == 2
    assert tech["avg_salary"] == 30000.0
    assert tech["median_salary"] == 30000.0
    assert tech["pay_gap"] == 0.1333
    assert tech["salary_band"] == "high"


def test_sales_medium_band():
    sales = [row for row in _result() if row["department"] == "Sales"][0]
    assert sales["avg_salary"] == 19000.0
    assert sales["salary_band"] == "medium"


def test_hr_low_band_single_employee():
    hr = _result()[-1]
    assert hr["median_salary"] == 15000.0
    assert hr["pay_gap"] == 0.0


def test_rejects_non_list_input():
    with pytest.raises(ValueError):
        student.analyze_salary_structure({})


def test_ignores_bad_rows():
    result = student.analyze_salary_structure(["bad", {}, {"department": ""}, {"department": "X", "salary": 100}])
    assert result == [{"department": "X", "employee_count": 1, "avg_salary": 100.0, "median_salary": 100.0, "pay_gap": 0.0, "salary_band": "low"}]


def test_ignores_non_positive_salary():
    result = student.analyze_salary_structure([{"department": "X", "salary": 0}, {"department": "X", "salary": -1}])
    assert result == []


def test_even_median():
    result = student.analyze_salary_structure([{"department": "A", "salary": 10}, {"department": "A", "salary": 20}, {"department": "A", "salary": 30}, {"department": "A", "salary": 40}])[0]
    assert result["median_salary"] == 25.0


def test_tie_break_department_name():
    result = student.analyze_salary_structure([{"department": "B", "salary": 100}, {"department": "A", "salary": 100}])
    assert [row["department"] for row in result] == ["A", "B"]


def test_string_numbers():
    assert student.analyze_salary_structure([{"department": "A", "salary": "20000"}])[0]["salary_band"] == "medium"


def test_bool_salary_ignored():
    assert student.analyze_salary_structure([{"department": "A", "salary": True}]) == []


def test_empty_list():
    assert student.analyze_salary_structure([]) == []


def test_boundary_high_band():
    assert student.analyze_salary_structure([{"department": "A", "salary": 30000}])[0]["salary_band"] == "high"


def test_boundary_medium_band():
    assert student.analyze_salary_structure([{"department": "A", "salary": 18000}])[0]["salary_band"] == "medium"
