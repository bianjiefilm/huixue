import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_solar02")
student = importlib.import_module(MODULE_NAME)


def assert_close(actual, expected, tol=1e-9):
    assert type(actual) is type(expected), f"type mismatch: {type(actual)} != {type(expected)}"
    if isinstance(expected, float):
        assert abs(actual - expected) < tol
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected):
            assert_close(a, e, tol)
    elif isinstance(expected, dict):
        assert set(actual.keys()) == set(expected.keys())
        for key in expected:
            assert_close(actual[key], expected[key], tol)
    else:
        assert actual == expected


ROWS = [
    {"station_id": "PV-02", "timestamp": "t2", "irradiance_wm2": 500, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 80, "power_kw": 1.0},
    {"station_id": "PV-01", "timestamp": "t1", "irradiance_wm2": 800, "module_temp_c": 45, "ambient_temp_c": 30, "humidity_pct": 50, "power_kw": 3.2},
]
SPECS = [
    {"station_id": "PV-01", "capacity_kw": 5, "panel_area_m2": 25, "efficiency": 0.2},
    {"station_id": "PV-02", "capacity_kw": 3, "panel_area_m2": 20, "efficiency": 0.18},
]


def test_builds_features_with_specs_and_sorts():
    result = student.build_weather_features(ROWS, SPECS)
    expected = [
        {"station_id": "PV-01", "timestamp": "t1", "irradiance_kwm2": 0.8, "temp_delta_c": 15.0, "humidity_band": "normal", "expected_power_kw": 4.0, "performance_ratio": 0.8, "heat_stress": False, "cloud_risk": 0.2},
        {"station_id": "PV-02", "timestamp": "t2", "irradiance_kwm2": 0.5, "temp_delta_c": 10.0, "humidity_band": "humid", "expected_power_kw": 1.8, "performance_ratio": 0.5556, "heat_stress": False, "cloud_risk": 0.8},
    ]
    assert_close(result, expected)


def test_uses_default_specs_when_missing():
    result = student.build_weather_features([ROWS[0]])
    assert result[0]["expected_power_kw"] == 2.25


def test_caps_expected_power_by_capacity():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 1200, "module_temp_c": 42, "ambient_temp_c": 28, "humidity_pct": 40, "power_kw": 4.5}]
    result = student.build_weather_features(rows, [{"station_id": "PV-01", "capacity_kw": 4, "panel_area_m2": 50, "efficiency": 0.2}])
    assert result[0]["expected_power_kw"] == 4.0
    assert result[0]["performance_ratio"] == 1.125


def test_heat_stress_by_module_temperature():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 700, "module_temp_c": 56, "ambient_temp_c": 35, "humidity_pct": 40, "power_kw": 3}]
    assert student.build_weather_features(rows)[0]["heat_stress"] is True


def test_heat_stress_by_temperature_delta():
    rows = [{"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 700, "module_temp_c": 50, "ambient_temp_c": 24, "humidity_pct": 40, "power_kw": 3}]
    assert student.build_weather_features(rows)[0]["heat_stress"] is True


def test_humidity_band_dry():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 20, "humidity_pct": 20, "power_kw": 1}
    assert student.build_weather_features([row])[0]["humidity_band"] == "dry"


def test_humidity_band_normal_upper_edge():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 20, "humidity_pct": 70, "power_kw": 1}
    assert student.build_weather_features([row])[0]["humidity_band"] == "normal"


def test_humidity_band_humid():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 20, "humidity_pct": 71, "power_kw": 1}
    assert student.build_weather_features([row])[0]["humidity_band"] == "humid"


def test_zero_irradiance_has_zero_expected_and_ratio():
    row = {"station_id": "PV-01", "timestamp": "night", "irradiance_wm2": 0, "module_temp_c": 18, "ambient_temp_c": 15, "humidity_pct": 55, "power_kw": 0}
    result = student.build_weather_features([row])
    assert result[0]["expected_power_kw"] == 0.0
    assert result[0]["performance_ratio"] == 0.0


def test_numeric_strings_are_accepted():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": "600", "module_temp_c": "40", "ambient_temp_c": "25", "humidity_pct": "45", "power_kw": "2.1"}
    result = student.build_weather_features([row])
    assert result[0]["irradiance_kwm2"] == 0.6


