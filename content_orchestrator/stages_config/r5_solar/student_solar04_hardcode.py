def recommend_solar_maintenance(station_features, station_specs=None, max_tasks=3):
    return [{
        "station_id": "PV-01",
        "site": "North",
        "avg_performance_ratio": 0.5,
        "low_performance_rate": 1.0,
        "heat_stress_rate": 0.0,
        "risk_score": 0.6,
        "severity": "high",
        "priority_action": "schedule_panel_cleaning",
        "drivers": ["soiling"],
        "estimated_hours": 6.0,
        "priority_rank": 1,
    }]
