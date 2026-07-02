def _num(value, default=None):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values):
    return sum(values) / len(values) if values else 0.0


def _specs(station_specs):
    if station_specs is None:
        return {}
    if not isinstance(station_specs, list):
        raise ValueError("station_specs must be a list")
    result = {}
    for spec in station_specs:
        if isinstance(spec, dict) and spec.get("station_id"):
            result[str(spec["station_id"]).strip()] = spec
    return result


def _severity(score):
    if score >= 0.75:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _action(drivers):
    if "offline" in drivers:
        return "inspect_inverter_and_grid_connection"
    if "prediction_alert" in drivers:
        return "review_forecast_and_sensor_pipeline"
    if "soiling" in drivers:
        return "schedule_panel_cleaning"
    if "thermal" in drivers:
        return "check_ventilation_and_module_hotspots"
    if "unstable" in drivers:
        return "review_weather_alignment"
    return "continue_monitoring"


def load_and_clean_solar(rows):
    """清洗光伏出力原始行, 返回端到端预测系统可复用的记录。"""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    required = ("station_id", "timestamp", "irradiance_wm2", "module_temp_c", "ambient_temp_c", "humidity_pct", "power_kw")
    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or any(key not in row for key in required):
            continue
        station_id = str(row["station_id"]).strip()
        timestamp = str(row["timestamp"]).strip()
        values = {key: _num(row[key]) for key in required[2:]}
        if not station_id or not timestamp or any(value is None for value in values.values()):
            continue
        if values["irradiance_wm2"] < 0 or values["irradiance_wm2"] > 1400:
            continue
        if values["module_temp_c"] < -40 or values["module_temp_c"] > 95:
            continue
        if values["ambient_temp_c"] < -40 or values["ambient_temp_c"] > 60:
            continue
        if values["humidity_pct"] < 0 or values["humidity_pct"] > 100:
            continue
        if values["power_kw"] < 0:
            continue
        key = (station_id, timestamp)
        if key in seen:
            continue
        seen.add(key)
        item = {"station_id": station_id, "timestamp": timestamp}
        item.update({key: round(value, 4) for key, value in values.items()})
        cleaned.append(item)
    return sorted(cleaned, key=lambda item: (item["station_id"], item["timestamp"]))


def build_weather_features(readings, station_specs=None):
    """根据清洗后的光伏读数生成天气与出力特征。"""
    if not isinstance(readings, list):
        raise ValueError("readings must be a list")
    specs = _specs(station_specs)
    output = []
    for row in readings:
        if not isinstance(row, dict) or not row.get("station_id"):
            continue
        try:
            station_id = str(row["station_id"]).strip()
            irradiance = _num(row["irradiance_wm2"])
            module_temp = _num(row["module_temp_c"])
            ambient_temp = _num(row["ambient_temp_c"])
            humidity = _num(row["humidity_pct"])
            power = _num(row["power_kw"])
        except KeyError:
            continue
        if None in {irradiance, module_temp, ambient_temp, humidity, power}:
            continue
        capacity = _num(specs.get(station_id, {}).get("capacity_kw"), 10.0) or 10.0
        expected = max(0.0, capacity * min(irradiance, 1000.0) / 1000.0 * (1.0 - max(module_temp - 25.0, 0.0) * 0.004))
        ratio = power / expected if expected > 0 else 0.0
        output.append({
            "station_id": station_id,
            "timestamp": str(row["timestamp"]),
            "expected_power_kw": round(expected, 4),
            "actual_power_kw": round(power, 4),
            "performance_ratio": round(ratio, 4),
            "cloud_risk": round(max(0.0, min(1.0, (humidity - 45.0) / 55.0 + (600.0 - irradiance) / 1500.0)), 4),
            "heat_stress": module_temp - ambient_temp >= 22.0 or module_temp >= 62.0,
            "temperature_delta": round(module_temp - ambient_temp, 4),
        })
    return sorted(output, key=lambda item: (item["station_id"], item["timestamp"]))


def score_output_prediction(features, predicted_rows, alert_threshold=0.15):
    """评估出力预测结果, 返回误差指标和告警明细。"""
    if not isinstance(features, list) or not isinstance(predicted_rows, list):
        raise ValueError("features and predicted_rows must be lists")
    threshold = _num(alert_threshold)
    if threshold is None or threshold <= 0:
        raise ValueError("alert_threshold must be positive")
    actual_map = {}
    for row in features:
        if isinstance(row, dict) and row.get("station_id") and row.get("timestamp"):
            actual = _num(row.get("actual_power_kw"))
            expected = _num(row.get("expected_power_kw"), 0.0) or 0.0
            if actual is not None:
                actual_map[(str(row["station_id"]), str(row["timestamp"]))] = (actual, expected)
    errors = []
    alerts = []
    for row in predicted_rows:
        if not isinstance(row, dict):
            continue
        key = (str(row.get("station_id")), str(row.get("timestamp")))
        pred = _num(row.get("predicted_power_kw"))
        if key not in actual_map or pred is None:
            continue
        actual, expected = actual_map[key]
        abs_error = abs(pred - actual)
        denom = max(expected, actual, 1.0)
        rel_error = abs_error / denom
        errors.append((key, actual, pred, abs_error, rel_error))
        if rel_error >= threshold:
            alerts.append({
                "station_id": key[0],
                "timestamp": key[1],
                "actual_power_kw": round(actual, 4),
                "predicted_power_kw": round(pred, 4),
                "relative_error": round(rel_error, 4),
            })
    if not errors:
        return {"total": 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0, "alert_count": 0, "worst_station": None, "alerts": []}
    actuals = [item[1] for item in errors]
    mae = _avg([item[3] for item in errors])
    rmse = (_avg([item[3] ** 2 for item in errors])) ** 0.5
    mean_actual = _avg(actuals)
    ss_tot = sum((value - mean_actual) ** 2 for value in actuals)
    ss_res = sum((item[2] - item[1]) ** 2 for item in errors)
    r2 = 1.0 if ss_tot == 0 and ss_res == 0 else 0.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    worst = max(errors, key=lambda item: (item[4], item[0][0], item[0][1]))
    return {
        "total": len(errors),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "alert_count": len(alerts),
        "worst_station": worst[0][0],
        "alerts": sorted(alerts, key=lambda item: (item["station_id"], item["timestamp"])),
    }


