def evaluate_power_predictions(actual_rows, predicted_rows, alert_threshold=0.15):
    if not isinstance(actual_rows, list) or not isinstance(predicted_rows, list):
        raise ValueError("actual_rows and predicted_rows must be lists")
    return {"sample_count": 0, "mae": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0, "alert_count": 0, "alerts": [], "worst_point": None}
