import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_wind03")
student = importlib.import_module(MODULE_NAME)


def assert_close(actual, expected, tol=1e-9):
    assert type(actual) is type(expected), f"type mismatch: {type(actual)} != {type(expected)}"
    if isinstance(expected, float):
        assert abs(actual - expected) < tol, f"{actual} != {expected}"
    elif isinstance(expected, dict):
        assert set(actual.keys()) == set(expected.keys())
        for key in expected:
            assert_close(actual[key], expected[key], tol)
    else:
        assert actual == expected


def test_balanced_fault_prediction_metrics():
    actual = student.evaluate_fault_predictions([1, 0, 1, 0], [0.9, 0.7, 0.4, 0.1], threshold=0.5)
    expected = {
        "threshold": 0.5, "total": 4, "predicted_alerts": 2, "actual_faults": 2,
        "confusion_matrix": {"tp": 1, "fp": 1, "tn": 1, "fn": 1},
        "precision": 0.5, "recall": 0.5, "f1": 0.5,
        "false_alarm_rate": 0.5, "missed_alarm_rate": 0.5, "accuracy": 0.5,
    }
    assert_close(actual, expected)


def test_perfect_predictions_have_full_scores():
    actual = student.evaluate_fault_predictions([1, 1, 0, 0], [0.91, 0.8, 0.2, 0.05])
    assert actual["confusion_matrix"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    assert actual["precision"] == 1.0
    assert actual["recall"] == 1.0
    assert actual["f1"] == 1.0
    assert actual["accuracy"] == 1.0


def test_all_negative_labels_with_false_alarms():
    actual = student.evaluate_fault_predictions([0, 0, 0], [0.2, 0.6, 0.7])
    assert actual["confusion_matrix"] == {"tp": 0, "fp": 2, "tn": 1, "fn": 0}
    assert actual["precision"] == 0.0
    assert actual["recall"] == 0.0
    assert actual["false_alarm_rate"] == 0.6667
    assert actual["missed_alarm_rate"] == 0.0


def test_all_positive_labels_with_missed_faults():
    actual = student.evaluate_fault_predictions([1, 1, 1, 1], [0.9, 0.4, 0.3, 0.2])
    assert actual["confusion_matrix"] == {"tp": 1, "fp": 0, "tn": 0, "fn": 3}
    assert actual["precision"] == 1.0
    assert actual["recall"] == 0.25
    assert actual["f1"] == 0.4
    assert actual["missed_alarm_rate"] == 0.75


def test_custom_threshold_changes_predictions():
    actual = student.evaluate_fault_predictions([1, 0, 1, 0, 1], [0.6, 0.55, 0.45, 0.35, 0.8], threshold=0.6)
    assert actual["threshold"] == 0.6
    assert actual["confusion_matrix"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 1}
    assert actual["precision"] == 1.0
    assert actual["recall"] == 0.6667
    assert actual["f1"] == 0.8


def test_threshold_boundary_is_inclusive():
    actual = student.evaluate_fault_predictions([1, 0], [0.5, 0.4999], threshold=0.5)
    assert actual["confusion_matrix"] == {"tp": 1, "fp": 0, "tn": 1, "fn": 0}


def test_rounding_to_four_decimals():
    actual = student.evaluate_fault_predictions([1, 1, 1, 0, 0, 0], [0.9, 0.8, 0.2, 0.7, 0.4, 0.3])
    assert actual["precision"] == 0.6667
    assert actual["recall"] == 0.6667
    assert actual["f1"] == 0.6667
    assert actual["accuracy"] == 0.6667


def test_non_list_inputs_raise_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions((1, 0), [0.8, 0.2])


def test_length_mismatch_raises_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions([1, 0], [0.8])


def test_empty_labels_raise_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions([], [])


def test_invalid_label_raises_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions([1, 2, 0], [0.8, 0.6, 0.1])


def test_invalid_score_raises_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions([1, 0], [0.8, "bad"])


def test_invalid_threshold_raises_value_error():
    with pytest.raises(ValueError):
        student.evaluate_fault_predictions([1, 0], [0.8, 0.2], threshold=1.2)
