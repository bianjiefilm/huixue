import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_wind05")
student = importlib.import_module(MODULE_NAME)


RAW_ROWS = [
    {"turbine_id": "WT-02", "timestamp": "t2", "wind_speed": "7", "active_power_kw": "510", "gearbox_temp_c": "71", "vibration_mms": "3.2", "ambient_temp_c": "24", "status": "normal"},
    {"turbine_id": "WT-01", "timestamp": "t1", "wind_speed": 6, "active_power_kw": 420, "gearbox_temp_c": 66, "vibration_mms": 2.1, "ambient_temp_c": 25, "status": "normal"},
    {"turbine_id": "WT-01", "timestamp": "t2", "wind_speed": 8, "active_power_kw": 650, "gearbox_temp_c": 82, "vibration_mms": 5.6, "ambient_temp_c": 26, "status": "warning"},
]


SPECS = [
    {"turbine_id": "WT-01", "site": "North"},
    {"turbine_id": "WT-02", "site": "North"},
    {"turbine_id": "WT-03", "site": "South"},
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


def test_01_clean_normalizes_sorts_and_keeps_fields():
    result = student.load_and_clean_scada(RAW_ROWS)
    assert [r["turbine_id"] for r in result] == ["WT-01", "WT-01", "WT-02"]
    assert result[0]["wind_speed"] == 6.0
    assert result[2]["status"] == "NORMAL"
    assert set(result[0]) == {"turbine_id", "timestamp", "wind_speed", "active_power_kw", "gearbox_temp_c", "vibration_mms", "ambient_temp_c", "status"}


def test_02_clean_drops_negative_and_extreme_values():
    rows = RAW_ROWS + [
        {"turbine_id": "WT-99", "timestamp": "bad1", "wind_speed": -1, "active_power_kw": 10, "gearbox_temp_c": 50, "vibration_mms": 1},
        {"turbine_id": "WT-99", "timestamp": "bad2", "wind_speed": 5, "active_power_kw": 10, "gearbox_temp_c": 150, "vibration_mms": 1},
    ]
    assert len(student.load_and_clean_scada(rows)) == 3


def test_03_clean_deduplicates_first_timestamp():
    rows = RAW_ROWS + [{"turbine_id": "WT-01", "timestamp": "t1", "wind_speed": 9, "active_power_kw": 999, "gearbox_temp_c": 99, "vibration_mms": 9}]
    result = student.load_and_clean_scada(rows)
    assert result[0]["active_power_kw"] == 420.0


def test_04_clean_skips_missing_and_non_numeric_rows():
    rows = [{"turbine_id": "WT-01", "timestamp": "x"}, {"turbine_id": "WT-01", "timestamp": "y", "wind_speed": "bad", "active_power_kw": 1, "gearbox_temp_c": 1, "vibration_mms": 1}]
    assert student.load_and_clean_scada(rows) == []


def test_05_clean_requires_list():
    with pytest.raises(ValueError):
        student.load_and_clean_scada({"turbine_id": "WT-01"})


def test_06_features_basic_window_values():
    readings = student.load_and_clean_scada(RAW_ROWS)
    result = student.build_health_features(readings, window_size=2)
    assert result[1]["turbine_id"] == "WT-01"
    assert result[1]["temp_avg"] == 74.0
    assert result[1]["vibration_max"] == 5.6
    assert result[1]["anomaly_count"] == 1
    assert result[1]["hot_flag"] is True
    assert result[1]["vibration_flag"] is True


def test_07_features_turbine_windows_are_separate():
    readings = student.load_and_clean_scada(RAW_ROWS)
    result = student.build_health_features(readings, window_size=3)
    assert result[2]["turbine_id"] == "WT-02"
    assert result[2]["temp_avg"] == 71.0


def test_08_features_window_size_one():
    readings = student.load_and_clean_scada(RAW_ROWS)
    result = student.build_health_features(readings, window_size=1)
    assert result[1]["temp_avg"] == 82.0
    assert result[1]["power_avg"] == 650.0


def test_09_features_empty_input():
    assert student.build_health_features([]) == []


def test_10_features_requires_list():
    with pytest.raises(ValueError):
        student.build_health_features("bad")


def test_11_features_bad_window_raises():
    with pytest.raises(ValueError):
        student.build_health_features([], window_size=0)


def test_12_risk_scores_hot_vibration_as_critical():
    features = student.build_health_features(student.load_and_clean_scada(RAW_ROWS), window_size=2)
    risks = student.score_fault_risk(features)
    assert risks[1]["turbine_id"] == "WT-01"
    assert risks[1]["risk_score"] >= 0.82
    assert risks[1]["risk_level"] == "critical"
    assert risks[1]["drivers"] == ["anomaly", "temperature", "vibration"]


def test_13_risk_low_for_normal_reading():
    features = student.build_health_features(student.load_and_clean_scada(RAW_ROWS), window_size=1)
    risks = student.score_fault_risk(features)
    assert risks[0]["risk_level"] == "low"
    assert risks[0]["risk_score"] < 0.35


def test_14_risk_low_power_driver():
    features = [{"turbine_id": "WT-03", "timestamp": "t1", "temp_avg": 65, "vibration_max": 3.1, "power_avg": 80, "anomaly_count": 0, "hot_flag": False, "vibration_flag": False}]
    result = student.score_fault_risk(features)
    assert "low_power" in result[0]["drivers"]


def test_15_risk_requires_list():
    with pytest.raises(ValueError):
        student.score_fault_risk({"turbine_id": "WT-01"})


def test_16_risk_skips_invalid_rows():
    result = student.score_fault_risk(["bad", {"turbine_id": "WT-01", "timestamp": "t1", "temp_avg": "bad"}])
    assert result == []


def test_17_plan_orders_by_risk_level_and_score():
    risks = [
        {"turbine_id": "WT-02", "risk_level": "medium", "risk_score": 0.4, "drivers": ["temperature"]},
        {"turbine_id": "WT-01", "risk_level": "critical", "risk_score": 0.91, "drivers": ["vibration"]},
        {"turbine_id": "WT-03", "risk_level": "high", "risk_score": 0.7, "drivers": ["low_power"]},
    ]
    result = student.generate_maintenance_plan(risks, SPECS, max_daily_tasks=2)
    assert [p["turbine_id"] for p in result] == ["WT-01", "WT-03", "WT-02"]
    assert [p["scheduled_day"] for p in result] == [1, 1, 2]


def test_18_plan_merges_same_turbine_best_risk():
    risks = [{"turbine_id": "WT-01", "risk_level": "medium", "risk_score": 0.4}, {"turbine_id": "WT-01", "risk_level": "high", "risk_score": 0.8}]
    result = student.generate_maintenance_plan(risks, SPECS)
    assert len(result) == 1
    assert result[0]["risk_level"] == "high"


def test_19_plan_unknown_site_and_actions():
    result = student.generate_maintenance_plan([{"turbine_id": "WT-99", "risk_level": "low", "risk_score": 0.1}], SPECS)
    assert result[0]["site"] == "UNKNOWN"
    assert result[0]["action"] == "monitor"


def test_20_plan_requires_lists():
    with pytest.raises(ValueError):
        student.generate_maintenance_plan({}, SPECS)


def test_21_plan_bad_capacity_raises():
    with pytest.raises(ValueError):
        student.generate_maintenance_plan([], SPECS, max_daily_tasks=0)


def test_22_report_summary_counts_sites_and_levels():
    plans = [
        {"site": "North", "risk_level": "critical", "estimated_hours": 8},
        {"site": "North", "risk_level": "high", "estimated_hours": 6},
        {"site": "South", "risk_level": "low", "estimated_hours": 2},
    ]
    result = student.summarize_warning_report(plans)
    assert result == {
        "total_tasks": 3,
        "high_priority": 2,
        "level_counts": {"critical": 1, "high": 1, "medium": 0, "low": 1},
        "site_counts": {"North": 2, "South": 1},
        "total_estimated_hours": 16.0,
    }


def test_23_report_empty_plans():
    assert student.summarize_warning_report([]) == {"total_tasks": 0, "high_priority": 0, "level_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "site_counts": {}, "total_estimated_hours": 0.0}


def test_24_report_accepts_severity_alias():
    result = student.summarize_warning_report([{"site": "West", "severity": "high", "estimated_hours": 5}])
    assert result["high_priority"] == 1
    assert result["site_counts"] == {"West": 1}


def test_25_report_requires_list():
    with pytest.raises(ValueError):
        student.summarize_warning_report({"site": "North"})


def test_26_end_to_end_warning_system_flow():
    cleaned = student.load_and_clean_scada(RAW_ROWS)
    features = student.build_health_features(cleaned, window_size=2)
    risks = student.score_fault_risk(features)
    plans = student.generate_maintenance_plan(risks, SPECS, max_daily_tasks=2)
    report = student.summarize_warning_report(plans)
    assert report["total_tasks"] == 2
    assert report["high_priority"] >= 1
    assert plans[0]["turbine_id"] == "WT-01"


def test_27_end_to_end_handles_no_valid_rows():
    cleaned = student.load_and_clean_scada([{"bad": "row"}])
    assert cleaned == []
    assert student.summarize_warning_report(student.generate_maintenance_plan(student.score_fault_risk(student.build_health_features(cleaned)), SPECS))["total_tasks"] == 0


def test_28_end_to_end_capacity_creates_second_day():
    rows = RAW_ROWS + [{"turbine_id": "WT-03", "timestamp": "t5", "wind_speed": 5, "active_power_kw": 50, "gearbox_temp_c": 90, "vibration_mms": 6, "ambient_temp_c": 28, "status": "fault"}]
    plans = student.generate_maintenance_plan(student.score_fault_risk(student.build_health_features(student.load_and_clean_scada(rows))), SPECS, max_daily_tasks=1)
    assert [p["scheduled_day"] for p in plans] == [1, 2, 3]


def test_29_driver_fields_are_stable_sorted_lists():
    features = [{"turbine_id": "WT-01", "timestamp": "t", "temp_avg": 90, "vibration_max": 6, "power_avg": 50, "anomaly_count": 1, "hot_flag": True, "vibration_flag": True}]
    assert student.score_fault_risk(features)[0]["drivers"] == ["anomaly", "low_power", "temperature", "vibration"]


def test_30_plan_output_has_exact_keys():
    plan = student.generate_maintenance_plan([{"turbine_id": "WT-01", "risk_level": "high", "risk_score": 0.7}], SPECS)[0]
    assert set(plan) == {"turbine_id", "risk_level", "risk_score", "priority_rank", "scheduled_day", "site", "action", "estimated_hours", "drivers"}
