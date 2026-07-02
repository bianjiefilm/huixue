import importlib
import os

import pytest

MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_hr03")
student = importlib.import_module(MODULE_NAME)

EMPLOYEES = [
    {"employee_id": "E1", "tenure_months": 4, "salary_market_ratio": 0.82, "overtime_hours": 50, "months_since_promotion": 6},
    {"employee_id": "E2", "tenure_months": 36, "salary_market_ratio": 1.05, "overtime_hours": 20, "months_since_promotion": 30},
    {"employee_id": "E3", "tenure_months": 18, "salary_market_ratio": 0.95, "overtime_hours": 10, "months_since_promotion": 10},
]
ENGAGEMENT = [
    {"employee_id": "E1", "engagement_score": 52, "manager_score": 70},
    {"employee_id": "E2", "engagement_score": 78, "manager_score": 55},
    {"employee_id": "E3", "engagement_score": 90, "manager_score": 90},
]


def _result():
    return student.predict_attrition_risk(EMPLOYEES, ENGAGEMENT)


def test_sorted_by_risk():
    assert [row["employee_id"] for row in _result()] == ["E1", "E2", "E3"]


def test_e1_critical_drivers():
    e1 = _result()[0]
    assert e1["attrition_score"] == 0.94
    assert e1["risk_level"] == "critical"
    assert e1["retention_action"] == "executive_retention_plan"
    assert e1["drivers"] == ["below_market_pay", "high_overtime", "low_engagement", "new_hire"]


def test_e2_medium_manager_action():
    e2 = _result()[1]
    assert e2["risk_level"] == "medium"
    assert e2["retention_action"] == "manager_intervention"


def test_e3_low_observe():
    assert _result()[2] == {"employee_id": "E3", "attrition_score": 0.12, "risk_level": "low", "drivers": [], "retention_action": "observe"}


def test_rejects_bad_employee_input():
    with pytest.raises(ValueError):
        student.predict_attrition_risk({})


def test_rejects_bad_engagement_input():
    with pytest.raises(ValueError):
        student.predict_attrition_risk([], {})


def test_ignores_bad_rows():
    result = student.predict_attrition_risk(["bad", {}, {"employee_id": ""}, EMPLOYEES[2]], ENGAGEMENT)
    assert len(result) == 1
    assert result[0]["employee_id"] == "E3"


def test_deduplicates_employees():
    result = student.predict_attrition_risk([EMPLOYEES[0], dict(EMPLOYEES[0], overtime_hours=0)], ENGAGEMENT)
    assert len(result) == 1
    assert result[0]["attrition_score"] == 0.94


def test_no_engagement_defaults_low():
    result = student.predict_attrition_risk([EMPLOYEES[2]])[0]
    assert result["risk_level"] == "low"


def test_salary_review_action_when_high_pay_risk():
    row = {"employee_id": "X", "tenure_months": 12, "salary_market_ratio": 0.7, "overtime_hours": 0, "months_since_promotion": 0}
    assert student.predict_attrition_risk([row])[0]["retention_action"] == "compensation_review"


def test_career_action_when_promotion_gap():
    row = {"employee_id": "X", "tenure_months": 12, "salary_market_ratio": 1.0, "overtime_hours": 0, "months_since_promotion": 30}
    assert student.predict_attrition_risk([row])[0]["retention_action"] == "career_conversation"


def test_score_cap():
    row = {"employee_id": "X", "tenure_months": 1, "salary_market_ratio": 0.1, "overtime_hours": 99, "months_since_promotion": 99}
    assert student.predict_attrition_risk([row], [{"employee_id": "X", "engagement_score": 0, "manager_score": 0}])[0]["attrition_score"] == 1.0


def test_string_numbers():
    row = {"employee_id": "X", "tenure_months": "4", "salary_market_ratio": "0.82", "overtime_hours": "50", "months_since_promotion": "6"}
    assert student.predict_attrition_risk([row])[0]["risk_level"] == "high"


def test_bool_values_ignored():
    row = {"employee_id": "X", "tenure_months": True, "salary_market_ratio": True, "overtime_hours": True, "months_since_promotion": True}
    assert student.predict_attrition_risk([row])[0]["risk_level"] == "low"


def test_empty_input():
    assert student.predict_attrition_risk([], []) == []
