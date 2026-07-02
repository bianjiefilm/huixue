import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_wind02")
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


def test_single_row_low_risk():
    rows = [{
        "turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 65,
        "ambient_temp_c": 25, "vibration_mms": 2, "active_power_kw": 500,
        "status": "normal",
    }]
    expected = [{
        "turbine_id": "WT-01", "timestamp": "t1", "temp_avg": 65.0,
        "temp_max": 65.0, "vibration_avg": 2.0, "vibration_max": 2.0,
        "power_avg": 500.0, "temp_delta": 40.0, "anomaly_count": 0,
        "hot_gearbox": False, "high_vibration": False, "risk_level": "low",
    }]
    assert_close(student.build_fault_features(rows), expected)


def test_two_row_window_high_risk():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 60, "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 400, "status": "normal"},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 78, "ambient_temp_c": 22, "vibration_mms": 5.5, "active_power_kw": 650, "status": "warning"},
    ]
    expected = [
        {"turbine_id": "WT-01", "timestamp": "t1", "temp_avg": 60.0, "temp_max": 60.0, "vibration_avg": 2.0, "vibration_max": 2.0, "power_avg": 400.0, "temp_delta": 40.0, "anomaly_count": 0, "hot_gearbox": False, "high_vibration": False, "risk_level": "low"},
        {"turbine_id": "WT-01", "timestamp": "t2", "temp_avg": 69.0, "temp_max": 78.0, "vibration_avg": 3.75, "vibration_max": 5.5, "power_avg": 525.0, "temp_delta": 56.0, "anomaly_count": 1, "hot_gearbox": True, "high_vibration": True, "risk_level": "high"},
    ]
    assert_close(student.build_fault_features(rows, window_size=2), expected)


def test_sorting_keeps_turbine_windows_separate():
    rows = [
        {"turbine_id": "WT-02", "timestamp": "t2", "gearbox_temp_c": 80, "ambient_temp_c": 30, "vibration_mms": 2, "active_power_kw": 300, "status": "normal"},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 72, "ambient_temp_c": 24, "vibration_mms": 3, "active_power_kw": 610, "status": "normal"},
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 68, "ambient_temp_c": 23, "vibration_mms": 2, "active_power_kw": 590, "status": "normal"},
    ]
    expected = [
        {"turbine_id": "WT-01", "timestamp": "t1", "temp_avg": 68.0, "temp_max": 68.0, "vibration_avg": 2.0, "vibration_max": 2.0, "power_avg": 590.0, "temp_delta": 45.0, "anomaly_count": 0, "hot_gearbox": False, "high_vibration": False, "risk_level": "low"},
        {"turbine_id": "WT-01", "timestamp": "t2", "temp_avg": 70.0, "temp_max": 72.0, "vibration_avg": 2.5, "vibration_max": 3.0, "power_avg": 600.0, "temp_delta": 48.0, "anomaly_count": 0, "hot_gearbox": False, "high_vibration": False, "risk_level": "low"},
        {"turbine_id": "WT-02", "timestamp": "t2", "temp_avg": 80.0, "temp_max": 80.0, "vibration_avg": 2.0, "vibration_max": 2.0, "power_avg": 300.0, "temp_delta": 50.0, "anomaly_count": 0, "hot_gearbox": True, "high_vibration": False, "risk_level": "medium"},
    ]
    assert_close(student.build_fault_features(rows, window_size=3), expected)


def test_window_size_one_uses_current_row_only():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 50, "ambient_temp_c": 20, "vibration_mms": 1, "active_power_kw": 100, "status": "normal"},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 90, "ambient_temp_c": 30, "vibration_mms": 6, "active_power_kw": 200, "status": "normal"},
    ]
    result = student.build_fault_features(rows, window_size=1)
    assert result[1]["temp_avg"] == 90.0
    assert result[1]["vibration_avg"] == 6.0
    assert result[1]["power_avg"] == 200.0
    assert result[1]["risk_level"] == "high"


def test_anomaly_count_can_raise_risk_without_hot_current_row():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 60, "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 100, "status": "alert"},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 62, "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 120, "anomaly_label": "fault"},
        {"turbine_id": "WT-01", "timestamp": "t3", "gearbox_temp_c": 63, "ambient_temp_c": 21, "vibration_mms": 2.5, "active_power_kw": 130, "status": "normal"},
    ]
    result = student.build_fault_features(rows, window_size=3)
    assert result[2]["anomaly_count"] == 2
    assert result[2]["risk_level"] == "high"


def test_empty_input_returns_empty_list():
    assert student.build_fault_features([]) == []


def test_non_list_rows_raises_value_error():
    with pytest.raises(ValueError):
        student.build_fault_features({"turbine_id": "WT-01"})


def test_invalid_window_size_raises_value_error():
    with pytest.raises(ValueError):
        student.build_fault_features([], window_size=0)


def test_skips_rows_with_missing_required_fields():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 60, "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 100},
        {"turbine_id": "WT-02", "timestamp": "t2", "gearbox_temp_c": 70},
    ]
    assert len(student.build_fault_features(rows)) == 1


def test_skips_rows_with_non_numeric_values():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": "bad", "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 100},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 70, "ambient_temp_c": 22, "vibration_mms": 3, "active_power_kw": 300},
    ]
    result = student.build_fault_features(rows)
    assert len(result) == 1
    assert result[0]["timestamp"] == "t2"


def test_thresholds_are_inclusive():
    rows = [{"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 75, "ambient_temp_c": 25, "vibration_mms": 5, "active_power_kw": 400}]
    result = student.build_fault_features(rows)
    assert result[0]["hot_gearbox"] is True
    assert result[0]["high_vibration"] is True
    assert result[0]["risk_level"] == "high"


def test_rounds_rolling_values_to_three_decimals():
    rows = [
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 61, "ambient_temp_c": 20, "vibration_mms": 1, "active_power_kw": 101},
        {"turbine_id": "WT-01", "timestamp": "t2", "gearbox_temp_c": 62, "ambient_temp_c": 20, "vibration_mms": 2, "active_power_kw": 102},
        {"turbine_id": "WT-01", "timestamp": "t3", "gearbox_temp_c": 64, "ambient_temp_c": 21, "vibration_mms": 4, "active_power_kw": 104},
    ]
    result = student.build_fault_features(rows, window_size=3)
    assert result[2]["temp_avg"] == 62.333
    assert result[2]["vibration_avg"] == 2.333
    assert result[2]["power_avg"] == 102.333


def test_multiple_turbines_with_same_timestamp_are_stable():
    rows = [
        {"turbine_id": "WT-02", "timestamp": "t1", "gearbox_temp_c": 70, "ambient_temp_c": 20, "vibration_mms": 4.9, "active_power_kw": 300},
        {"turbine_id": "WT-01", "timestamp": "t1", "gearbox_temp_c": 74, "ambient_temp_c": 24, "vibration_mms": 5.1, "active_power_kw": 500},
    ]
    result = student.build_fault_features(rows)
    assert [item["turbine_id"] for item in result] == ["WT-01", "WT-02"]
    assert result[0]["risk_level"] == "medium"
