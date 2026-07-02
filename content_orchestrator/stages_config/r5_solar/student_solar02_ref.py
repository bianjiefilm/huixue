def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _band(humidity):
    if humidity < 35:
        return "dry"
    if humidity <= 70:
        return "normal"
    return "humid"


def _spec_map(station_specs):
    if station_specs is None:
        return {}
    if not isinstance(station_specs, list):
        raise ValueError("station_specs must be a list")
    result = {}
    for spec in station_specs:
        if isinstance(spec, dict) and spec.get("station_id"):
            result[str(spec["station_id"]).strip()] = spec
    return result


def build_weather_features(rows, station_specs=None):
    """把清洗后的光伏读数转换为天气与出力特征。"""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    specs = _spec_map(station_specs)

    features = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("station_id") or not row.get("timestamp"):
            continue
        station_id = str(row["station_id"]).strip()
        irradiance = _num(row.get("irradiance_wm2"))
        module_temp = _num(row.get("module_temp_c"))
        ambient_temp = _num(row.get("ambient_temp_c"))
        humidity = _num(row.get("humidity_pct"))
        power = _num(row.get("power_kw"))
        spec = specs.get(station_id, {})
        capacity = max(_num(spec.get("capacity_kw"), 5.0), 0.1)
        area = max(_num(spec.get("panel_area_m2"), 25.0), 0.1)
        efficiency = max(min(_num(spec.get("efficiency"), 0.18), 0.3), 0.05)

        expected = irradiance / 1000.0 * area * efficiency
        expected = min(expected, capacity)
        perf = power / expected if expected > 0 else 0.0
        cloud_risk = max(0.0, min(1.0, (100.0 - irradiance / 10.0 + humidity - 50.0) / 100.0))

        features.append({
            "station_id": station_id,
            "timestamp": str(row["timestamp"]).strip(),
            "irradiance_kwm2": round(irradiance / 1000.0, 4),
            "temp_delta_c": round(module_temp - ambient_temp, 3),
            "humidity_band": _band(humidity),
            "expected_power_kw": round(expected, 4),
            "performance_ratio": round(perf, 4),
            "heat_stress": module_temp >= 55 or (module_temp - ambient_temp) >= 25,
            "cloud_risk": round(cloud_risk, 4),
        })
    return sorted(features, key=lambda item: (item["station_id"], item["timestamp"]))
