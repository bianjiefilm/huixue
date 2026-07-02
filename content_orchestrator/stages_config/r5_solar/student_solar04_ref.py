def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    if "soiling" in drivers:
        return "schedule_panel_cleaning"
    if "thermal" in drivers:
        return "check_ventilation_and_module_hotspots"
    if "unstable" in drivers:
        return "review_sensor_and_weather_alignment"
    return "continue_monitoring"


def recommend_solar_maintenance(station_features, station_specs=None, max_tasks=3):
    """根据光伏特征识别低效电站并生成维护优先级。"""
    if not isinstance(station_features, list):
        raise ValueError("station_features must be a list")
    if isinstance(max_tasks, bool) or not isinstance(max_tasks, int) or max_tasks <= 0:
        raise ValueError("max_tasks must be a positive integer")
    specs = _specs(station_specs)

    grouped = {}
    for row in station_features:
        if not isinstance(row, dict) or not row.get("station_id"):
            continue
        station_id = str(row["station_id"]).strip()
        if not station_id:
            continue
        grouped.setdefault(station_id, []).append(row)

    plans = []
    for station_id, rows in grouped.items():
        count = len(rows)
        perf_values = [_num(row.get("performance_ratio")) for row in rows]
        cloud_values = [_num(row.get("cloud_risk")) for row in rows]
        heat_count = sum(1 for row in rows if bool(row.get("heat_stress")))
        low_perf_count = sum(1 for value in perf_values if value < 0.72)
        offline_count = sum(1 for row in rows if _num(row.get("expected_power_kw")) >= 1.0 and _num(row.get("performance_ratio")) <= 0.05)
        avg_perf = sum(perf_values) / count if count else 0.0
        avg_cloud = sum(cloud_values) / count if count else 0.0
        low_perf_rate = low_perf_count / count if count else 0.0
        heat_rate = heat_count / count if count else 0.0
        offline_rate = offline_count / count if count else 0.0

        drivers = []
        if offline_rate >= 0.25:
            drivers.append("offline")
        if low_perf_rate >= 0.4 and avg_cloud < 0.7:
            drivers.append("soiling")
        if heat_rate >= 0.3:
            drivers.append("thermal")
        if avg_cloud >= 0.75 and low_perf_rate >= 0.4:
            drivers.append("unstable")
        if not drivers and avg_perf < 0.85:
            drivers.append("monitor")

        risk = (
            (1.0 - min(avg_perf, 1.2) / 1.2) * 0.45
            + low_perf_rate * 0.25
            + heat_rate * 0.15
            + offline_rate * 0.15
        )
        risk = max(0.0, min(1.0, risk))
        spec = specs.get(station_id, {})
        capacity = _num(spec.get("capacity_kw"), 0.0)
        base_hours = 2.0 + 2.0 * len(drivers) + (capacity / 10.0 if capacity else 0.0)
        severity = _severity(risk)
        if severity == "critical":
            base_hours += 4.0
        elif severity == "high":
            base_hours += 2.0

        plans.append({
            "station_id": station_id,
            "site": str(spec.get("site", "UNKNOWN")),
            "avg_performance_ratio": round(avg_perf, 4),
            "low_performance_rate": round(low_perf_rate, 4),
            "heat_stress_rate": round(heat_rate, 4),
            "risk_score": round(risk, 4),
            "severity": severity,
            "priority_action": _action(drivers),
            "drivers": drivers,
            "estimated_hours": round(base_hours, 2),
        })

    plans.sort(key=lambda item: (-item["risk_score"], item["station_id"]))
    limited = []
    for index, plan in enumerate(plans[:max_tasks], start=1):
        item = dict(plan)
        item["priority_rank"] = index
        limited.append(item)
    return limited
