import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fin05")
student = importlib.import_module(MODULE_NAME)


STATEMENTS = [
    {"period": "2025Q2", "revenue": 1500, "cost": 900, "net_profit": 210, "current_assets": 700, "current_liabilities": 350, "total_assets": 2500, "total_liabilities": 1000, "equity": 1500},
    {"period": "2025Q1", "revenue": "1200", "cost": 760, "net_profit": 120, "current_assets": 600, "current_liabilities": 500, "total_assets": 2200, "total_liabilities": 1320, "equity": 880},
    {"period": "2025Q3", "revenue": 900, "cost": 780, "net_profit": -20, "current_assets": 300, "current_liabilities": 500, "total_assets": 1800, "total_liabilities": 1500, "equity": 300},
]
CASH = [
    {"period": "2025Q2", "operating_cash_in": 1300, "operating_cash_out": 900, "investing_cash_flow": -120, "financing_cash_flow": 50, "capex": 80, "net_profit": 210, "cash_balance": 900, "monthly_burn": 100},
    {"period": "2025Q1", "operating_cash_in": "900", "operating_cash_out": 760, "investing_cash_flow": -200, "financing_cash_flow": 20, "capex": 160, "net_profit": 120, "cash_balance": 300, "monthly_burn": 80},
    {"period": "2025Q3", "operating_cash_in": 600, "operating_cash_out": 760, "investing_cash_flow": -100, "financing_cash_flow": 0, "capex": 120, "net_profit": -20, "cash_balance": 120, "monthly_burn": 60},
]
PROJECTS = [
    {"project_id": "P2", "initial_investment": 800, "cash_flows": [260, 260, 260, 260]},
    {"project_id": "P1", "initial_investment": "1000", "cash_flows": [400, 420, 430]},
    {"project_id": "P3", "initial_investment": 500, "cash_flows": [80, 90, 100]},
]


def _metrics():
    return student.analyze_financial_ratios(STATEMENTS)


def _cash():
    return student.analyze_cash_flows(CASH)


def _risks():
    return student.detect_financial_risks(_metrics(), _cash())


def _investments():
    return student.evaluate_investment_returns(PROJECTS, 0.1)


def test_01_metrics_period_order():
    assert [row["period"] for row in _metrics()] == ["2025Q1", "2025Q2", "2025Q3"]


def test_02_metrics_excellent_period():
    assert _metrics()[1]["quality_level"] == "excellent"


def test_03_metrics_weak_period():
    assert _metrics()[2]["quality_level"] == "weak"


def test_04_metrics_zero_denominator():
    assert student.analyze_financial_ratios([{"period": "P"}])[0]["gross_margin"] is None


def test_05_metrics_reject_bad_type():
    with pytest.raises(ValueError):
        student.analyze_financial_ratios({})


def test_06_cash_period_order():
    assert [row["period"] for row in _cash()] == ["2025Q1", "2025Q2", "2025Q3"]


def test_07_cash_q1_critical():
    assert _cash()[0]["risk_level"] == "critical"


def test_08_cash_q2_low():
    assert _cash()[1]["risk_level"] == "low"


def test_09_cash_zero_burn():
    assert student.analyze_cash_flows([dict(CASH[0], monthly_burn=0)])[0]["runway_months"] is None


def test_10_cash_reject_bad_type():
    with pytest.raises(ValueError):
        student.analyze_cash_flows({})


def test_11_risk_top_period():
    assert _risks()[0]["period"] == "2025Q3"


def test_12_risk_critical_signals():
    assert "high_leverage" in _risks()[0]["signals"]
    assert "negative_free_cash_flow" in _risks()[0]["signals"]


def test_13_risk_low_period():
    low = [row for row in _risks() if row["period"] == "2025Q2"][0]
    assert low["risk_score"] == 0


def test_14_risk_reject_bad_type():
    with pytest.raises(ValueError):
        student.detect_financial_risks({}, [])


def test_15_investment_order():
    assert [row["project_id"] for row in _investments()] == ["P1", "P2", "P3"]


def test_16_investment_p1_invest():
    assert _investments()[0]["priority"] == "invest"


def test_17_investment_p3_defer():
    assert _investments()[-1]["priority"] == "defer"


def test_18_investment_zero_initial():
    assert student.evaluate_investment_returns([{"project_id": "Z", "initial_investment": 0, "cash_flows": [10]}])[0]["roi"] is None


def test_19_investment_reject_bad_type():
    with pytest.raises(ValueError):
        student.evaluate_investment_returns({})


def test_20_report_exact_summary():
    report = student.summarize_financial_report(_metrics(), _cash(), _risks(), _investments())
    assert report == {"periods": 3, "excellent_periods": 1, "negative_free_cash_periods": 2, "critical_risk_periods": 1, "invest_projects": 1, "overall_status": "turnaround_required"}


def test_21_report_growth_ready_without_critical():
    report = student.summarize_financial_report(_metrics(), _cash(), [{"risk_level": "low"}], _investments())
    assert report["overall_status"] == "growth_ready"


def test_22_report_stable_without_invest():
    report = student.summarize_financial_report(_metrics(), _cash(), [{"risk_level": "low"}], [{"priority": "watch"}])
    assert report["overall_status"] == "stable"


def test_23_report_rejects_bad_type():
    with pytest.raises(ValueError):
        student.summarize_financial_report({}, [], [], [])


def test_24_end_to_end_pipeline_runs():
    metrics = student.analyze_financial_ratios(STATEMENTS)
    cash = student.analyze_cash_flows(CASH)
    risks = student.detect_financial_risks(metrics, cash)
    investments = student.evaluate_investment_returns(PROJECTS)
    assert student.summarize_financial_report(metrics, cash, risks, investments)["periods"] == 3


def test_25_bad_rows_ignored_in_pipeline():
    assert len(student.analyze_financial_ratios(["bad", STATEMENTS[0]])) == 1


def test_26_empty_inputs():
    assert student.summarize_financial_report([], [], [], []) == {"periods": 0, "excellent_periods": 0, "negative_free_cash_periods": 0, "critical_risk_periods": 0, "invest_projects": 0, "overall_status": "stable"}


def test_27_project_tie_break():
    rows = [{"project_id": "B", "initial_investment": 0, "cash_flows": []}, {"project_id": "A", "initial_investment": 0, "cash_flows": []}]
    assert [row["project_id"] for row in student.evaluate_investment_returns(rows)] == ["A", "B"]


def test_28_cash_bool_ignored():
    row = dict(CASH[0], operating_cash_in=True)
    assert student.analyze_cash_flows([row])[0]["net_cash_flow"] == -970.0


def test_29_metric_bool_ignored():
    row = dict(STATEMENTS[0], revenue=True)
    assert student.analyze_financial_ratios([row])[0]["gross_margin"] is None


def test_30_discount_rate_boundary():
    with pytest.raises(ValueError):
        student.evaluate_investment_returns([], -1)
