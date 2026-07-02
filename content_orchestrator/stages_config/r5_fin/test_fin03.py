import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fin03")
student = importlib.import_module(MODULE_NAME)


METRICS = [
    {"period": "2025Q1", "revenue_growth": None, "net_margin": 0.1, "current_ratio": 1.2, "debt_to_asset": 0.6, "roe": 0.1364},
    {"period": "2025Q2", "revenue_growth": 0.25, "net_margin": 0.14, "current_ratio": 2.0, "debt_to_asset": 0.4, "roe": 0.14},
    {"period": "2025Q3", "revenue_growth": -0.4, "net_margin": -0.0222, "current_ratio": 0.6, "debt_to_asset": 0.8333, "roe": -0.0667},
]
CASH = [
    {"period": "2025Q1", "free_cash_flow": -20, "runway_months": 3.75},
    {"period": "2025Q2", "free_cash_flow": 320, "runway_months": 9},
    {"period": "2025Q3", "free_cash_flow": -280, "runway_months": 2},
]


def _result():
    return student.detect_financial_risks(METRICS, CASH)


def test_sorted_by_risk_descending():
    assert [row["period"] for row in _result()] == ["2025Q3", "2025Q1", "2025Q2"]


def test_critical_risk_full_signals():
    top = _result()[0]
    assert top["risk_level"] == "critical"
    assert top["risk_score"] == 100
    assert top["recommended_action"] == "board_level_turnaround"
    assert top["signals"] == ["high_leverage", "liquidity_pressure", "negative_free_cash_flow", "negative_return", "revenue_decline", "short_cash_runway", "thin_profit"]


def test_medium_risk_cash_pressure():
    q1 = [row for row in _result() if row["period"] == "2025Q1"][0]
    assert q1["risk_level"] == "medium"
    assert q1["risk_score"] == 28
    assert q1["signals"] == ["negative_free_cash_flow", "short_cash_runway"]


def test_low_risk_no_signals():
    q2 = [row for row in _result() if row["period"] == "2025Q2"][0]
    assert q2 == {"period": "2025Q2", "risk_score": 0, "risk_level": "low", "signals": [], "recommended_action": "routine_monitoring"}


def test_high_risk_threshold():
    metrics = [{"period": "P", "revenue_growth": -0.2, "net_margin": 0.01, "current_ratio": 0.8}]
    result = student.detect_financial_risks(metrics, [])[0]
    assert result["risk_level"] == "high"
    assert result["risk_score"] == 58


def test_rejects_non_list_inputs():
    with pytest.raises(ValueError):
        student.detect_financial_risks({}, [])
    with pytest.raises(ValueError):
        student.detect_financial_risks([], {})


def test_ignores_bad_rows():
    result = student.detect_financial_risks(["bad", {}, {"period": ""}, METRICS[1]], CASH)
    assert len(result) == 1
    assert result[0]["period"] == "2025Q2"


def test_deduplicates_periods():
    result = student.detect_financial_risks([METRICS[2], dict(METRICS[2], net_margin=1)], CASH)
    assert len(result) == 1
    assert result[0]["risk_score"] == 100


def test_missing_cash_flow_still_works():
    result = student.detect_financial_risks([METRICS[2]], [])[0]
    assert result["risk_score"] == 88
    assert "negative_free_cash_flow" not in result["signals"]


def test_string_numbers_are_accepted():
    result = student.detect_financial_risks([{"period": "P", "net_margin": "-0.1", "debt_to_asset": "0.9"}], [])[0]
    assert result["risk_score"] == 36


def test_bool_values_do_not_trigger_false_numeric_signal():
    result = student.detect_financial_risks([{"period": "P", "debt_to_asset": True}], [])[0]
    assert result["risk_score"] == 0


def test_medium_action():
    result = student.detect_financial_risks([{"period": "P", "net_margin": 0.01, "roe": -0.1}], [])[0]
    assert result["risk_level"] == "medium"
    assert result["recommended_action"] == "monthly_monitoring"


def test_high_action():
    result = student.detect_financial_risks([{"period": "P", "current_ratio": 0.5, "debt_to_asset": 0.9, "roe": -0.1}], [])[0]
    assert result["risk_level"] == "high"
    assert result["recommended_action"] == "cash_and_debt_recovery_plan"


def test_empty_inputs_return_empty_list():
    assert student.detect_financial_risks([], []) == []


def test_cash_map_ignores_bad_rows():
    result = student.detect_financial_risks([METRICS[0]], ["bad", {}, {"period": ""}])[0]
    assert result["risk_score"] == 0
