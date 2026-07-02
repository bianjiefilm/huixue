def load_and_clean_solar(rows):
    return []


def build_weather_features(readings, station_specs=None):
    return []


def score_output_prediction(features, predicted_rows, alert_threshold=0.15):
    return {"total": 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0, "alert_count": 0, "worst_station": None, "alerts": []}


def generate_maintenance_recommendation(feature_rows, prediction_summary=None, station_specs=None, max_tasks=3):
    return []


def summarize_solar_report(plans, prediction_summary=None):
    return {"total_tasks": 0, "high_priority": 0, "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "site_counts": {}, "total_estimated_hours": 0.0, "prediction_quality": "unknown"}
