import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fin04")
student = importlib.import_module(MODULE_NAME)


PROJECTS = [
    {"project_id": "P2", "initial_investment": 800, "cash_flows": [260, 260, 260, 260]},
    {"project_id": "P1", "initial_investment": "1000", "cash_flows": [400, 420, 430]},
    {"project_id": "P3", "initial_investment": 500, "cash_flows": [80, 90, 100]},
]


def _result():
    return student.evaluate_investment_returns(PROJECTS, 0.1)


def test_sorted_by_npv_descending():
    assert [row["project_id"] for row in _result()] == ["P1", "P2", "P3"]


def test_p1_roi_payback_npv_priority():
    p1 = _result()[0]
    assert p1["roi"] == 0.25
    assert p1["payback_period"] == 2.42
    assert abs(p1["npv"] - 33.81) < 0.01
    assert p1["priority"] == "invest"


def test_p2_watch_due_long_payback():
    p2 = [row for row in _result() if row["project_id"] == "P2"][0]
    assert p2["roi"] == 0.3
    assert p2["payback_period"] == 3.08
    assert p2["priority"] == "watch"


def test_p3_defer_negative_npv():
    p3 = _result()[-1]
    assert p3["roi"] == -0.46
    assert p3["payback_period"] is None
    assert p3["priority"] == "defer"


def test_zero_initial_investment():
    row = student.evaluate_investment_returns([{"project_id": "Z", "initial_investment": 0, "cash_flows": [10]}])[0]
    assert row["roi"] is None
    assert row["payback_period"] == 0.0


def test_rejects_non_list_projects():
    with pytest.raises(ValueError):
        student.evaluate_investment_returns({})


def test_rejects_invalid_discount_rate():
    with pytest.raises(ValueError):
        student.evaluate_investment_returns([], -1)


def test_ignores_bad_rows():
    result = student.evaluate_investment_returns(["bad", {}, {"project_id": ""}, PROJECTS[0]])
    assert len(result) == 1
    assert result[0]["project_id"] == "P2"


def test_deduplicates_projects():
    result = student.evaluate_investment_returns([PROJECTS[0], dict(PROJECTS[0], initial_investment=1)])
    assert len(result) == 1
    assert result[0]["roi"] == 0.3


def test_non_list_cash_flows_treated_empty():
    result = student.evaluate_investment_returns([{"project_id": "X", "initial_investment": 100, "cash_flows": {}}])[0]
    assert result["roi"] == -1.0
    assert result["payback_period"] is None


def test_negative_initial_uses_absolute_value():
    result = student.evaluate_investment_returns([{"project_id": "X", "initial_investment": -100, "cash_flows": [150]}], 0)[0]
    assert result["roi"] == 0.5
    assert result["payback_period"] == 0.67


def test_string_flows_are_accepted():
    result = student.evaluate_investment_returns([{"project_id": "X", "initial_investment": "100", "cash_flows": ["50", "60"]}], 0)[0]
    assert result["roi"] == 0.1
    assert result["npv"] == 10.0


def test_bool_flow_is_ignored():
    result = student.evaluate_investment_returns([{"project_id": "X", "initial_investment": 100, "cash_flows": [True, 100]}], 0)[0]
    assert result["roi"] == 0.0


def test_empty_input_returns_empty_list():
    assert student.evaluate_investment_returns([]) == []


def test_tie_breaks_by_project_id():
    rows = [{"project_id": "B", "initial_investment": 0, "cash_flows": []}, {"project_id": "A", "initial_investment": 0, "cash_flows": []}]
    assert [row["project_id"] for row in student.evaluate_investment_returns(rows)] == ["A", "B"]
