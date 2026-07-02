def clean_solar_readings(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    return [{
        "station_id": "",
        "timestamp": "",
        "irradiance_wm2": 0.0,
        "module_temp_c": 0.0,
        "ambient_temp_c": 0.0,
        "humidity_pct": 0.0,
        "power_kw": 0.0,
        "quality_label": "normal",
    } for _ in rows if isinstance(_, dict)]
