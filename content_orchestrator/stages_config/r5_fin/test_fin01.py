import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fin01")
student = importlib.import_module(MODULE_NAME)


STATEMENTS = [
    {"period": "2025Q2", "revenue": 1500, "cost": 900, "net_profit": 210, "current_assets": 700, "current_liabilities": 350, "total_assets": 2500, "total_liabilities": 1000, "equity": 1500},
    {"period": "2025Q1", "revenue": "1200", "cost": 760, "net_profit": 120, "current_assets": 600, "current_liabilities": 500, "total_assets": 2200, "total_liabilities": 1320, "equity": 880},
    {"period": "2025Q3", "revenue": 900, "cost": 780, "net_profit": -20, "current_assets": 300, "current_liabilities": 500, "total_assets": 1800, "total_liabilities": 1500, "equity": 300},
]


def _result():
    return student.analyze_financial_ratios(STATEMENTS)


def test_sorted_periods_and_keys():
    result = _result()
    assert [row["period"] for row in result] == ["2025Q1", "2025Q2", "2025Q3"]
    assert set(result[0]) == {"period", "revenue_growth", "gross_margin", "net_margin", "current_ratio", "debt_to_asset", "roe", "quality_level"}


def test_first_period_has_no_growth():
    first = _result()[0]
    assert first["revenue_growth"] is None
    assert first["quality_level"] == "watch"


def test_growth_and_margin_for_second_period():
    second = _result()[1]
    assert abs(second["revenue_growth"] - 0.25) < 1e-9
    assert abs(second["gross_margin"] - 0.4) < 1e-9
    assert abs(second["net_margin"] - 0.14) < 1e-9
    assert second["quality_level"] == "excellent"


def test_weak_period_with_negative_profit():
    third = _result()[2]
    assert abs(third["revenue_growth"] + 0.4) < 1e-9
    assert third["net_margin"] < 0
    assert third["quality_level"] == "weak"


def test_current_ratio_and_debt_to_asset():
    result = _result()
    assert result[1]["current_ratio"] == 2.0
    assert result[2]["debt_to_asset"] == 0.8333


def test_roe_calculation():
    assert _result()[1]["roe"] == 0.14


def test_zero_denominator_returns_none():
    row = {"period": "2025Q4", "revenue": 0, "cost": 0, "net_profit": 0, "current_assets": 1, "current_liabilities": 0, "total_assets": 0, "total_liabilities": 1, "equity": 0}
    result = student.analyze_financial_ratios([row])[0]
    assert result["gross_margin"] is None
    assert result["current_ratio"] is None
    assert result["debt_to_asset"] is None
    assert result["roe"] is None


def test_rejects_non_list_input():
    with pytest.raises(ValueError):
        student.analyze_financial_ratios({})


def test_ignores_bad_rows_and_empty_period():
    result = student.analyze_financial_ratios(["bad", {}, {"period": ""}, STATEMENTS[0]])
    assert len(result) == 1
    assert result[0]["period"] == "2025Q2"


def test_deduplicates_periods():
    result = student.analyze_financial_ratios([STATEMENTS[0], dict(STATEMENTS[0], revenue=999)])
    assert len(result) == 1
    assert result[0]["gross_margin"] == 0.4


def test_missing_numeric_fields_default_to_zero():
    result = student.analyze_financial_ratios([{"period": "2025Q1"}])[0]
    assert result["gross_margin"] is None
    assert result["quality_level"] == "weak"


def test_string_numbers_are_accepted():
    row = {"period": "2025Q1", "revenue": "1000", "cost": "500", "net_profit": "120", "current_assets": "300", "current_liabilities": "100", "total_assets": "1000", "total_liabilities": "400", "equity": "600"}
    result = student.analyze_financial_ratios([row])[0]
    assert result["gross_margin"] == 0.5
    assert result["roe"] == 0.2


def test_bool_values_are_not_treated_as_numbers():
    row = dict(STATEMENTS[0], revenue=True)
    result = student.analyze_financial_ratios([row])[0]
    assert result["gross_margin"] is None


def test_growth_when_previous_revenue_zero_is_none():
    rows = [dict(STATEMENTS[0], period="2025Q1", revenue=0), dict(STATEMENTS[1], period="2025Q2", revenue=100)]
    result = student.analyze_financial_ratios(rows)
    assert result[1]["revenue_growth"] is None


def test_quality_threshold_healthy():
    row = {"period": "2025Q1", "revenue": 1000, "cost": 600, "net_profit": 100, "current_assets": 180, "current_liabilities": 100, "total_assets": 1000, "total_liabilities": 500, "equity": 1000}
    assert student.analyze_financial_ratios([row])[0]["quality_level"] == "healthy"
