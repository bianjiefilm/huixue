import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fund04")
student = importlib.import_module(MODULE_NAME)


PROFILES = [
    {"customer_id": "C001", "risk_level": "balanced", "main_fund_type": "equity", "marketing_tag": "wealth_upgrade", "aum": 55000},
    {"customer_id": "C002", "risk_level": "aggressive", "main_fund_type": "index", "marketing_tag": "relationship_reactivation", "aum": 20000},
    {"customer_id": "C003", "risk_level": "defensive", "main_fund_type": "money_market", "marketing_tag": "stable_income", "aum": 5000},
]
CHURN = [{"customer_id": "C001", "churn_risk": 0.06}, {"customer_id": "C002", "churn_risk": 0.64}, {"customer_id": "C003", "churn_risk": 0.79}]
PRODUCTS = [
    {"product_id": "P-EQ", "fund_type": "equity", "risk_level": "balanced", "suitable_risk_levels": ["balanced", "aggressive"], "min_aum": 10000, "base_score": 0.28},
    {"product_id": "P-IDX", "fund_type": "index", "risk_level": "aggressive", "suitable_risk_levels": ["aggressive"], "min_aum": 10000, "base_score": 0.26, "retention_product": True},
    {"product_id": "P-MM", "fund_type": "money_market", "risk_level": "defensive", "suitable_risk_levels": ["defensive", "conservative"], "min_aum": 0, "base_score": 0.24, "retention_product": True},
    {"product_id": "P-BOND", "fund_type": "bond", "risk_level": "conservative", "suitable_risk_levels": ["defensive", "conservative", "balanced"], "min_aum": 3000, "base_score": 0.25},
]


def test_recommends_for_each_customer_sorted_by_id():
    result = student.recommend_fund_products(PROFILES, CHURN, PRODUCTS)
    assert [row["customer_id"] for row in result] == ["C001", "C002", "C003"]


def test_balanced_equity_customer_prefers_equity_product():
    recs = student.recommend_fund_products([PROFILES[0]], CHURN, PRODUCTS)[0]["recommendations"]
    assert recs[0] == {"product_id": "P-EQ", "score": 0.76, "reason": ["aum_fit", "risk_fit", "type_continuity"]}


def test_aggressive_high_churn_customer_prefers_index_retention():
    recs = student.recommend_fund_products([PROFILES[1]], CHURN, PRODUCTS)[0]["recommendations"]
    assert recs[0]["product_id"] == "P-IDX"
    assert recs[0]["score"] == 0.92
    assert "retention_fit" in recs[0]["reason"]


def test_defensive_stable_income_prefers_money_market():
    recs = student.recommend_fund_products([PROFILES[2]], CHURN, PRODUCTS)[0]["recommendations"]
    assert recs[0]["product_id"] == "P-MM"
    assert recs[0]["score"] == 1.0


def test_top_n_limits_recommendations():
    assert len(student.recommend_fund_products([PROFILES[0]], CHURN, PRODUCTS, top_n=1)[0]["recommendations"]) == 1


def test_unknown_churn_defaults_to_zero():
    recs = student.recommend_fund_products([PROFILES[1]], [], PRODUCTS)[0]["recommendations"]
    assert recs[0]["product_id"] == "P-IDX"
    assert recs[0]["score"] == 0.74


def test_risk_gap_penalizes_unsuitable_product():
    product = {"product_id": "P-HIGH", "fund_type": "equity", "risk_level": "aggressive", "suitable_risk_levels": ["aggressive"], "min_aum": 0, "base_score": 0.5}
    rec = student.recommend_fund_products([PROFILES[2]], CHURN, [product])[0]["recommendations"][0]
    assert rec["score"] == 0.42
    assert rec["reason"] == ["aum_fit", "risk_gap"]


def test_rejects_bad_input_types():
    with pytest.raises(ValueError):
        student.recommend_fund_products({}, CHURN, PRODUCTS)
    with pytest.raises(ValueError):
        student.recommend_fund_products(PROFILES, {}, PRODUCTS)
    with pytest.raises(ValueError):
        student.recommend_fund_products(PROFILES, CHURN, {})


def test_rejects_bad_top_n():
    with pytest.raises(ValueError):
        student.recommend_fund_products(PROFILES, CHURN, PRODUCTS, top_n=0)
    with pytest.raises(ValueError):
        student.recommend_fund_products(PROFILES, CHURN, PRODUCTS, top_n=True)


def test_empty_products_returns_empty_recommendation_lists():
    assert student.recommend_fund_products([PROFILES[0]], CHURN, []) == [{"customer_id": "C001", "recommendations": []}]


def test_invalid_profiles_and_products_are_ignored():
    result = student.recommend_fund_products(["bad", {}, PROFILES[0]], CHURN, ["bad", {}, PRODUCTS[0]])
    assert result == [{"customer_id": "C001", "recommendations": [{"product_id": "P-EQ", "score": 0.76, "reason": ["aum_fit", "risk_fit", "type_continuity"]}]}]


def test_tie_breaks_by_product_id():
    products = [{"product_id": "P-B", "base_score": 0.5}, {"product_id": "P-A", "base_score": 0.5}]
    recs = student.recommend_fund_products([PROFILES[0]], [], products)[0]["recommendations"]
    assert [r["product_id"] for r in recs] == ["P-A", "P-B"]


def test_score_capped_at_one():
    product = {"product_id": "P-X", "fund_type": "equity", "risk_level": "balanced", "suitable_risk_levels": ["balanced"], "min_aum": 0, "base_score": 0.9, "retention_product": True}
    assert student.recommend_fund_products([PROFILES[0]], [{"customer_id": "C001", "churn_risk": 0.9}], [product])[0]["recommendations"][0]["score"] == 1.0


def test_score_floored_at_zero():
    product = {"product_id": "P-X", "risk_level": "aggressive", "base_score": 0.05}
    assert student.recommend_fund_products([PROFILES[2]], [], [product])[0]["recommendations"][0]["score"] == 0.0


def test_output_has_exact_keys():
    row = student.recommend_fund_products([PROFILES[0]], CHURN, [PRODUCTS[0]])[0]
    assert set(row) == {"customer_id", "recommendations"}
    assert set(row["recommendations"][0]) == {"product_id", "score", "reason"}
