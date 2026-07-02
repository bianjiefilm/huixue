import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fund05")
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
CAMPAIGNS = [
    {"campaign_id": "CP-EQ", "base_score": 0.2, "target_segments": ["high_value_active"], "target_risk_levels": ["balanced", "aggressive"], "fund_types": ["equity"], "preferred_tag": "wealth_upgrade", "min_aum": 30000},
    {"campaign_id": "CP-IDX", "base_score": 0.24, "target_segments": ["high_value_watch", "growth_active"], "target_risk_levels": ["aggressive"], "fund_types": ["index"], "preferred_tag": "relationship_reactivation", "min_aum": 10000},
    {"campaign_id": "CP-MM", "base_score": 0.22, "target_segments": ["low_value"], "target_risk_levels": ["defensive", "conservative"], "fund_types": ["money_market"], "preferred_tag": "stable_income", "min_aum": 0},
]
INTERACTIONS = [
    {"customer_id": "C002", "contacts": 3, "clicks": 0, "complaints": 0},
    {"customer_id": "C003", "contacts": 2, "clicks": 1, "complaints": 1},
    {"customer_id": "C001", "contacts": 2, "clicks": 4, "complaints": 0},
]
PRODUCTS = [
    {"product_id": "P-EQ", "fund_type": "equity", "risk_level": "balanced", "suitable_risk_levels": ["balanced", "aggressive"], "min_aum": 10000, "base_score": 0.28},
    {"product_id": "P-IDX", "fund_type": "index", "risk_level": "aggressive", "suitable_risk_levels": ["aggressive"], "min_aum": 10000, "base_score": 0.26, "retention_product": True},
    {"product_id": "P-MM", "fund_type": "money_market", "risk_level": "defensive", "suitable_risk_levels": ["defensive", "conservative"], "min_aum": 0, "base_score": 0.24, "retention_product": True},
    {"product_id": "P-BOND", "fund_type": "bond", "risk_level": "conservative", "suitable_risk_levels": ["defensive", "conservative", "balanced"], "min_aum": 3000, "base_score": 0.25},
]


def _profiles():
    return student.build_customer_profiles(CUSTOMERS, TRANSACTIONS, "2026-05-01")


def _responses():
    return student.rank_marketing_responses(_profiles(), CAMPAIGNS)


def _churn():
    return student.predict_churn_risk(_profiles(), INTERACTIONS)


def _recs():
    return student.recommend_fund_products(_profiles(), _churn(), PRODUCTS)


def test_01_profiles_sorted_and_exact_keys():
    result = _profiles()
    assert [r["customer_id"] for r in result] == ["C001", "C002", "C003", "C004"]
    assert set(result[0]) == {"customer_id", "age_group", "risk_level", "aum", "transaction_count", "last_transaction_days", "main_fund_type", "rfm_segment", "marketing_tag"}


def test_02_profile_high_value_active():
    assert _profiles()[0]["rfm_segment"] == "high_value_active"
    assert _profiles()[0]["marketing_tag"] == "wealth_upgrade"


def test_03_profile_defensive_stable_income():
    assert _profiles()[2]["risk_level"] == "defensive"
    assert _profiles()[2]["marketing_tag"] == "stable_income"


def test_04_profile_no_transactions_kept():
    assert _profiles()[3]["transaction_count"] == 0
    assert _profiles()[3]["main_fund_type"] == "unknown"


def test_05_profiles_reject_bad_inputs():
    with pytest.raises(ValueError):
        student.build_customer_profiles({}, TRANSACTIONS)


def test_06_profiles_ignore_invalid_transactions():
    result = student.build_customer_profiles([CUSTOMERS[1]], TRANSACTIONS + [{"customer_id": "C001", "date": "bad", "amount": 999999}], "2026-05-01")
    assert result[0]["aum"] == 55000.0


def test_07_responses_choose_best_campaigns():
    result = _responses()
    assert [r["campaign_id"] for r in result[:3]] == ["CP-IDX", "CP-MM", "CP-EQ"]


def test_08_response_score_and_reasons():
    c001 = [r for r in _responses() if r["customer_id"] == "C001"][0]
    assert c001["propensity_score"] == 0.95
    assert c001["reason"] == ["aum_ready", "fund_type_match", "risk_match", "segment_match", "tag_match"]


def test_09_response_history_penalty():
    result = student.rank_marketing_responses([_profiles()[0]], CAMPAIGNS, [{"customer_id": "C001", "campaign_id": "CP-EQ", "responded": False}])[0]
    assert result["propensity_score"] == 0.87


def test_10_responses_reject_bad_history_type():
    with pytest.raises(ValueError):
        student.rank_marketing_responses([], [], {})


def test_11_churn_sorted_by_risk():
    assert [r["customer_id"] for r in _churn()] == ["C003", "C002", "C004", "C001"]


