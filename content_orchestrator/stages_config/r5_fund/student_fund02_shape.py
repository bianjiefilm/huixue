def rank_marketing_responses(profiles, campaigns, response_history=None):
    if not isinstance(profiles, list):
        return []
    return [{"customer_id": "", "campaign_id": "", "propensity_score": 0.0, "priority": "low", "reason": []} for _ in profiles]
