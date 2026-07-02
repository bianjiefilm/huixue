import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fund03")
student = importlib.import_module(MODULE_NAME)


PROFILES = [
    {"customer_id": "C001", "aum": 55000, "last_transaction_days": 11, "rfm_segment": "high_value_active"},
    {"customer_id": "C002", "aum": 20000, "last_transaction_days": 151, "rfm_segment": "high_value_watch"},
    {"customer_id": "C003", "aum": 5000, "last_transaction_days": 212, "rfm_segment": "low_value"},
    {"customer_id": "C004", "aum": 0, "last_transaction_days": None, "rfm_segment": "low_value"},
]

INTERACTIONS = [
    {"customer_id": "C002", "contacts": 3, "clicks": 0, "complaints": 0},
    {"customer_id": "C003", "contacts": 2, "clicks": 1, "complaints": 1},
    {"customer_id": "C001", "contacts": 2, "clicks": 4, "complaints": 0},
]


def test_predicts_sorted_churn_risk():
    result = student.predict_churn_risk(PROFILES, INTERACTIONS)
    assert [row["customer_id"] for row in result] == ["C003", "C002", "C004", "C001"]


def test_critical_inactive_negative_feedback_customer():
    result = student.predict_churn_risk([PROFILES[2]], INTERACTIONS)[0]
    assert result == {"customer_id": "C003", "churn_risk": 0.79, "risk_level": "critical", "drivers": ["inactive", "low_value", "negative_feedback"], "retention_action": "advisor_call_with_retention_offer"}


def test_high_value_watch_with_low_engagement():
    result = student.predict_churn_risk([PROFILES[1]], INTERACTIONS)[0]
    assert result["churn_risk"] == 0.64
    assert result["risk_level"] == "high"
    assert result["retention_action"] == "education_content"


def test_recent_interest_reduces_risk():
    result = student.predict_churn_risk([PROFILES[0]], INTERACTIONS)[0]
    assert result["churn_risk"] == 0.06
    assert result["risk_level"] == "low"
    assert "recent_interest" in result["drivers"]


def test_none_recency_is_treated_as_inactive():
    result = student.predict_churn_risk([PROFILES[3]], [])[0]
    assert result["drivers"] == ["inactive", "low_value"]
    assert result["risk_level"] == "high"


def test_cooling_driver_boundary():
    result = student.predict_churn_risk([{"customer_id": "C9", "last_transaction_days": 91, "aum": 1, "rfm_segment": "growth_active"}])[0]
    assert result["drivers"] == ["cooling"]
    assert result["risk_level"] == "low"


def test_no_interactions_defaults_to_empty():
    result = student.predict_churn_risk([PROFILES[0]])[0]
    assert result["churn_risk"] == 0.18
    assert result["drivers"] == ["large_aum"]


def test_multiple_interactions_are_aggregated():
    interactions = [{"customer_id": "C1", "contacts": 1, "clicks": 0}, {"customer_id": "C1", "contacts": 1, "clicks": 0}]
    result = student.predict_churn_risk([{"customer_id": "C1", "last_transaction_days": 1, "aum": 1, "rfm_segment": "growth_active"}], interactions)[0]
    assert result["drivers"] == ["low_engagement"]


def test_positive_clicks_prevent_low_engagement_driver():
    interactions = [{"customer_id": "C1", "contacts": 2, "clicks": 1}]
    result = student.predict_churn_risk([{"customer_id": "C1", "last_transaction_days": 1, "aum": 1, "rfm_segment": "growth_active"}], interactions)[0]
    assert result["drivers"] == []


def test_rejects_bad_input_types():
    with pytest.raises(ValueError):
        student.predict_churn_risk({})
    with pytest.raises(ValueError):
        student.predict_churn_risk([], {})


def test_invalid_profiles_are_ignored():
    assert student.predict_churn_risk(["bad", {}, PROFILES[0]], INTERACTIONS)[0]["customer_id"] == "C001"


def test_invalid_interactions_are_ignored():
    result = student.predict_churn_risk([PROFILES[1]], ["bad", {}, {"customer_id": "C002", "contacts": "bad", "clicks": "bad"}])[0]
    assert result["drivers"] == ["cooling", "high_value_watch"]


def test_score_capped_at_one():
    profile = {"customer_id": "C1", "last_transaction_days": 999, "aum": 999999, "rfm_segment": "high_value_watch"}
    interactions = [{"customer_id": "C1", "contacts": 2, "clicks": 0, "complaints": 5}]
    assert student.predict_churn_risk([profile], interactions)[0]["churn_risk"] == 1.0


def test_output_has_exact_keys():
    result = student.predict_churn_risk([PROFILES[0]])[0]
    assert set(result) == {"customer_id", "churn_risk", "risk_level", "drivers", "retention_action"}


def test_empty_profiles_returns_empty():
    assert student.predict_churn_risk([]) == []
