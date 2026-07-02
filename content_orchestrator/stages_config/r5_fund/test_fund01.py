import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fund01")
student = importlib.import_module(MODULE_NAME)


CUSTOMERS = [
    {"customer_id": "C003", "age": 64, "risk_score": 22},
    {"customer_id": "C001", "age": 36, "risk_score": 72},
    {"customer_id": "C002", "age": "28", "risk_score": "83"},
    {"customer_id": "C004", "age": 51, "risk_score": 48},
]

TRANSACTIONS = [
    {"customer_id": "C001", "date": "2026-04-20", "amount": 20000, "fund_type": "equity"},
    {"customer_id": "C001", "date": "2026-04-01", "amount": "25000", "fund_type": "bond"},
    {"customer_id": "C001", "date": "2026-03-15", "amount": 10000, "fund_type": "equity"},
    {"customer_id": "C002", "date": "2026-02-10", "amount": 8000, "fund_type": "index"},
    {"customer_id": "C002", "date": "2026-01-01", "amount": 12000, "fund_type": "index"},
    {"customer_id": "C003", "date": "2025-10-01", "amount": 5000, "fund_type": "money_market"},
]


def test_builds_sorted_profiles_with_core_fields():
    result = student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")
    assert [row["customer_id"] for row in result] == ["C001", "C002", "C003", "C004"]
    assert set(result[0]) == {"customer_id", "age_group", "risk_level", "aum", "transaction_count", "last_transaction_days", "main_fund_type", "rfm_segment", "marketing_tag"}


def test_high_value_active_customer_profile():
    c001 = student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")[0]
    assert c001 == {
        "customer_id": "C001",
        "age_group": "core",
        "risk_level": "balanced",
        "aum": 55000.0,
        "transaction_count": 3,
        "last_transaction_days": 11,
        "main_fund_type": "equity",
        "rfm_segment": "high_value_active",
        "marketing_tag": "wealth_upgrade",
    }


def test_growth_customer_uses_latest_recency_and_main_type():
    c002 = student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")[1]
    assert c002["age_group"] == "young"
    assert c002["risk_level"] == "aggressive"
    assert c002["aum"] == 20000.0
    assert c002["last_transaction_days"] == 80
    assert c002["main_fund_type"] == "index"
    assert c002["rfm_segment"] == "high_value_watch"


def test_defensive_money_market_gets_stable_income_tag():
    c003 = student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")[2]
    assert c003["risk_level"] == "defensive"
    assert c003["marketing_tag"] == "stable_income"


def test_customer_without_transactions_is_kept():
    c004 = student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")[3]
    assert c004["aum"] == 0.0
    assert c004["transaction_count"] == 0
    assert c004["last_transaction_days"] is None
    assert c004["main_fund_type"] == "unknown"


def test_mature_conservative_age_bucket():
    result = student.build_customer_profiles([{"customer_id": "C9", "age": 59, "risk_score": 30}], [], "2026-05-01")[0]
    assert result["age_group"] == "mature"
    assert result["risk_level"] == "conservative"


def test_senior_boundary_age_bucket():
    result = student.build_customer_profiles([{"customer_id": "C9", "age": 60, "risk_score": 55}], [], "2026-05-01")[0]
    assert result["age_group"] == "senior"
    assert result["risk_level"] == "balanced"


def test_rejects_non_list_inputs():
    with pytest.raises(ValueError):
        student.build_customer_profiles({}, TRANSACTIONS)
    with pytest.raises(ValueError):
        student.build_customer_profiles(CUSTOMERS, {})


def test_ignores_invalid_transactions():
    tx = TRANSACTIONS + [
        {"customer_id": "C001", "date": "bad", "amount": 99999, "fund_type": "equity"},
        {"customer_id": "C001", "date": "2026-04-01", "amount": -1, "fund_type": "equity"},
    ]
    c001 = student.build_customer_profiles(CUSTOMERS, tx, "2026-05-01")[0]
    assert c001["aum"] == 55000.0


def test_ignores_invalid_customer_rows_and_deduplicates():
    customers = ["bad", {"customer_id": ""}, CUSTOMERS[1], {"customer_id": "C001", "age": 99, "risk_score": 99}]
    result = student.build_customer_profiles(customers, TRANSACTIONS, "2026-05-01")
    assert len(result) == 1
    assert result[0]["age_group"] == "core"


def test_default_as_of_date_is_stable():
    explicit = student.build_customer_profiles([CUSTOMERS[1]], TRANSACTIONS, "2026-05-01")[0]
    implicit = student.build_customer_profiles([CUSTOMERS[1]], TRANSACTIONS)[0]
    assert explicit["last_transaction_days"] == implicit["last_transaction_days"]


def test_main_fund_type_tie_breaks_by_name():
    tx = [
        {"customer_id": "C1", "date": "2026-04-01", "amount": 100, "fund_type": "bond"},
        {"customer_id": "C1", "date": "2026-04-02", "amount": 100, "fund_type": "equity"},
    ]
    result = student.build_customer_profiles([{"customer_id": "C1", "age": 40, "risk_score": 60}], tx)[0]
    assert result["main_fund_type"] == "equity"


def test_stable_income_for_defensive_no_transactions():
    result = student.build_customer_profiles([{"customer_id": "C1", "age": 40, "risk_score": 10}], [])[0]
    assert result["marketing_tag"] == "stable_income"


def test_observe_for_low_value_balanced_customer():
    result = student.build_customer_profiles([{"customer_id": "C1", "age": 40, "risk_score": 60}], [])[0]
    assert result["marketing_tag"] == "observe"


def test_relationship_reactivation_for_high_value_watch():
    tx = [{"customer_id": "C1", "date": "2025-12-01", "amount": 50000, "fund_type": "bond"}]
    result = student.build_customer_profiles([{"customer_id": "C1", "age": 40, "risk_score": 60}], tx, "2026-05-01")[0]
    assert result["rfm_segment"] == "high_value_watch"
    assert result["marketing_tag"] == "relationship_reactivation"
