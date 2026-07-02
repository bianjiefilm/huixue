def _to_float(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    return float(value)


def _is_anomaly(row):
    label = str(row.get("anomaly_label", "")).strip().lower()
    status = str(row.get("status", "")).strip().lower()
    return label in {"1", "true", "fault", "warning", "anomaly", "alert"} or status in {"fault", "warning", "anomaly", "alert"}


def _risk_level(hot, high_vibration, anomaly_count):
    if (hot and high_vibration) or anomaly_count >= 2:
        return "high"
    if hot or high_vibration or anomaly_count == 1:
        return "medium"
    return "low"


def build_fault_features(rows, window_size=3):
    """按机组生成温度、振动、功率相关的故障特征。"""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError("window_size must be a positive integer")

    cleaned = []
    required = ("turbine_id", "timestamp", "gearbox_temp_c", "ambient_temp_c", "vibration_mms", "active_power_kw")
    for row in rows:
        if not isinstance(row, dict) or any(key not in row for key in required):
            continue
        try:
            item = {
                "turbine_id": str(row["turbine_id"]),
                "timestamp": str(row["timestamp"]),
                "gearbox_temp_c": _to_float(row["gearbox_temp_c"]),
                "ambient_temp_c": _to_float(row["ambient_temp_c"]),
                "vibration_mms": _to_float(row["vibration_mms"]),
                "active_power_kw": _to_float(row["active_power_kw"]),
                "is_anomaly": _is_anomaly(row),
            }
        except (TypeError, ValueError):
            continue
        cleaned.append(item)

    cleaned.sort(key=lambda item: (item["turbine_id"], item["timestamp"]))
    by_turbine = {}
    for item in cleaned:
        by_turbine.setdefault(item["turbine_id"], []).append(item)

    output = []
    for turbine_id in sorted(by_turbine):
        group = by_turbine[turbine_id]
        for index, item in enumerate(group):
            window = group[max(0, index - window_size + 1):index + 1]
            temps = [r["gearbox_temp_c"] for r in window]
            vibrations = [r["vibration_mms"] for r in window]
            powers = [r["active_power_kw"] for r in window]
            anomaly_count = sum(1 for r in window if r["is_anomaly"])
            hot = item["gearbox_temp_c"] >= 75.0
            high_vibration = item["vibration_mms"] >= 5.0
            output.append({
                "turbine_id": item["turbine_id"],
                "timestamp": item["timestamp"],
                "temp_avg": round(sum(temps) / len(temps), 3),
                "temp_max": round(max(temps), 3),
                "vibration_avg": round(sum(vibrations) / len(vibrations), 3),
                "vibration_max": round(max(vibrations), 3),
                "power_avg": round(sum(powers) / len(powers), 3),
                "temp_delta": round(item["gearbox_temp_c"] - item["ambient_temp_c"], 3),
                "anomaly_count": anomaly_count,
                "hot_gearbox": hot,
                "high_vibration": high_vibration,
                "risk_level": _risk_level(hot, high_vibration, anomaly_count),
            })
    return output
