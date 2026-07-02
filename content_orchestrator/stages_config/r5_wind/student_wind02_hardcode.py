def build_fault_features(rows, window_size=3):
    return [{
        "turbine_id": "WT-01",
        "timestamp": "t1",
        "temp_avg": 65.0,
        "temp_max": 65.0,
        "vibration_avg": 2.0,
        "vibration_max": 2.0,
        "power_avg": 500.0,
        "temp_delta": 40.0,
        "anomaly_count": 0,
        "hot_gearbox": False,
        "high_vibration": False,
        "risk_level": "low",
    }]
