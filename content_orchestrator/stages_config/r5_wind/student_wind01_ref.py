def clean_scada_readings(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")

    required = [
        "turbine_id",
        "timestamp",
        "wind_speed",
        "rotor_speed",
        "active_power_kw",
        "gearbox_temp_c",
        "vibration_mms",
    ]
    seen = set()
    cleaned = []

    for item in rows:
        if not isinstance(item, dict):
            continue
        if any(key not in item or item[key] in (None, "") for key in required):
            continue

        try:
            wind_speed = float(item["wind_speed"])
            rotor_speed = float(item["rotor_speed"])
            active_power = float(item["active_power_kw"])
            gearbox_temp = float(item["gearbox_temp_c"])
            vibration = float(item["vibration_mms"])
        except (TypeError, ValueError):
            continue

        if not (0 <= wind_speed <= 35):
            continue
        if not (0 <= rotor_speed <= 30):
            continue
        if active_power < 0:
            continue
        if not (-40 <= gearbox_temp <= 130):
            continue
        if not (0 <= vibration <= 50):
            continue

        turbine_id = str(item["turbine_id"])
        timestamp = str(item["timestamp"])
        key = (turbine_id, timestamp)
        if key in seen:
            continue
        seen.add(key)

        cleaned.append({
            "turbine_id": turbine_id,
            "timestamp": timestamp,
            "wind_speed": wind_speed,
            "rotor_speed": rotor_speed,
            "active_power_kw": active_power,
            "gearbox_temp_c": gearbox_temp,
            "vibration_mms": vibration,
            "status": str(item.get("status", "OK")).upper(),
            "anomaly_label": "gearbox_hot" if gearbox_temp >= 95 or vibration >= 12 else "normal",
        })

    return sorted(cleaned, key=lambda row: (row["turbine_id"], row["timestamp"]))
