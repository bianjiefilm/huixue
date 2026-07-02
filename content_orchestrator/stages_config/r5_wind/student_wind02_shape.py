def build_fault_features(rows, window_size=3):
    if not isinstance(rows, list):
        return []
    return [{
        "turbine_id": "",
        "timestamp": "",
        "temp_avg": 0,
        "temp_max": 0,
        "vibration_avg": 0,
        "vibration_max": 0,
        "power_avg": 0,
        "temp_delta": 0,
        "anomaly_count": 0,
        "hot_gearbox": False,
        "high_vibration": False,
        "risk_level": "",
    } for _ in rows]
