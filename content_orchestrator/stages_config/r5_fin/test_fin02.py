import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fin02")
student = importlib.import_module(MODULE_NAME)


RECORDS = [
    {"period": "2025Q2", "operating_cash_in": 1300, "operating_cash_out": 900, "investing_cash_flow": -120, "financing_cash_flow": 50, "capex": 80, "net_profit": 210, "cash_balance": 900, "monthly_burn": 100},
    {"period": "2025Q1", "operating_cash_in": "900", "operating_cash_out": 760, "investing_cash_flow": -200, "financing_cash_flow": 20, "capex": 160, "net_profit": 120, "cash_balance": 300, "monthly_burn": 80},
    {"period": "2025Q3", "operating_cash_in": 600, "operating_cash_out": 760, "investing_cash_flow": -100, "financing_cash_flow": 0, "capex": 120, "net_profit": -20, "cash_balance": 120, "monthly_burn": 60},
]


def _result():
    return student.analyze_cash_flows(RECORDS)


def test_sorted_periods_and_keys():
    result = _result()
    assert [row["period"] for row in result] == ["2025Q1", "2025Q2", "2025Q3"]
    assert set(result[0]) == {"period", "net_cash_flow", "free_cash_flow", "cash_conversion", "runway_months", "risk_level"}


def test_q1_high_risk_cash_gap():
    q1 = _result()[0]
    assert q1["net_cash_flow"] == -40.0
    assert q1["free_cash_flow"] == -20.0
    assert q1["cash_conversion"] == 1.1667
    assert q1["runway_months"] == 3.75
    assert q1["risk_level"] == "critical"


def test_q2_low_risk_cash_generation():
    q2 = _result()[1]
    assert q2["net_cash_flow"] == 330.0
    assert q2["free_cash_flow"] == 320.0
    assert q2["cash_conversion"] == 1.9048
    assert q2["risk_level"] == "low"


def test_q3_critical_with_negative_cash():
    q3 = _result()[2]
    assert q3["net_cash_flow"] == -260.0
    assert q3["free_cash_flow"] == -280.0
    assert q3["risk_level"] == "critical"


def test_zero_profit_conversion_is_none():
    row = dict(RECORDS[0], period="2025Q4", net_profit=0)
    assert student.analyze_cash_flows([row])[0]["cash_conversion"] is None


def test_zero_burn_runway_is_none():
    row = dict(RECORDS[0], monthly_burn=0)
    assert student.analyze_cash_flows([row])[0]["runway_months"] is None


def test_rejects_non_list_input():
    with pytest.raises(ValueError):
        student.analyze_cash_flows({})


def test_ignores_bad_rows():
    result = student.analyze_cash_flows(["bad", {}, {"period": ""}, RECORDS[0]])
    assert len(result) == 1
    assert result[0]["period"] == "2025Q2"


def test_deduplicates_periods():
    result = student.analyze_cash_flows([RECORDS[0], dict(RECORDS[0], operating_cash_in=999)])
    assert len(result) == 1
    assert result[0]["net_cash_flow"] == 330.0


def test_missing_fields_default_to_zero():
    result = student.analyze_cash_flows([{"period": "2025Q1"}])[0]
    assert result["net_cash_flow"] == 0.0
    assert result["risk_level"] == "low"


def test_negative_capex_uses_absolute_value():
    row = dict(RECORDS[0], capex=-80)
    assert student.analyze_cash_flows([row])[0]["free_cash_flow"] == 320.0


def test_bool_values_are_ignored():
    row = dict(RECORDS[0], operating_cash_in=True)
    result = student.analyze_cash_flows([row])[0]
    assert result["net_cash_flow"] == -970.0


def test_medium_risk_for_low_conversion_only():
    row = {"period": "2025Q1", "operating_cash_in": 60, "operating_cash_out": 0, "net_profit": 100, "cash_balance": 1000, "monthly_burn": 100}
    assert student.analyze_cash_flows([row])[0]["risk_level"] == "medium"


def test_high_risk_for_two_flags():
    row = {"period": "2025Q1", "operating_cash_in": 80, "operating_cash_out": 100, "net_profit": 0, "cash_balance": 1000, "monthly_burn": 100}
    assert student.analyze_cash_flows([row])[0]["risk_level"] == "high"


def test_empty_input_returns_empty_list():
    assert student.analyze_cash_flows([]) == []
