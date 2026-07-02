import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_solar05")
student = importlib.import_module(MODULE_NAME)


RAW_ROWS = [
    {"station_id": "PV-02", "timestamp": "t1", "irradiance_wm2": "500", "module_temp_c": "42", "ambient_temp_c": "27", "humidity_pct": "70", "power_kw": "2.2"},
    {"station_id": "PV-01", "timestamp": "t1", "irradiance_wm2": 800, "module_temp_c": 48, "ambient_temp_c": 29, "humidity_pct": 45, "power_kw": 5.6},
    {"station_id": "PV-01", "timestamp": "t2", "irradiance_wm2": 850, "module_temp_c": 66, "ambient_temp_c": 31, "humidity_pct": 40, "power_kw": 4.4},
    {"station_id": "PV-03", "timestamp": "t1", "irradiance_wm2": 700, "module_temp_c": 43, "ambient_temp_c": 28, "humidity_pct": 42, "power_kw": 0.0},
]

SPECS = [
    {"station_id": "PV-01", "site": "North", "capacity_kw": 8},
    {"station_id": "PV-02", "site": "North", "capacity_kw": 5},
    {"station_id": "PV-03", "site": "South", "capacity_kw": 6},
]


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


def _features():
    return student.build_weather_features(student.load_and_clean_solar(RAW_ROWS), SPECS)


def _predictions():
    return [
        {"station_id": "PV-01", "timestamp": "t1", "predicted_power_kw": 5.4},
        {"station_id": "PV-01", "timestamp": "t2", "predicted_power_kw": 5.6},
        {"station_id": "PV-02", "timestamp": "t1", "predicted_power_kw": 2.0},
        {"station_id": "PV-03", "timestamp": "t1", "predicted_power_kw": 1.8},
    ]


def test_01_clean_sorts_and_normalizes_numeric_fields():
    result = student.load_and_clean_solar(RAW_ROWS)
    assert [row["station_id"] for row in result] == ["PV-01", "PV-01", "PV-02", "PV-03"]
    assert result[0]["irradiance_wm2"] == 800.0
    assert set(result[0]) == {"station_id", "timestamp", "irradiance_wm2", "module_temp_c", "ambient_temp_c", "humidity_pct", "power_kw"}


def test_02_clean_filters_invalid_physical_ranges():
    rows = RAW_ROWS + [
        {"station_id": "PV-X", "timestamp": "bad1", "irradiance_wm2": -1, "module_temp_c": 20, "ambient_temp_c": 20, "humidity_pct": 40, "power_kw": 1},
        {"station_id": "PV-X", "timestamp": "bad2", "irradiance_wm2": 500, "module_temp_c": 120, "ambient_temp_c": 20, "humidity_pct": 40, "power_kw": 1},
        {"station_id": "PV-X", "timestamp": "bad3", "irradiance_wm2": 500, "module_temp_c": 20, "ambient_temp_c": 20, "humidity_pct": 140, "power_kw": 1},
    ]
    assert len(student.load_and_clean_solar(rows)) == 4


def test_03_clean_deduplicates_station_timestamp_first_row():
    rows = RAW_ROWS + [{"station_id": "PV-01", "timestamp": "t1", "irradiance_wm2": 999, "module_temp_c": 50, "ambient_temp_c": 30, "humidity_pct": 40, "power_kw": 9.9}]
    result = student.load_and_clean_solar(rows)
    assert result[0]["power_kw"] == 5.6


def test_04_clean_skips_missing_and_non_numeric_rows():
    rows = [{"station_id": "PV-01", "timestamp": "x"}, {"station_id": "PV-01", "timestamp": "y", "irradiance_wm2": "bad", "module_temp_c": 20, "ambient_temp_c": 20, "humidity_pct": 50, "power_kw": 1}]
    assert student.load_and_clean_solar(rows) == []


def test_05_clean_requires_list():
    with pytest.raises(ValueError):
        student.load_and_clean_solar({"station_id": "PV-01"})


def test_06_features_computes_expected_power_and_ratio():
    result = _features()
    assert result[0]["station_id"] == "PV-01"
    assert result[0]["expected_power_kw"] == 5.8112
    assert result[0]["performance_ratio"] == 0.9637
    assert result[0]["cloud_risk"] == 0.0


