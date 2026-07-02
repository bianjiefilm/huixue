def predict_churn_risk(profiles, interactions=None):
    if not isinstance(profiles, list):
        return []
    return [{"customer_id": "", "churn_risk": 0.0, "risk_level": "low", "drivers": [], "retention_action": "observe"} for _ in profiles]