def test_invalid_numeric_defaults_to_zero():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": "bad", "module_temp_c": 40, "ambient_temp_c": 25, "humidity_pct": 45, "power_kw": 2.1}
    result = student.build_weather_features([row])
    assert result[0]["expected_power_kw"] == 0.0


def test_skips_non_dict_rows():
    assert student.build_weather_features(["bad", ROWS[0]])[0]["station_id"] == "PV-02"


def test_skips_missing_station_or_timestamp():
    assert student.build_weather_features([{"station_id": "PV-01"}, {"timestamp": "x"}]) == []


def test_empty_rows_returns_empty_list():
    assert student.build_weather_features([]) == []


def test_rows_must_be_list():
    with pytest.raises(ValueError):
        student.build_weather_features({"station_id": "PV-01"})


def test_specs_must_be_list_when_provided():
    with pytest.raises(ValueError):
        student.build_weather_features([], {"PV-01": {}})


def test_efficiency_is_clamped_low():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 40, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 1}
    result = student.build_weather_features([row], [{"station_id": "PV-01", "panel_area_m2": 10, "capacity_kw": 10, "efficiency": 0.01}])
    assert result[0]["expected_power_kw"] == 0.5


def test_efficiency_is_clamped_high():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 40, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 4}
    result = student.build_weather_features([row], [{"station_id": "PV-01", "panel_area_m2": 10, "capacity_kw": 10, "efficiency": 0.5}])
    assert result[0]["expected_power_kw"] == 3.0


def test_cloud_risk_is_clamped_to_zero():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 1400, "module_temp_c": 40, "ambient_temp_c": 25, "humidity_pct": 0, "power_kw": 4}
    assert student.build_weather_features([row])[0]["cloud_risk"] == 0.0


def test_cloud_risk_is_clamped_to_one():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 0, "module_temp_c": 20, "ambient_temp_c": 15, "humidity_pct": 100, "power_kw": 0}
    assert student.build_weather_features([row])[0]["cloud_risk"] == 1.0


def test_station_text_is_stripped_for_spec_matching():
    row = {"station_id": " PV-09 ", "timestamp": " t ", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 20, "humidity_pct": 50, "power_kw": 1}
    result = student.build_weather_features([row], [{"station_id": "PV-09", "capacity_kw": 2, "panel_area_m2": 20, "efficiency": 0.2}])
    assert result[0]["station_id"] == "PV-09"
    assert result[0]["timestamp"] == "t"


def test_performance_ratio_above_one_is_preserved():
    row = {"station_id": "PV-01", "timestamp": "x", "irradiance_wm2": 500, "module_temp_c": 30, "ambient_temp_c": 20, "humidity_pct": 50, "power_kw": 3}
    assert student.build_weather_features([row])[0]["performance_ratio"] == 1.3333


def test_multiple_rows_keep_independent_feature_values():
    rows = [
        {"station_id": "PV-01", "timestamp": "a", "irradiance_wm2": 100, "module_temp_c": 25, "ambient_temp_c": 20, "humidity_pct": 30, "power_kw": 0.3},
        {"station_id": "PV-01", "timestamp": "b", "irradiance_wm2": 900, "module_temp_c": 58, "ambient_temp_c": 31, "humidity_pct": 75, "power_kw": 1.0},
    ]
    result = student.build_weather_features(rows)
    assert result[0]["humidity_band"] == "dry"
    assert result[1]["heat_stress"] is True


def test_expected_power_uses_station_specific_specs():
    rows = [
        {"station_id": "PV-A", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 1},
        {"station_id": "PV-B", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 1},
    ]
    specs = [
        {"station_id": "PV-A", "capacity_kw": 3, "panel_area_m2": 10, "efficiency": 0.2},
        {"station_id": "PV-B", "capacity_kw": 3, "panel_area_m2": 20, "efficiency": 0.2},
    ]
    result = student.build_weather_features(rows, specs)
    assert [item["expected_power_kw"] for item in result] == [2.0, 3.0]


def test_missing_station_spec_uses_default_without_affecting_known_station():
    rows = [
        {"station_id": "PV-A", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 1},
        {"station_id": "PV-Z", "timestamp": "x", "irradiance_wm2": 1000, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 1},
    ]
    specs = [{"station_id": "PV-A", "capacity_kw": 2, "panel_area_m2": 10, "efficiency": 0.2}]
    result = student.build_weather_features(rows, specs)
    assert [item["expected_power_kw"] for item in result] == [2.0, 4.5]
