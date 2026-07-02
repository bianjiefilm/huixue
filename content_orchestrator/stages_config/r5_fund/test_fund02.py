import importlib
import os

import pytest


MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_fund02")
student = importlib.import_module(MODULE_NAME)


PROFILES = [
    {"customer_id": "C001", "rfm_segment": "high_value_active", "risk_level": "balanced", "main_fund_type": "equity", "marketing_tag": "wealth_upgrade", "aum": 55000},
    {"customer_id": "C002", "rfm_segment": "high_value_watch", "risk_level": "aggressive", "main_fund_type": "index", "marketing_tag": "relationship_reactivation", "aum": 20000},
    {"customer_id": "C003", "rfm_segment": "low_value", "risk_level": "defensive", "main_fund_type": "money_market", "marketing_tag": "stable_income", "aum": 5000},
]

CAMPAIGNS = [
    {"campaign_id": "CP-EQ", "base_score": 0.2, "target_segments": ["high_value_active"], "target_risk_levels": ["balanced", "aggressive"], "fund_types": ["equity"], "preferred_tag": "wealth_upgrade", "min_aum": 30000},
    {"campaign_id": "CP-IDX", "base_score": 0.24, "target_segments": ["high_value_watch", "growth_active"], "target_risk_levels": ["aggressive"], "fund_types": ["index"], "preferred_tag": "relationship_reactivation", "min_aum": 10000},
    {"campaign_id": "CP-MM", "base_score": 0.22, "target_segments": ["low_value"], "target_risk_levels": ["defensive", "conservative"], "fund_types": ["money_market"], "preferred_tag": "stable_income", "min_aum": 0},
]


def test_selects_best_campaigns_and_sorts_by_score():
    result = student.rank_marketing_responses(PROFILES, CAMPAIGNS)
    assert [row["customer_id"] for row in result] == ["C002", "C003", "C001"]
    assert [row["campaign_id"] for row in result] == ["CP-IDX", "CP-MM", "CP-EQ"]


def test_high_value_active_score_details():
    result = student.rank_marketing_responses([PROFILES[0]], CAMPAIGNS)[0]
    assert result == {"customer_id": "C001", "campaign_id": "CP-EQ", "propensity_score": 0.95, "priority": "high", "reason": ["aum_ready", "fund_type_match", "risk_match", "segment_match", "tag_match"]}


def test_high_value_watch_reactivation_score():
    result = student.rank_marketing_responses([PROFILES[1]], CAMPAIGNS)[0]
    assert result["campaign_id"] == "CP-IDX"
    assert result["propensity_score"] == 0.99
    assert result["priority"] == "high"


def test_defensive_customer_gets_stable_income_campaign():
    result = student.rank_marketing_responses([PROFILES[2]], CAMPAIGNS)[0]
    assert result["campaign_id"] == "CP-MM"
    assert result["reason"] == ["aum_ready", "fund_type_match", "risk_match", "segment_match", "tag_match"]


def test_history_non_response_penalty_can_change_score():
    history = [{"customer_id": "C001", "campaign_id": "CP-EQ", "responded": False}]
    result = student.rank_marketing_responses([PROFILES[0]], CAMPAIGNS, history)[0]
    assert result["campaign_id"] == "CP-EQ"
    assert result["propensity_score"] == 0.87


def test_positive_history_lifts_score():
    history = [{"customer_id": "C003", "campaign_id": "CP-OLD", "responded": True}]
    result = student.rank_marketing_responses([PROFILES[2]], CAMPAIGNS, history)[0]
    assert result["propensity_score"] == 1.0


def test_medium_priority_boundary():
    campaigns = [{"campaign_id": "CP-A", "base_score": 0.5, "target_segments": [], "target_risk_levels": [], "fund_types": [], "min_aum": 999999}]
    result = student.rank_marketing_responses([PROFILES[0]], campaigns)[0]
    assert result["priority"] == "medium"


def test_low_priority_for_weak_match():
    campaigns = [{"campaign_id": "CP-A", "base_score": 0.1, "target_segments": [], "target_risk_levels": [], "fund_types": [], "min_aum": 999999}]
    result = student.rank_marketing_responses([PROFILES[0]], campaigns)[0]
    assert result["priority"] == "low"


def test_rejects_non_list_inputs():
    with pytest.raises(ValueError):
        student.rank_marketing_responses({}, CAMPAIGNS)
    with pytest.raises(ValueError):
        student.rank_marketing_responses(PROFILES, {})
    with pytest.raises(ValueError):
        student.rank_marketing_responses(PROFILES, CAMPAIGNS, {})


def test_empty_campaigns_returns_empty():
    assert student.rank_marketing_responses(PROFILES, []) == []


def test_invalid_profiles_and_campaigns_are_ignored():
    result = student.rank_marketing_responses(["bad", {}, PROFILES[0]], ["bad", {}, CAMPAIGNS[0]])
    assert len(result) == 1
    assert result[0]["customer_id"] == "C001"


def test_tie_breaks_by_campaign_id():
    campaigns = [{"campaign_id": "CP-A", "base_score": 0.5}, {"campaign_id": "CP-B", "base_score": 0.5}]
    result = student.rank_marketing_responses([PROFILES[0]], campaigns)[0]
    assert result["campaign_id"] == "CP-B"


def test_score_is_capped_at_one():
    campaign = {"campaign_id": "CP-X", "base_score": 0.9, "target_segments": ["high_value_active"], "target_risk_levels": ["balanced"], "fund_types": ["equity"], "preferred_tag": "wealth_upgrade", "min_aum": 0}
    assert student.rank_marketing_responses([PROFILES[0]], [campaign])[0]["propensity_score"] == 1.0


def test_score_is_floored_at_zero():
    history = [{"customer_id": "C001", "campaign_id": "CP-A", "responded": False} for _ in range(5)]
    result = student.rank_marketing_responses([PROFILES[0]], [{"campaign_id": "CP-A", "base_score": 0.1}], history)[0]
    assert result["propensity_score"] == 0.0


def test_output_has_exact_keys():
    result = student.rank_marketing_responses([PROFILES[0]], [CAMPAIGNS[0]])[0]
    assert set(result) == {"customer_id", "campaign_id", "propensity_score", "priority", "reason"}
