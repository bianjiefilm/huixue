import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_wind04")
student = importlib.import_module(MODULE_NAME)


def assert_close(actual, expected, tol=1e-9):
    assert type(actual) is type(expected), f"type mismatch: {type(actual)} != {type(expected)}"
    if isinstance(expected, float):
        assert abs(actual - expected) < tol, f"{actual} != {expected}"
    elif isinstance(expected, list):
        assert len(actual) == len(expected), f"length mismatch: {len(actual)} != {len(expected)}"
        for left, right in zip(actual, expected):
            assert_close(left, right, tol)
    elif isinstance(expected, dict):
        assert set(actual.keys()) == set(expected.keys())
        for key in expected:
            assert_close(actual[key], expected[key], tol)
    else:
        assert actual == expected


SPECS = [
    {"turbine_id": "WT-01", "site": "North", "gearbox_model": "GX"},
    {"turbine_id": "WT-02", "site": "North", "gearbox_model": "G2"},
    {"turbine_id": "WT-03", "site": "South", "gearbox_model": "AX"},
]


def test_basic_severity_priority_and_capacity():
    alerts = [
        {"turbine_id": "WT-02", "severity": "medium", "risk_score": 0.7, "detected_at": "t2", "reason": "vibration"},
        {"turbine_id": "WT-01", "severity": "critical", "risk_score": 0.8, "detected_at": "t1", "reason": "temperature"},
        {"turbine_id": "WT-03", "severity": "high", "risk_score": 0.9, "detected_at": "t3", "reason": "oil"},
    ]
    result = student.plan_maintenance(alerts, SPECS, max_daily_tasks=2)
    expected = [
        {"turbine_id": "WT-01", "severity": "critical", "risk_score": 0.8, "priority_rank": 1, "scheduled_day": 1, "site": "North", "gearbox_model": "GX", "action": "immediate_shutdown_inspection", "estimated_hours": 10.0, "reasons": ["temperature"]},
        {"turbine_id": "WT-03", "severity": "high", "risk_score": 0.9, "priority_rank": 2, "scheduled_day": 1, "site": "South", "gearbox_model": "AX", "action": "priority_field_inspection", "estimated_hours": 7.5, "reasons": ["oil"]},
        {"turbine_id": "WT-02", "severity": "medium", "risk_score": 0.7, "priority_rank": 3, "scheduled_day": 2, "site": "North", "gearbox_model": "G2", "action": "scheduled_condition_check", "estimated_hours": 4.0, "reasons": ["vibration"]},
    ]
    assert_close(result, expected)


def test_duplicate_alerts_merge_reasons_and_keep_highest_severity():
    alerts = [
        {"turbine_id": "WT-01", "severity": "medium", "risk_score": 0.6, "detected_at": "t1", "reason": "temp"},
        {"turbine_id": "WT-01", "severity": "high", "risk_score": 0.7, "detected_at": "t2", "reason": "vibration"},
    ]
    result = student.plan_maintenance(alerts, SPECS)
    assert result[0]["severity"] == "high"
    assert result[0]["risk_score"] == 0.7
    assert result[0]["reasons"] == ["temp", "vibration"]


def test_equal_severity_sorts_by_risk_then_time_then_turbine():
    alerts = [
        {"turbine_id": "WT-03", "severity": "high", "risk_score": 0.8, "detected_at": "t2", "reason": "a"},
        {"turbine_id": "WT-02", "severity": "high", "risk_score": 0.9, "detected_at": "t3", "reason": "b"},
        {"turbine_id": "WT-01", "severity": "high", "risk_score": 0.8, "detected_at": "t1", "reason": "c"},
    ]
    result = student.plan_maintenance(alerts, SPECS, max_daily_tasks=1)
    assert [item["turbine_id"] for item in result] == ["WT-02", "WT-01", "WT-03"]
    assert [item["scheduled_day"] for item in result] == [1, 2, 3]


def test_unknown_turbine_uses_unknown_metadata():
    alerts = [{"turbine_id": "WT-99", "severity": "low", "risk_score": 0.2, "reason": "manual"}]
    result = student.plan_maintenance(alerts, SPECS)
    assert result[0]["site"] == "UNKNOWN"
    assert result[0]["gearbox_model"] == "UNKNOWN"
    assert result[0]["estimated_hours"] == 2.0


def test_empty_alerts_returns_empty_list():
    assert student.plan_maintenance([], SPECS) == []


def test_skips_invalid_alert_rows():
    alerts = ["bad", {"turbine_id": "WT-01"}, {"severity": "high"}, {"turbine_id": "WT-02", "severity": "low", "risk_score": 0.1}]
    result = student.plan_maintenance(alerts, SPECS)
    assert len(result) == 1
    assert result[0]["turbine_id"] == "WT-02"


def test_risk_score_is_clamped_and_rounded():
    alerts = [
        {"turbine_id": "WT-01", "severity": "low", "risk_score": 1.23456},
        {"turbine_id": "WT-02", "severity": "low", "risk_score": -0.5},
    ]
    result = student.plan_maintenance(alerts, SPECS)
    assert result[0]["risk_score"] == 1.0
    assert result[1]["risk_score"] == 0.0


def test_non_list_inputs_raise_value_error():
    with pytest.raises(ValueError):
        student.plan_maintenance({"turbine_id": "WT-01"}, SPECS)


def test_specs_must_be_list():
    with pytest.raises(ValueError):
        student.plan_maintenance([], {"WT-01": {}})


def test_bad_capacity_raises_value_error():
    with pytest.raises(ValueError):
        student.plan_maintenance([], SPECS, max_daily_tasks=0)


def test_unknown_severity_raises_value_error():
    with pytest.raises(ValueError):
        student.plan_maintenance([{"turbine_id": "WT-01", "severity": "urgent"}], SPECS)


def test_case_insensitive_severity_and_numeric_strings():
    alerts = [{"turbine_id": "WT-01", "severity": " HIGH ", "risk_score": "0.87654", "reason": "bearing"}]
    result = student.plan_maintenance(alerts, SPECS)
    assert result[0]["severity"] == "high"
    assert result[0]["risk_score"] == 0.8765


def test_capacity_three_keeps_first_three_on_day_one():
    alerts = [
        {"turbine_id": "WT-01", "severity": "critical", "risk_score": 0.9},
        {"turbine_id": "WT-02", "severity": "high", "risk_score": 0.8},
        {"turbine_id": "WT-03", "severity": "medium", "risk_score": 0.7},
        {"turbine_id": "WT-04", "severity": "low", "risk_score": 0.6},
    ]
    result = student.plan_maintenance(alerts, SPECS, max_daily_tasks=3)
    assert [item["scheduled_day"] for item in result] == [1, 1, 1, 2]
