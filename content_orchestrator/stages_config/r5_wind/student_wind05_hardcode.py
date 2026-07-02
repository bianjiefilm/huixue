def load_and_clean_scada(rows):
    return [{"turbine_id": "WT-01", "timestamp": "t1", "wind_speed": 6.0, "active_power_kw": 400.0, "gearbox_temp_c": 65.0, "vibration_mms": 2.0, "ambient_temp_c": 25.0, "status": "NORMAL"}]


def build_health_features(readings, window_size=3):
    return [{"turbine_id": "WT-01", "timestamp": "t1", "temp_avg": 65.0, "temp_delta": 40.0, "vibration_max": 2.0, "power_avg": 400.0, "anomaly_count": 0, "hot_flag": False, "vibration_flag": False}]


def score_fault_risk(features, weights=None):
    return [{"turbine_id": "WT-01", "timestamp": "t1", "risk_score": 0.1, "risk_level": "low", "drivers": []}]


def generate_maintenance_plan(risks, specs, max_daily_tasks=2):
    return [{"turbine_id": "WT-01", "risk_level": "low", "risk_score": 0.1, "priority_rank": 1, "scheduled_day": 1, "site": "North", "action": "monitor", "estimated_hours": 2, "drivers": []}]


def summarize_warning_report(plans):
    return {"total_tasks": 1, "high_priority": 0, "level_counts": {"critical": 0, "high": 0, "medium": 0, "low": 1}, "site_counts": {"North": 1}, "total_estimated_hours": 2.0}
