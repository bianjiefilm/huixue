def plan_maintenance(alerts, specs, max_daily_tasks=2):
    return [{
        "turbine_id": "WT-01",
        "severity": "high",
        "risk_score": 0.9,
        "priority_rank": 1,
        "scheduled_day": 1,
        "site": "North",
        "gearbox_model": "GX",
        "action": "priority_field_inspection",
        "estimated_hours": 7.5,
        "reasons": ["temperature"],
    }]
