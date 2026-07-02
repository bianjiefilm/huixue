def predict_attrition_risk(employees, engagement=None):
    if not isinstance(employees, list):
        return []
    return [{"employee_id": "", "attrition_score": 0.0, "risk_level": "low", "drivers": [], "retention_action": "observe"} for _ in employees]
