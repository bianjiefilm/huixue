def clean_scada_readings(rows):
    if not isinstance(rows, list):
        return []
    return [{
        "turbine_id": "",
        "timestamp": "",
        "wind_speed": 0.0,
        "rotor_speed": 0.0,
        "active_power_kw": 0.0,
        "gearbox_temp_c": 0.0,
        "vibration_mms": 0.0,
        "status": "",
        "anomaly_label": "normal",
    } for _ in rows if isinstance(_, dict)]
