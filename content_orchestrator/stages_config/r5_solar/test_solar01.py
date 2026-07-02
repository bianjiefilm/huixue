import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_solar01")
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


BASE_ROWS = [
    {"station_id": "PV-02", "timestamp": "2026-07-01T10:15:00Z", "irradiance_wm2": "760", "module_temp_c": "45.2", "ambient_temp_c": "31", "humidity_pct": "55", "power_kw": "2.9"},
    {"station_id": "PV-01", "timestamp": "2026-07-01T10:00:00Z", "irradiance_wm2": 820, "module_temp_c": 43.1234, "ambient_temp_c": 29, "humidity_pct": 48, "power_kw": 3.6},
    {"station_id": "PV-01", "timestamp": "2026-07-01T09:45:00Z", "irradiance_wm2": 650, "module_temp_c": 39, "ambient_temp_c": 28, "humidity_pct": 52, "power_kw": 2.7},
]


def test_normalizes_numeric_strings_and_sorts_rows():
    result = student.clean_solar_readings(BASE_ROWS)
    expected = [
        {"station_id": "PV-01", "timestamp": "2026-07-01T09:45:00Z", "irradiance_wm2": 650.0, "module_temp_c": 39.0, "ambient_temp_c": 28.0, "humidity_pct": 52.0, "power_kw": 2.7, "quality_label": "normal"},
        {"station_id": "PV-01", "timestamp": "2026-07-01T10:00:00Z", "irradiance_wm2": 820.0, "module_temp_c": 43.123, "ambient_temp_c": 29.0, "humidity_pct": 48.0, "power_kw": 3.6, "quality_label": "normal"},
        {"station_id": "PV-02", "timestamp": "2026-07-01T10:15:00Z", "irradiance_wm2": 760.0, "module_temp_c": 45.2, "ambient_temp_c": 31.0, "humidity_pct": 55.0, "power_kw": 2.9, "quality_label": "normal"},
    ]
    assert_close(result, expected)


def test_drops_negative_irradiance():
    rows = BASE_ROWS + [{"station_id": "PV-03", "timestamp": "bad", "irradiance_wm2": -1, "module_temp_c": 30, "ambient_temp_c": 25, "humidity_pct": 40, "power_kw": 1}]
    assert len(student.clean_solar_readings(rows)) == 3


def test_drops_negative_power():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 25, "humidity_pct": 40, "power_kw": -0.1}]
    assert student.clean_solar_readings(rows) == []


def test_drops_extreme_module_temperature():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": 500, "module_temp_c": 120, "ambient_temp_c": 25, "humidity_pct": 40, "power_kw": 1}]
    assert student.clean_solar_readings(rows) == []


def test_drops_invalid_humidity():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": 500, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 120, "power_kw": 1}]
    assert student.clean_solar_readings(rows) == []


def test_drops_missing_required_fields():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 500, "module_temp_c": 35}]
    assert student.clean_solar_readings(rows) == []


def test_drops_non_numeric_values():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": "bad", "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 40, "power_kw": 1}]
    assert student.clean_solar_readings(rows) == []


def test_deduplicates_station_timestamp_keep_first():
    rows = BASE_ROWS + [{"station_id": "PV-01", "timestamp": "2026-07-01T09:45:00Z", "irradiance_wm2": 999, "module_temp_c": 50, "ambient_temp_c": 30, "humidity_pct": 40, "power_kw": 9}]
    result = student.clean_solar_readings(rows)
    assert result[0]["irradiance_wm2"] == 650.0


def test_marks_underperforming_when_power_too_low_for_sun():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 40, "power_kw": 1.0}]
    assert student.clean_solar_readings(rows)[0]["quality_label"] == "underperforming"


def test_marks_night_anomaly_when_power_high_without_sun():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 20, "module_temp_c": 18, "ambient_temp_c": 15, "humidity_pct": 60, "power_kw": 25}]
    assert student.clean_solar_readings(rows)[0]["quality_label"] == "night_anomaly"


def test_empty_rows_return_empty_list():
    assert student.clean_solar_readings([]) == []


def test_non_dict_rows_are_ignored():
    rows = ["bad", None, BASE_ROWS[0]]
    assert len(student.clean_solar_readings(rows)) == 1


def test_rows_must_be_list():
    with pytest.raises(ValueError):
        student.clean_solar_readings({"station_id": "PV-01"})


def test_boundary_zero_irradiance_zero_power_is_valid():
    rows = [{"station_id": "PV-01", "timestamp": "night", "irradiance_wm2": 0, "module_temp_c": 16, "ambient_temp_c": 12, "humidity_pct": 80, "power_kw": 0}]
    assert student.clean_solar_readings(rows)[0]["quality_label"] == "normal"


def test_boundary_max_reasonable_irradiance_is_valid():
    rows = [{"station_id": "PV-01", "timestamp": "noon", "irradiance_wm2": 1400, "module_temp_c": 60, "ambient_temp_c": 35, "humidity_pct": 20, "power_kw": 5.8}]
    assert student.clean_solar_readings(rows)[0]["irradiance_wm2"] == 1400.0


def test_drops_irradiance_above_physical_limit():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": 1400.1, "module_temp_c": 60, "ambient_temp_c": 35, "humidity_pct": 20, "power_kw": 5.8}]
    assert student.clean_solar_readings(rows) == []


def test_drops_low_ambient_temperature_outlier():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": 400, "module_temp_c": 20, "ambient_temp_c": -50, "humidity_pct": 40, "power_kw": 1.0}]
    assert student.clean_solar_readings(rows) == []


def test_strips_station_and_timestamp_text():
    rows = [{"station_id": " PV-09 ", "timestamp": " t1 ", "irradiance_wm2": 300, "module_temp_c": 22, "ambient_temp_c": 19, "humidity_pct": 30, "power_kw": 1.4}]
    result = student.clean_solar_readings(rows)
    assert result[0]["station_id"] == "PV-09"
    assert result[0]["timestamp"] == "t1"


def test_blank_station_is_dropped():
    rows = [{"station_id": "  ", "timestamp": "t1", "irradiance_wm2": 300, "module_temp_c": 22, "ambient_temp_c": 19, "humidity_pct": 30, "power_kw": 1.4}]
    assert student.clean_solar_readings(rows) == []


def test_boolean_numeric_values_are_rejected():
    rows = [{"station_id": "PV-01", "timestamp": "bad", "irradiance_wm2": True, "module_temp_c": 22, "ambient_temp_c": 19, "humidity_pct": 30, "power_kw": 1.4}]
    assert student.clean_solar_readings(rows) == []
