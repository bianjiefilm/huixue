import importlib
import os

import pytest

MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_hr04")
student = importlib.import_module(MODULE_NAME)

REVIEWS = [
    {"employee_id": "E2", "goal_score": 88, "competency_score": 82, "values_score": 90, "peer_score": 80},
    {"employee_id": "E1", "goal_score": 96, "competency_score": 94, "values_score": 92, "peer_score": 90},
    {"employee_id": "E3", "goal_score": 62, "competency_score": 70, "values_score": 80, "peer_score": 65},
    {"employee_id": "E4", "goal_score": 40, "competency_score": 55, "values_score": 60, "peer_score": 50},
]


def _result():
    return student.evaluate_performance_reviews(REVIEWS)


def test_sorted_by_score():
    assert [row["employee_id"] for row in _result()] == ["E1", "E2", "E3", "E4"]


def test_fields_present():
    assert set(_result()[0]) == {"employee_id", "performance_score", "rating", "bonus_multiplier", "development_focus"}


def test_a_rating_bonus():
    e1 = _result()[0]
    assert e1["performance_score"] == 94.0
    assert e1["rating"] == "A"
    assert e1["bonus_multiplier"] == 1.5
    assert e1["development_focus"] == []


def test_b_rating():
    e2 = _result()[1]
    assert e2["rating"] == "B"
    assert e2["bonus_multiplier"] == 1.1


def test_c_rating_focus():
    e3 = _result()[2]
    assert e3["rating"] == "C"
    assert e3["development_focus"] == ["collaboration", "goal_execution", "skill_growth"]


def test_d_rating_zero_bonus():
    e4 = _result()[3]
    assert e4["rating"] == "D"
    assert e4["bonus_multiplier"] == 0.0


def test_rejects_non_list_input():
    with pytest.raises(ValueError):
        student.evaluate_performance_reviews({})


def test_ignores_bad_rows():
    result = student.evaluate_performance_reviews(["bad", {}, {"employee_id": ""}, REVIEWS[0]])
    assert len(result) == 1
    assert result[0]["employee_id"] == "E2"


def test_deduplicates_employee():
    result = student.evaluate_performance_reviews([REVIEWS[0], dict(REVIEWS[0], goal_score=0)])
    assert len(result) == 1
    assert result[0]["rating"] == "B"


def test_string_numbers():
    row = {"employee_id": "X", "goal_score": "90", "competency_score": "90", "values_score": "90", "peer_score": "90"}
    assert student.evaluate_performance_reviews([row])[0]["rating"] == "A"


def test_missing_scores_default_zero():
    row = {"employee_id": "X"}
    result = student.evaluate_performance_reviews([row])[0]
    assert result["performance_score"] == 0.0
    assert result["rating"] == "D"


def test_bool_scores_ignored():
    row = {"employee_id": "X", "goal_score": True, "competency_score": True, "values_score": True, "peer_score": True}
    assert student.evaluate_performance_reviews([row])[0]["performance_score"] == 0.0


def test_boundary_b_rating():
    row = {"employee_id": "X", "goal_score": 75, "competency_score": 75, "values_score": 75, "peer_score": 75}
    assert student.evaluate_performance_reviews([row])[0]["rating"] == "B"


def test_boundary_c_rating():
    row = {"employee_id": "X", "goal_score": 60, "competency_score": 60, "values_score": 60, "peer_score": 60}
    assert student.evaluate_performance_reviews([row])[0]["rating"] == "C"


def test_empty_input():
    assert student.evaluate_performance_reviews([]) == []
