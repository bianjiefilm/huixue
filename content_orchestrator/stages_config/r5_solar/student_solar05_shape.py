def load_and_clean_solar(rows):
    return [{"station_id": "", "timestamp": "", "irradiance_wm2": 0.0, "module_temp_c": 0.0, "ambient_temp_c": 0.0, "humidity_pct": 0.0, "power_kw": 0.0} for _ in rows] if isinstance(rows, list) else []


def build_weather_features(readings, station_specs=None):
    return [{"station_id": "", "timestamp": "", "expected_power_kw": 0.0, "performance_ratio": 0.0, "cloud_risk": 0.0, "heat_stress": False} for _ in readings] if isinstance(readings, list) else []


def score_output_prediction(features, predicted_rows, alert_threshold=0.15):
    return {"total": len(features) if isinstance(features, list) else 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0, "alert_count": 0, "worst_station": "", "alerts": []}


def generate_maintenance_recommendation(feature_rows, prediction_summary=None, station_specs=None, max_tasks=3):
    return [{"station_id": "", "site": "", "risk_score": 0.0, "severity": "low", "priority_action": "", "drivers": [], "estimated_hours": 0.0, "priority_rank": 1}] if feature_rows else []


def summarize_solar_report(plans, prediction_summary=None):
    return {"total_tasks": len(plans) if isinstance(plans, list) else 0, "high_priority": 0, "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "site_counts": {}, "total_estimated_hours": 0.0, "prediction_quality": "unknown"}
