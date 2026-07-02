import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_solar03")
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


ACTUAL = [
    {"station_id": "PV-02", "timestamp": "t2", "actual_power_kw": 4.0},
    {"station_id": "PV-01", "timestamp": "t1", "actual_power_kw": 2.0},
    {"station_id": "PV-01", "timestamp": "t2", "actual_power_kw": 3.0},
]
PRED = [
    {"station_id": "PV-01", "timestamp": "t1", "predicted_power_kw": 2.2},
    {"station_id": "PV-01", "timestamp": "t2", "predicted_power_kw": 2.4},
    {"station_id": "PV-02", "timestamp": "t2", "predicted_power_kw": 4.4},
]


def test_basic_metrics_and_alerts():
    result = student.evaluate_power_predictions(ACTUAL, PRED, alert_threshold=0.15)
    expected = {
        "sample_count": 3,
        "mae": 0.4,
        "rmse": 0.432,
        "mape": 0.1333,
        "r2": 0.72,
        "alert_count": 1,
        "alerts": [{"station_id": "PV-01", "timestamp": "t2", "relative_error": 0.2, "abs_error": 0.6}],
        "worst_point": {"station_id": "PV-01", "timestamp": "t2", "relative_error": 0.2, "abs_error": 0.6},
    }
    assert_close(result, expected)


def test_threshold_inclusive_behavior_uses_greater_than():
    result = student.evaluate_power_predictions(ACTUAL, PRED, alert_threshold=0.2)
    assert result["alert_count"] == 0


def test_custom_threshold_flags_more_points():
    result = student.evaluate_power_predictions(ACTUAL, PRED, alert_threshold=0.05)
    assert result["alert_count"] == 3


def test_zero_actual_uses_safe_denominator():
    actual = [{"station_id": "PV-01", "timestamp": "night", "actual_power_kw": 0}]
    pred = [{"station_id": "PV-01", "timestamp": "night", "predicted_power_kw": 0.2}]
    result = student.evaluate_power_predictions(actual, pred, alert_threshold=0.1)
    assert result["mape"] == 0.2
    assert result["alert_count"] == 1


def test_perfect_predictions_have_r2_one():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 2}, {"station_id": "PV-01", "timestamp": "y", "actual_power_kw": 4}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 2}, {"station_id": "PV-01", "timestamp": "y", "predicted_power_kw": 4}]
    result = student.evaluate_power_predictions(actual, pred)
    assert result["mae"] == 0.0
    assert result["r2"] == 1.0


def test_constant_actual_imperfect_r2_zero():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 2}, {"station_id": "PV-01", "timestamp": "y", "actual_power_kw": 2}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 2}, {"station_id": "PV-01", "timestamp": "y", "predicted_power_kw": 3}]
    assert student.evaluate_power_predictions(actual, pred)["r2"] == 0.0


def test_no_matching_pairs_returns_empty_metrics():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 2}]
    pred = [{"station_id": "PV-02", "timestamp": "x", "predicted_power_kw": 2}]
    assert student.evaluate_power_predictions(actual, pred)["sample_count"] == 0


def test_skips_bad_actual_rows():
    actual = ACTUAL + [{"station_id": "PV-03", "timestamp": "bad", "actual_power_kw": "bad"}]
    assert student.evaluate_power_predictions(actual, PRED)["sample_count"] == 3


def test_skips_bad_prediction_rows():
    pred = PRED + [{"station_id": "PV-01", "timestamp": "t1", "predicted_power_kw": "bad"}]
    assert student.evaluate_power_predictions(ACTUAL, pred)["sample_count"] == 3


def test_numeric_strings_are_accepted():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": "2.5"}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": "3.0"}]
    assert student.evaluate_power_predictions(actual, pred)["mae"] == 0.5


def test_rows_must_be_lists():
    with pytest.raises(ValueError):
        student.evaluate_power_predictions({}, [])


def test_predictions_must_be_list():
    with pytest.raises(ValueError):
        student.evaluate_power_predictions([], {})


def test_negative_threshold_raises():
    with pytest.raises(ValueError):
        student.evaluate_power_predictions([], [], alert_threshold=-0.1)


def test_boolean_threshold_raises():
    with pytest.raises(ValueError):
        student.evaluate_power_predictions([], [], alert_threshold=True)


def test_missing_station_or_timestamp_are_skipped():
    actual = [{"station_id": "PV-01"}, {"timestamp": "x"}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 1}]
    assert student.evaluate_power_predictions(actual, pred)["sample_count"] == 0


def test_worst_point_tie_breaks_stably():
    actual = [{"station_id": "PV-B", "timestamp": "t", "actual_power_kw": 10}, {"station_id": "PV-A", "timestamp": "t", "actual_power_kw": 10}]
    pred = [{"station_id": "PV-B", "timestamp": "t", "predicted_power_kw": 12}, {"station_id": "PV-A", "timestamp": "t", "predicted_power_kw": 12}]
    assert student.evaluate_power_predictions(actual, pred)["worst_point"]["station_id"] == "PV-B"


def test_output_alerts_sorted_by_joined_pair_order():
    result = student.evaluate_power_predictions(ACTUAL, PRED, alert_threshold=0.05)
    assert [item["station_id"] for item in result["alerts"]] == ["PV-01", "PV-01", "PV-02"]


def test_blank_inputs_return_empty_metrics():
    result = student.evaluate_power_predictions([], [])
    assert result == {"sample_count": 0, "mae": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0, "alert_count": 0, "alerts": [], "worst_point": None}


def test_duplicate_actual_rows_last_value_wins():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 2}, {"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 4}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 5}]
    assert student.evaluate_power_predictions(actual, pred)["mae"] == 1.0


def test_duplicate_predictions_are_each_evaluated():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 2}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 2}, {"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 3}]
    assert student.evaluate_power_predictions(actual, pred)["sample_count"] == 2


def test_rmse_penalizes_large_single_error():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 10}, {"station_id": "PV-01", "timestamp": "y", "actual_power_kw": 10}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 10}, {"station_id": "PV-01", "timestamp": "y", "predicted_power_kw": 4}]
    assert student.evaluate_power_predictions(actual, pred)["rmse"] == 4.2426


def test_alerts_include_absolute_error_field():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 10}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 7}]
    assert student.evaluate_power_predictions(actual, pred)["alerts"][0]["abs_error"] == 3.0


def test_mape_averages_relative_errors():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 10}, {"station_id": "PV-01", "timestamp": "y", "actual_power_kw": 5}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 9}, {"station_id": "PV-01", "timestamp": "y", "predicted_power_kw": 4}]
    assert student.evaluate_power_predictions(actual, pred)["mape"] == 0.15


def test_station_and_timestamp_are_stripped_for_matching():
    actual = [{"station_id": " PV-01 ", "timestamp": " t ", "actual_power_kw": 10}]
    pred = [{"station_id": "PV-01", "timestamp": "t", "predicted_power_kw": 9}]
    assert student.evaluate_power_predictions(actual, pred)["sample_count"] == 1


def test_unmatched_prediction_is_ignored():
    actual = [{"station_id": "PV-01", "timestamp": "x", "actual_power_kw": 10}]
    pred = [{"station_id": "PV-01", "timestamp": "x", "predicted_power_kw": 9}, {"station_id": "PV-99", "timestamp": "x", "predicted_power_kw": 1}]
    assert student.evaluate_power_predictions(actual, pred)["sample_count"] == 1
