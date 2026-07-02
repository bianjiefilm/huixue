import importlib
import os
import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_wind01")
student = importlib.import_module(MODULE_NAME)


def row(turbine_id, timestamp, wind_speed, rotor_speed, power, temp, vibration, status="ok"):
    return {
        "turbine_id": turbine_id,
        "timestamp": timestamp,
        "wind_speed": wind_speed,
        "rotor_speed": rotor_speed,
        "active_power_kw": power,
        "gearbox_temp_c": temp,
        "vibration_mms": vibration,
        "status": status,
    }


def cleaned(turbine_id, timestamp, wind_speed, rotor_speed, power, temp, vibration, status, label):
    return {
        "turbine_id": str(turbine_id),
        "timestamp": str(timestamp),
        "wind_speed": float(wind_speed),
        "rotor_speed": float(rotor_speed),
        "active_power_kw": float(power),
        "gearbox_temp_c": float(temp),
        "vibration_mms": float(vibration),
        "status": str(status).upper(),
        "anomaly_label": label,
    }


def assert_close(actual, expected, tolerance=1e-9):
    if isinstance(expected, float):
        assert isinstance(actual, (int, float))
        assert abs(actual - expected) < tolerance
        return
    if isinstance(expected, list):
        assert isinstance(actual, list)
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            assert_close(left, right, tolerance)
        return
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert set(actual.keys()) == set(expected.keys())
        for key in expected:
            assert_close(actual[key], expected[key], tolerance)
        return
    assert actual == expected


def test_normalizes_numeric_strings_and_status():
    rows = [row("WT-01", "2026-01-01T00:00:00Z", "7.5", "12", "540", "63.2", "2.1", "normal")]
    assert_close(student.clean_scada_readings(rows), [
        cleaned("WT-01", "2026-01-01T00:00:00Z", 7.5, 12, 540, 63.2, 2.1, "normal", "normal")
    ])


def test_sorts_by_turbine_and_timestamp():
    rows = [
        row("WT-02", "2026-01-01T00:10:00Z", 6, 10, 400, 60, 2, "ok"),
        row("WT-01", "2026-01-01T00:20:00Z", 8, 12, 610, 66, 3, "ok"),
        row("WT-01", "2026-01-01T00:05:00Z", 5, 9, 320, 55, 1.5, "ok"),
    ]
    assert_close(student.clean_scada_readings(rows), [
        cleaned("WT-01", "2026-01-01T00:05:00Z", 5, 9, 320, 55, 1.5, "ok", "normal"),
        cleaned("WT-01", "2026-01-01T00:20:00Z", 8, 12, 610, 66, 3, "ok", "normal"),
        cleaned("WT-02", "2026-01-01T00:10:00Z", 6, 10, 400, 60, 2, "ok", "normal"),
    ])


def test_drops_negative_wind_speed():
    rows = [row("WT-01", "t1", -1, 10, 100, 50, 1), row("WT-01", "t2", 3, 9, 90, 49, 1)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t2", 3, 9, 90, 49, 1, "ok", "normal")])


def test_drops_negative_power():
    rows = [row("WT-01", "t1", 4, 8, -10, 50, 1), row("WT-01", "t2", 4, 8, 120, 50, 1)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t2", 4, 8, 120, 50, 1, "ok", "normal")])


def test_drops_extreme_gearbox_temperature():
    rows = [row("WT-01", "t1", 4, 8, 120, 135, 1), row("WT-01", "t2", 4, 8, 120, 94.9, 1)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t2", 4, 8, 120, 94.9, 1, "ok", "normal")])


def test_flags_hot_gearbox():
    rows = [row("WT-01", "t1", 9, 14, 900, 96, 2)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t1", 9, 14, 900, 96, 2, "ok", "gearbox_hot")])


def test_flags_high_vibration():
    rows = [row("WT-01", "t1", 9, 14, 900, 70, 12.5)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t1", 9, 14, 900, 70, 12.5, "ok", "gearbox_hot")])


def test_drops_missing_required_field():
    rows = [row("WT-01", "t1", 5, 10, 120, 50, 1), {"turbine_id": "WT-02", "timestamp": "t2"}]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t1", 5, 10, 120, 50, 1, "ok", "normal")])


def test_skips_non_dict_rows():
    rows = ["bad", row("WT-01", "t1", 5, 10, 120, 50, 1), None]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t1", 5, 10, 120, 50, 1, "ok", "normal")])


def test_keeps_first_duplicate_key():
    rows = [
        row("WT-01", "t1", 5, 10, 120, 50, 1, "first"),
        row("WT-01", "t1", 9, 14, 900, 96, 12.5, "second"),
    ]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t1", 5, 10, 120, 50, 1, "first", "normal")])


def test_empty_input_returns_empty_list():
    assert_close(student.clean_scada_readings([]), [])


def test_raises_on_non_list_input():
    with pytest.raises(ValueError):
        student.clean_scada_readings({"turbine_id": "WT-01"})


def test_drops_non_numeric_values():
    rows = [row("WT-01", "t1", "bad", 10, 120, 50, 1), row("WT-01", "t2", 6, 11, 300, 52, 1.2)]
    assert_close(student.clean_scada_readings(rows), [cleaned("WT-01", "t2", 6, 11, 300, 52, 1.2, "ok", "normal")])