def test_07_features_detects_heat_stress():
    result = _features()
    pv01_t2 = [row for row in result if row["station_id"] == "PV-01" and row["timestamp"] == "t2"][0]
    assert pv01_t2["heat_stress"] is True
    assert pv01_t2["temperature_delta"] == 35.0


def test_08_features_default_capacity_for_unknown_station():
    readings = student.load_and_clean_solar([{"station_id": "PV-99", "timestamp": "t", "irradiance_wm2": 500, "module_temp_c": 35, "ambient_temp_c": 25, "humidity_pct": 50, "power_kw": 4}])
    result = student.build_weather_features(readings)
    assert result[0]["expected_power_kw"] == 4.8


def test_09_features_empty_input():
    assert student.build_weather_features([], SPECS) == []


def test_10_features_requires_list_and_specs_list():
    with pytest.raises(ValueError):
        student.build_weather_features("bad")
    with pytest.raises(ValueError):
        student.build_weather_features([], {"PV-01": {}})


def test_11_score_prediction_metrics_and_alerts():
    result = student.score_output_prediction(_features(), _predictions(), alert_threshold=0.15)
    assert result["total"] == 4
    assert result["mae"] == 0.85
    assert result["rmse"] == 1.0909
    assert result["r2"] == 0.7406
    assert result["alert_count"] == 2
    assert result["worst_station"] == "PV-03"


def test_12_score_prediction_alert_detail_fields():
    alerts = student.score_output_prediction(_features(), _predictions(), alert_threshold=0.15)["alerts"]
    assert alerts == [
        {"station_id": "PV-01", "timestamp": "t2", "actual_power_kw": 4.4, "predicted_power_kw": 5.6, "relative_error": 0.2111},
        {"station_id": "PV-03", "timestamp": "t1", "actual_power_kw": 0.0, "predicted_power_kw": 1.8, "relative_error": 0.4618},
    ]


def test_13_score_prediction_handles_empty_matches():
    assert student.score_output_prediction([], []) == {"total": 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0, "alert_count": 0, "worst_station": None, "alerts": []}


def test_14_score_prediction_requires_lists_and_positive_threshold():
    with pytest.raises(ValueError):
        student.score_output_prediction({}, [])
    with pytest.raises(ValueError):
        student.score_output_prediction([], [], alert_threshold=0)


def test_15_score_prediction_ignores_unmatched_predictions():
    result = student.score_output_prediction(_features(), [{"station_id": "PV-X", "timestamp": "z", "predicted_power_kw": 99}])
    assert result["total"] == 0


def test_16_maintenance_prioritizes_offline_prediction_alerts():
    summary = student.score_output_prediction(_features(), _predictions(), alert_threshold=0.15)
    plans = student.generate_maintenance_recommendation(_features(), summary, SPECS, max_tasks=3)
    assert [plan["station_id"] for plan in plans] == ["PV-03", "PV-01", "PV-02"]
    assert plans[0]["drivers"] == ["offline", "soiling", "prediction_alert"]
    assert plans[0]["severity"] == "critical"


def test_17_maintenance_output_exact_keys():
    plan = student.generate_maintenance_recommendation(_features(), None, SPECS)[0]
    assert set(plan) == {"station_id", "site", "risk_score", "severity", "priority_action", "drivers", "estimated_hours", "priority_rank"}


def test_18_maintenance_heat_and_soiling_actions():
    plans = student.generate_maintenance_recommendation(_features(), None, SPECS, max_tasks=3)
    pv01 = [plan for plan in plans if plan["station_id"] == "PV-01"][0]
    assert pv01["drivers"] == ["thermal"]
    assert pv01["priority_action"] == "check_ventilation_and_module_hotspots"


