NUMERIC_FIELDS = (
    "irradiance_wm2",
    "module_temp_c",
    "ambient_temp_c",
    "humidity_pct",
    "power_kw",
)


def _to_float(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    return float(value)


def _valid(row):
    try:
        values = {field: _to_float(row[field]) for field in NUMERIC_FIELDS}
    except (KeyError, TypeError, ValueError):
        return None

    if not row.get("station_id") or not row.get("timestamp"):
        return None
    if values["irradiance_wm2"] < 0 or values["irradiance_wm2"] > 1400:
        return None
    if values["power_kw"] < 0:
        return None
    if values["module_temp_c"] < -40 or values["module_temp_c"] > 95:
        return None
    if values["ambient_temp_c"] < -45 or values["ambient_temp_c"] > 60:
        return None
    if values["humidity_pct"] < 0 or values["humidity_pct"] > 100:
        return None

    station_id = str(row["station_id"]).strip()
    timestamp = str(row["timestamp"]).strip()
    if not station_id or not timestamp:
        return None

    expected_kw = values["irradiance_wm2"] * 0.004
    quality_label = "normal"
    if values["irradiance_wm2"] >= 200 and values["power_kw"] < expected_kw * 0.35:
        quality_label = "underperforming"
    elif values["irradiance_wm2"] < 50 and values["power_kw"] > 20:
        quality_label = "night_anomaly"

    return {
        "station_id": station_id,
        "timestamp": timestamp,
        "irradiance_wm2": round(values["irradiance_wm2"], 3),
        "module_temp_c": round(values["module_temp_c"], 3),
        "ambient_temp_c": round(values["ambient_temp_c"], 3),
        "humidity_pct": round(values["humidity_pct"], 3),
        "power_kw": round(values["power_kw"], 3),
        "quality_label": quality_label,
    }


def clean_solar_readings(rows):
    """清洗光伏出力读数，返回可用于后续特征工程的标准行。"""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")

    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = _valid(row)
        if item is None:
            continue
        key = (item["station_id"], item["timestamp"])
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return sorted(cleaned, key=lambda item: (item["station_id"], item["timestamp"]))
