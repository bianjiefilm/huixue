def build_weather_features(rows, station_specs=None):
    return [{
        "station_id": "PV-01",
        "timestamp": "t1",
        "irradiance_kwm2": 0.8,
        "temp_delta_c": 12.0,
        "humidity_band": "normal",
        "expected_power_kw": 3.6,
        "performance_ratio": 1.0,
        "heat_stress": False,
        "cloud_risk": 0.2,
    }]