def test_19_maintenance_high_cloud_unstable_driver():
    features = [
        {"station_id": "PV-09", "performance_ratio": 0.5, "cloud_risk": 0.9, "heat_stress": False, "expected_power_kw": 3},
        {"station_id": "PV-09", "performance_ratio": 0.6, "cloud_risk": 0.8, "heat_stress": False, "expected_power_kw": 3},
    ]
    result = student.generate_maintenance_recommendation(features)
    assert result[0]["drivers"] == ["unstable"]
    assert result[0]["priority_action"] == "review_weather_alignment"


def test_20_maintenance_limits_and_ranks_output():
    result = student.generate_maintenance_recommendation(_features(), None, SPECS, max_tasks=2)
    assert len(result) == 2
    assert [item["priority_rank"] for item in result] == [1, 2]


def test_21_maintenance_requires_list_and_positive_max():
    with pytest.raises(ValueError):
        student.generate_maintenance_recommendation({})
    with pytest.raises(ValueError):
        student.generate_maintenance_recommendation([], max_tasks=True)


def test_22_report_summary_counts_levels_and_sites():
    summary = student.score_output_prediction(_features(), _predictions())
    plans = student.generate_maintenance_recommendation(_features(), summary, SPECS)
    report = student.summarize_solar_report(plans, summary)
    assert report["total_tasks"] == 3
    assert report["high_priority"] >= 1
    assert report["site_counts"] == {"North": 2, "South": 1}
    assert report["prediction_quality"] == "watch"


def test_23_report_empty_plans_unknown_prediction_quality():
    assert student.summarize_solar_report([]) == {"total_tasks": 0, "high_priority": 0, "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "site_counts": {}, "total_estimated_hours": 0.0, "prediction_quality": "unknown"}


def test_24_report_quality_good_and_poor_boundaries():
    assert student.summarize_solar_report([], {"r2": 0.9})["prediction_quality"] == "good"
    assert student.summarize_solar_report([], {"r2": 0.2})["prediction_quality"] == "poor"


def test_25_report_requires_list():
    with pytest.raises(ValueError):
        student.summarize_solar_report({"site": "North"})


def test_26_end_to_end_solar_system_flow():
    cleaned = student.load_and_clean_solar(RAW_ROWS)
    features = student.build_weather_features(cleaned, SPECS)
    summary = student.score_output_prediction(features, _predictions())
    plans = student.generate_maintenance_recommendation(features, summary, SPECS)
    report = student.summarize_solar_report(plans, summary)
    assert report["total_tasks"] == 3
    assert plans[0]["station_id"] == "PV-03"
    assert summary["alert_count"] == 2


def test_27_end_to_end_handles_no_valid_rows():
    cleaned = student.load_and_clean_solar([{"bad": "row"}])
    assert cleaned == []
    assert student.summarize_solar_report(student.generate_maintenance_recommendation(student.build_weather_features(cleaned)))["total_tasks"] == 0


def test_28_end_to_end_capacity_changes_estimated_hours():
    features = _features()
    small = student.generate_maintenance_recommendation(features, None, [{"station_id": "PV-03", "capacity_kw": 3}])[0]
    large = student.generate_maintenance_recommendation(features, None, [{"station_id": "PV-03", "capacity_kw": 30}])[0]
    assert large["estimated_hours"] > small["estimated_hours"]


def test_29_prediction_alert_driver_can_change_priority_action():
    features = [{"station_id": "PV-10", "performance_ratio": 0.95, "cloud_risk": 0.1, "heat_stress": False, "expected_power_kw": 4}]
    plans = student.generate_maintenance_recommendation(features, {"alerts": [{"station_id": "PV-10"}]})
    assert plans[0]["drivers"] == ["prediction_alert"]
    assert plans[0]["priority_action"] == "review_forecast_and_sensor_pipeline"


def test_30_full_output_is_stably_sorted():
    rows = RAW_ROWS + [{"station_id": "PV-00", "timestamp": "t1", "irradiance_wm2": 800, "module_temp_c": 30, "ambient_temp_c": 24, "humidity_pct": 35, "power_kw": 7.5}]
    features = student.build_weather_features(student.load_and_clean_solar(rows), SPECS)
    plans = student.generate_maintenance_recommendation(features, None, SPECS, max_tasks=4)
    assert [plan["priority_rank"] for plan in plans] == list(range(1, len(plans) + 1))
