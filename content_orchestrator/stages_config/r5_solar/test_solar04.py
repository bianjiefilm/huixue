import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_solar04")
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


FEATURES = [
    {"station_id": "PV-01", "timestamp": "t1", "performance_ratio": 0.5, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3.0},
    {"station_id": "PV-01", "timestamp": "t2", "performance_ratio": 0.6, "cloud_risk": 0.3, "heat_stress": False, "expected_power_kw": 3.2},
    {"station_id": "PV-01", "timestamp": "t3", "performance_ratio": 0.7, "cloud_risk": 0.2, "heat_stress": True, "expected_power_kw": 3.1},
    {"station_id": "PV-02", "timestamp": "t1", "performance_ratio": 0.9, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 2.0},
    {"station_id": "PV-02", "timestamp": "t2", "performance_ratio": 0.95, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 2.1},
    {"station_id": "PV-03", "timestamp": "t1", "performance_ratio": 0.0, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 2.5},
    {"station_id": "PV-03", "timestamp": "t2", "performance_ratio": 0.0, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 2.6},
]
SPECS = [
    {"station_id": "PV-01", "site": "North", "capacity_kw": 8},
    {"station_id": "PV-02", "site": "North", "capacity_kw": 5},
    {"station_id": "PV-03", "site": "South", "capacity_kw": 10},
]


def test_prioritizes_offline_and_soiling_stations():
    result = student.recommend_solar_maintenance(FEATURES, SPECS, max_tasks=2)
    expected = [
        {"station_id": "PV-03", "site": "South", "avg_performance_ratio": 0.0, "low_performance_rate": 1.0, "heat_stress_rate": 0.0, "risk_score": 0.85, "severity": "critical", "priority_action": "inspect_inverter_and_grid_connection", "drivers": ["offline", "soiling"], "estimated_hours": 11.0, "priority_rank": 1},
        {"station_id": "PV-01", "site": "North", "avg_performance_ratio": 0.6, "low_performance_rate": 1.0, "heat_stress_rate": 0.3333, "risk_score": 0.525, "severity": "medium", "priority_action": "schedule_panel_cleaning", "drivers": ["soiling", "thermal"], "estimated_hours": 6.8, "priority_rank": 2},
    ]
    assert_close(result, expected)


def test_max_tasks_limits_output():
    assert len(student.recommend_solar_maintenance(FEATURES, SPECS, max_tasks=1)) == 1


def test_unknown_station_uses_unknown_site():
    features = [{"station_id": "PV-99", "performance_ratio": 0.4, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 3.0}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["site"] == "UNKNOWN"


def test_high_cloud_low_performance_is_unstable_not_soiling():
    features = [
        {"station_id": "PV-01", "performance_ratio": 0.5, "cloud_risk": 0.9, "heat_stress": False, "expected_power_kw": 3.0},
        {"station_id": "PV-01", "performance_ratio": 0.6, "cloud_risk": 0.8, "heat_stress": False, "expected_power_kw": 3.0},
    ]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["drivers"] == ["unstable"]
    assert result[0]["priority_action"] == "review_sensor_and_weather_alignment"


def test_thermal_only_action():
    features = [
        {"station_id": "PV-01", "performance_ratio": 0.9, "cloud_risk": 0.1, "heat_stress": True, "expected_power_kw": 3.0},
        {"station_id": "PV-01", "performance_ratio": 0.92, "cloud_risk": 0.1, "heat_stress": True, "expected_power_kw": 3.0},
    ]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["drivers"] == ["thermal"]
    assert result[0]["priority_action"] == "check_ventilation_and_module_hotspots"


def test_monitor_driver_for_mild_underperformance():
    features = [{"station_id": "PV-01", "performance_ratio": 0.8, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3.0}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["drivers"] == ["monitor"]
    assert result[0]["priority_action"] == "continue_monitoring"


def test_empty_features_returns_empty_list():
    assert student.recommend_solar_maintenance([]) == []


def test_skips_non_dict_rows_and_missing_station():
    result = student.recommend_solar_maintenance(["bad", {"timestamp": "x"}, FEATURES[0]])
    assert result[0]["station_id"] == "PV-01"


def test_station_features_must_be_list():
    with pytest.raises(ValueError):
        student.recommend_solar_maintenance({"station_id": "PV-01"})


def test_specs_must_be_list():
    with pytest.raises(ValueError):
        student.recommend_solar_maintenance([], {"PV-01": {}})


def test_max_tasks_must_be_positive_int():
    with pytest.raises(ValueError):
        student.recommend_solar_maintenance([], max_tasks=0)


def test_bool_max_tasks_rejected():
    with pytest.raises(ValueError):
        student.recommend_solar_maintenance([], max_tasks=True)


def test_numeric_strings_are_accepted():
    features = [{"station_id": "PV-01", "performance_ratio": "0.5", "cloud_risk": "0.2", "heat_stress": False, "expected_power_kw": "3.0"}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["avg_performance_ratio"] == 0.5


def test_boolean_performance_defaults_zero():
    features = [{"station_id": "PV-01", "performance_ratio": True, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 3.0}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["avg_performance_ratio"] == 0.0


def test_low_risk_station_severity_low():
    features = [{"station_id": "PV-01", "performance_ratio": 1.05, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 3.0}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["severity"] == "low"
    assert result[0]["drivers"] == []


def test_sort_tie_breaks_by_station_id():
    features = [{"station_id": "PV-B", "performance_ratio": 0.5, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 3}, {"station_id": "PV-A", "performance_ratio": 0.5, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 3}]
    result = student.recommend_solar_maintenance(features)
    assert [item["station_id"] for item in result[:2]] == ["PV-A", "PV-B"]


def test_high_severity_gets_extra_hours():
    features = [{"station_id": "PV-01", "performance_ratio": 0.2, "cloud_risk": 0.1, "heat_stress": True, "expected_power_kw": 4}]
    result = student.recommend_solar_maintenance(features, [{"station_id": "PV-01", "capacity_kw": 20}])
    assert result[0]["estimated_hours"] >= 8.0


def test_station_id_is_stripped_for_spec_matching():
    features = [{"station_id": " PV-09 ", "performance_ratio": 0.5, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3}]
    result = student.recommend_solar_maintenance(features, [{"station_id": "PV-09", "site": "West", "capacity_kw": 5}])
    assert result[0]["station_id"] == "PV-09"
    assert result[0]["site"] == "West"


def test_offline_driver_precedes_soiling_driver():
    features = [{"station_id": "PV-01", "performance_ratio": 0.0, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 2.0}]
    result = student.recommend_solar_maintenance(features)
    assert result[0]["drivers"][:2] == ["offline", "soiling"]


def test_multiple_clean_stations_keep_three_ranked_rows():
    features = [
        {"station_id": "PV-01", "performance_ratio": 0.75, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3},
        {"station_id": "PV-02", "performance_ratio": 0.65, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3},
        {"station_id": "PV-03", "performance_ratio": 0.55, "cloud_risk": 0.2, "heat_stress": False, "expected_power_kw": 3},
    ]
    result = student.recommend_solar_maintenance(features, max_tasks=3)
    assert len(result) == 3
    assert [item["priority_rank"] for item in result] == [1, 2, 3]
