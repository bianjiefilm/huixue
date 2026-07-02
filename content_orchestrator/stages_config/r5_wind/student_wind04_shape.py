def plan_maintenance(alerts, specs, max_daily_tasks=2):
    if not isinstance(alerts, list):
        return []
    return [{
        "turbine_id": "",
        "severity": "",
        "risk_score": 0.0,
        "priority_rank": 0,
        "scheduled_day": 0,
        "site": "",
        "gearbox_model": "",
        "action": "",
        "estimated_hours": 0,
        "reasons": [],
    } for _ in alerts]
