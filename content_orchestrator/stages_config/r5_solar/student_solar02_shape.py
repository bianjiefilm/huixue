def build_weather_features(rows, station_specs=None):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    if station_specs is not None and not isinstance(station_specs, list):
        raise ValueError("station_specs must be a list")
    return [{
        "station_id": "",
        "timestamp": "",
        "irradiance_kwm2": 0.0,
        "temp_delta_c": 0.0,
        "humidity_band": "normal",
        "expected_power_kw": 0.0,
        "performance_ratio": 0.0,
        "heat_stress": False,
        "cloud_risk": 0.0,
    } for row in rows if isinstance(row, dict)]