def generate_maintenance_recommendation(feature_rows, prediction_summary=None, station_specs=None, max_tasks=3):
    """结合天气特征和预测告警生成光伏维护建议。"""
    if not isinstance(feature_rows, list):
        raise ValueError("feature_rows must be a list")
    if isinstance(max_tasks, bool) or not isinstance(max_tasks, int) or max_tasks <= 0:
        raise ValueError("max_tasks must be a positive integer")
    specs = _specs(station_specs)
    alert_stations = set()
    if isinstance(prediction_summary, dict):
        alert_stations = {str(row.get("station_id")) for row in prediction_summary.get("alerts", []) if isinstance(row, dict)}
    grouped = {}
    for row in feature_rows:
        if isinstance(row, dict) and row.get("station_id"):
            grouped.setdefault(str(row["station_id"]).strip(), []).append(row)
    plans = []
    for station_id, rows in grouped.items():
        ratios = [_num(row.get("performance_ratio"), 0.0) or 0.0 for row in rows]
        clouds = [_num(row.get("cloud_risk"), 0.0) or 0.0 for row in rows]
        expected = [_num(row.get("expected_power_kw"), 0.0) or 0.0 for row in rows]
        heat_rate = sum(1 for row in rows if bool(row.get("heat_stress"))) / len(rows)
        low_perf_rate = sum(1 for value in ratios if value < 0.72) / len(rows)
        offline_rate = sum(1 for value, exp in zip(ratios, expected) if exp >= 1.0 and value <= 0.05) / len(rows)
        avg_perf = _avg(ratios)
        avg_cloud = _avg(clouds)
        drivers = []
        if offline_rate >= 0.25:
            drivers.append("offline")
        if low_perf_rate >= 0.4 and avg_cloud < 0.7:
            drivers.append("soiling")
        if heat_rate >= 0.3:
            drivers.append("thermal")
        if avg_cloud >= 0.75 and low_perf_rate >= 0.4:
            drivers.append("unstable")
        if station_id in alert_stations:
            drivers.append("prediction_alert")
        if not drivers and avg_perf < 0.85:
            drivers.append("monitor")
        risk = (1.0 - min(avg_perf, 1.2) / 1.2) * 0.35 + low_perf_rate * 0.22 + heat_rate * 0.13 + offline_rate * 0.18 + (0.12 if station_id in alert_stations else 0.0)
        risk = max(0.0, min(1.0, risk))
        spec = specs.get(station_id, {})
        severity = _severity(risk)
        hours = 2.0 + len(drivers) * 1.8 + (_num(spec.get("capacity_kw"), 0.0) or 0.0) / 12.0
        if severity == "critical":
            hours += 4.0
        elif severity == "high":
            hours += 2.0
        plans.append({
            "station_id": station_id,
            "site": str(spec.get("site", "UNKNOWN")),
            "risk_score": round(risk, 4),
            "severity": severity,
            "priority_action": _action(drivers),
            "drivers": drivers,
            "estimated_hours": round(hours, 2),
        })
    ordered = sorted(plans, key=lambda item: (-item["risk_score"], item["station_id"]))[:max_tasks]
    for index, plan in enumerate(ordered, start=1):
        plan["priority_rank"] = index
    return ordered


def summarize_solar_report(plans, prediction_summary=None):
    """汇总预测质量和维护排期, 返回管理报告。"""
    if not isinstance(plans, list):
        raise ValueError("plans must be a list")
    level_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    site_counts = {}
    total_hours = 0.0
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        site = str(plan.get("site", "UNKNOWN"))
        severity = str(plan.get("severity", "low")).lower()
        site_counts[site] = site_counts.get(site, 0) + 1
        if severity in level_counts:
            level_counts[severity] += 1
        total_hours += _num(plan.get("estimated_hours"), 0.0) or 0.0
    r2 = _num(prediction_summary.get("r2") if isinstance(prediction_summary, dict) else None, None)
    quality = "unknown" if r2 is None else "good" if r2 >= 0.85 else "watch" if r2 >= 0.6 else "poor"
    return {
        "total_tasks": sum(site_counts.values()),
        "high_priority": level_counts["critical"] + level_counts["high"],
        "severity_counts": level_counts,
        "site_counts": dict(sorted(site_counts.items())),
        "total_estimated_hours": round(total_hours, 2),
        "prediction_quality": quality,
    }