def test_12_churn_negative_feedback_critical():
    c003 = _churn()[0]
    assert c003["risk_level"] == "critical"
    assert c003["retention_action"] == "advisor_call_with_retention_offer"


def test_13_churn_recent_interest_reduces_score():
    c001 = [r for r in _churn() if r["customer_id"] == "C001"][0]
    assert c001["churn_risk"] == 0.06
    assert "recent_interest" in c001["drivers"]


def test_14_churn_rejects_bad_interactions():
    with pytest.raises(ValueError):
        student.predict_churn_risk([], {})


def test_15_recommendations_top_product_for_each_customer():
    result = _recs()
    assert [r["recommendations"][0]["product_id"] for r in result[:3]] == ["P-EQ", "P-IDX", "P-MM"]


def test_16_recommendations_reason_fields():
    c002 = [r for r in _recs() if r["customer_id"] == "C002"][0]["recommendations"][0]
    assert c002["score"] == 0.92
    assert "retention_fit" in c002["reason"]


def test_17_recommendations_top_n_limit():
    assert len(student.recommend_fund_products([_profiles()[0]], _churn(), PRODUCTS, top_n=1)[0]["recommendations"]) == 1


def test_18_recommendations_reject_bad_top_n():
    with pytest.raises(ValueError):
        student.recommend_fund_products([], [], [], top_n=0)


def test_19_recommendations_empty_products():
    assert student.recommend_fund_products([_profiles()[0]], [], []) == [{"customer_id": "C001", "recommendations": []}]


def test_20_recommendations_score_cap():
    product = {"product_id": "P-X", "fund_type": "equity", "risk_level": "balanced", "suitable_risk_levels": ["balanced"], "min_aum": 0, "base_score": 0.9, "retention_product": True}
    assert student.recommend_fund_products([_profiles()[0]], [{"customer_id": "C001", "churn_risk": 0.9}], [product])[0]["recommendations"][0]["score"] == 1.0


def test_21_report_summary_exact_counts():
    report = student.summarize_marketing_report(_profiles(), _responses(), _churn(), _recs())
    assert report == {"total_customers": 4, "high_value_customers": 2, "high_churn_customers": 3, "high_priority_responses": 3, "top_product_counts": {"P-EQ": 1, "P-IDX": 1, "P-MM": 2}, "action_mix": {"advisor_call_with_retention_offer": 1, "education_content": 1, "observe": 1, "reactivation_campaign": 1}}


def test_22_report_rejects_bad_inputs():
    with pytest.raises(ValueError):
        student.summarize_marketing_report({}, [], [], [])


def test_23_report_empty_inputs():
    assert student.summarize_marketing_report([], [], [], []) == {"total_customers": 0, "high_value_customers": 0, "high_churn_customers": 0, "high_priority_responses": 0, "top_product_counts": {}, "action_mix": {}}


def test_24_end_to_end_pipeline_flow():
    profiles = _profiles()
    responses = student.rank_marketing_responses(profiles, CAMPAIGNS)
    churn = student.predict_churn_risk(profiles, INTERACTIONS)
    recs = student.recommend_fund_products(profiles, churn, PRODUCTS)
    report = student.summarize_marketing_report(profiles, responses, churn, recs)
    assert report["total_customers"] == 4
    assert report["top_product_counts"]["P-MM"] == 2


def test_25_end_to_end_no_transactions():
    profiles = student.build_customer_profiles([{"customer_id": "C9", "age": 44, "risk_score": 10}], [])
    churn = student.predict_churn_risk(profiles)
    assert profiles[0]["marketing_tag"] == "stable_income"
    assert churn[0]["risk_level"] == "high"


def test_26_end_to_end_invalid_rows_are_ignored():
    profiles = student.build_customer_profiles(["bad", CUSTOMERS[1]], ["bad"] + TRANSACTIONS)
    assert len(profiles) == 1
    assert profiles[0]["customer_id"] == "C001"


def test_27_campaign_empty_returns_empty_response():
    assert student.rank_marketing_responses(_profiles(), []) == []


def test_28_product_tie_break_is_stable():
    products = [{"product_id": "P-B", "base_score": 0.5}, {"product_id": "P-A", "base_score": 0.5}]
    recs = student.recommend_fund_products([_profiles()[0]], [], products)[0]["recommendations"]
    assert [r["product_id"] for r in recs] == ["P-A", "P-B"]


def test_29_churn_score_is_capped():
    profile = {"customer_id": "C9", "last_transaction_days": 999, "aum": 999999, "rfm_segment": "high_value_watch"}
    assert student.predict_churn_risk([profile], [{"customer_id": "C9", "contacts": 3, "clicks": 0, "complaints": 9}])[0]["churn_risk"] == 1.0


def test_30_all_public_functions_require_lists():
    with pytest.raises(ValueError):
        student.recommend_fund_products({}, [], [])
