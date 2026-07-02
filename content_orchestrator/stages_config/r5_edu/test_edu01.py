import importlib
import os
import pytest

student = importlib.import_module(os.environ.get("STUDENT_MODULE", "student_edu01"))

RECORDS = [
    {"student_id": "S1", "total_tasks": 10, "completed_tasks": 10, "avg_score": 92, "learning_minutes": 120},
    {"student_id": "S2", "total_tasks": 10, "completed_tasks": 5, "avg_score": 58, "learning_minutes": 20},
    {"student_id": "S3", "total_tasks": 8, "completed_tasks": 6, "avg_score": "78", "learning_minutes": 45},
    {"student_id": "S4", "total_tasks": 0, "completed_tasks": 0, "avg_score": 99},
]

def test_summary_keys_and_counts():
    res = student.summarize_learning_progress(RECORDS)
    assert set(res) == {"student_count", "avg_completion", "avg_score", "active_students", "at_risk_students", "top_students"}
    assert res["student_count"] == 3
    assert res["active_students"] == 2

def test_average_metrics():
    res = student.summarize_learning_progress(RECORDS)
    assert abs(res["avg_completion"] - 0.75) < 0.0001
    assert abs(res["avg_score"] - 76.0) < 0.001

def test_at_risk_and_top_students():
    res = student.summarize_learning_progress(RECORDS)
    assert res["at_risk_students"] == ["S2"]
    assert res["top_students"] == ["S1", "S3", "S2"]

def test_caps_completion_at_total():
    res = student.summarize_learning_progress([{"student_id": "S1", "total_tasks": 4, "completed_tasks": 9, "avg_score": 70, "learning_minutes": 30}])
    assert res["avg_completion"] == 1.0

def test_empty_list():
    assert student.summarize_learning_progress([])["student_count"] == 0

def test_rejects_non_list():
    with pytest.raises(ValueError):
        student.summarize_learning_progress({})

def test_ignores_bad_rows():
    res = student.summarize_learning_progress(["bad", {}, {"student_id": "S", "total_tasks": 3, "completed_tasks": 2, "avg_score": 66}])
    assert res["student_count"] == 1

def test_negative_minutes_not_active():
    res = student.summarize_learning_progress([{"student_id": "S", "total_tasks": 1, "completed_tasks": 1, "avg_score": 80, "learning_minutes": -3}])
    assert res["active_students"] == 0

def test_tie_break_top_student_id():
    res = student.summarize_learning_progress([{"student_id": "B", "total_tasks": 1, "completed_tasks": 1, "avg_score": 90}, {"student_id": "A", "total_tasks": 1, "completed_tasks": 1, "avg_score": 90}])
    assert res["top_students"] == ["A", "B"]

def test_score_risk_even_when_completion_high():
    res = student.summarize_learning_progress([{"student_id": "S", "total_tasks": 5, "completed_tasks": 5, "avg_score": 59}])
    assert res["at_risk_students"] == ["S"]

def test_completion_risk_even_when_score_high():
    res = student.summarize_learning_progress([{"student_id": "S", "total_tasks": 10, "completed_tasks": 3, "avg_score": 90}])
    assert res["at_risk_students"] == ["S"]

def test_bool_score_ignored():
    assert student.summarize_learning_progress([{"student_id": "S", "total_tasks": 1, "completed_tasks": 1, "avg_score": True}])["student_count"] == 0
