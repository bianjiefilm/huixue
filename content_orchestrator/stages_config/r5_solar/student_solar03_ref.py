def _to_float(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    return float(value)


def _key(row):
    return (str(row["station_id"]).strip(), str(row["timestamp"]).strip())


def evaluate_power_predictions(actual_rows, predicted_rows, alert_threshold=0.15):
    """评估光伏出力预测结果，并标出误差超阈值样本。"""
    if not isinstance(actual_rows, list) or not isinstance(predicted_rows, list):
        raise ValueError("actual_rows and predicted_rows must be lists")
    threshold = _to_float(alert_threshold)
    if threshold < 0:
        raise ValueError("alert_threshold must be non-negative")

    actual = {}
    for row in actual_rows:
        if not isinstance(row, dict) or not row.get("station_id") or not row.get("timestamp"):
            continue
        try:
            actual[_key(row)] = _to_float(row["actual_power_kw"])
        except (KeyError, TypeError, ValueError):
            continue

    pairs = []
    for row in predicted_rows:
        if not isinstance(row, dict) or not row.get("station_id") or not row.get("timestamp"):
            continue
        key = _key(row)
        if key not in actual:
            continue
        try:
            pred = _to_float(row["predicted_power_kw"])
        except (KeyError, TypeError, ValueError):
            continue
        act = actual[key]
        abs_error = abs(pred - act)
        denom = abs(act) if abs(act) > 1e-9 else 1.0
        rel_error = abs_error / denom
        pairs.append({
            "station_id": key[0],
            "timestamp": key[1],
            "actual_power_kw": round(act, 4),
            "predicted_power_kw": round(pred, 4),
            "abs_error": round(abs_error, 4),
            "relative_error": round(rel_error, 4),
        })

    pairs.sort(key=lambda item: (item["station_id"], item["timestamp"]))
    n = len(pairs)
    if n == 0:
        return {
            "sample_count": 0,
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "r2": 0.0,
            "alert_count": 0,
            "alerts": [],
            "worst_point": None,
        }

    errors = [item["abs_error"] for item in pairs]
    rels = [item["relative_error"] for item in pairs]
    actual_values = [item["actual_power_kw"] for item in pairs]
    mae = sum(errors) / n
    rmse = (sum(error * error for error in errors) / n) ** 0.5
    mean_actual = sum(actual_values) / n
    ss_tot = sum((value - mean_actual) ** 2 for value in actual_values)
    ss_res = sum((item["predicted_power_kw"] - item["actual_power_kw"]) ** 2 for item in pairs)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else (1.0 if ss_res == 0 else 0.0)
    alerts = [
        {
            "station_id": item["station_id"],
            "timestamp": item["timestamp"],
            "relative_error": item["relative_error"],
            "abs_error": item["abs_error"],
        }
        for item in pairs
        if item["relative_error"] > threshold
    ]
    worst = max(pairs, key=lambda item: (item["relative_error"], item["abs_error"], item["station_id"], item["timestamp"]))
    return {
        "sample_count": n,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(sum(rels) / n, 4),
        "r2": round(r2, 4),
        "alert_count": len(alerts),
        "alerts": alerts,
        "worst_point": {
            "station_id": worst["station_id"],
            "timestamp": worst["timestamp"],
            "relative_error": worst["relative_error"],
            "abs_error": worst["abs_error"],
        },
    }
