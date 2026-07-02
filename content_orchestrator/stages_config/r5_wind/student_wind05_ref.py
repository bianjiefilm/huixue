def _num(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    return float(value)


def _avg(values):
    return sum(values) / len(values) if values else 0.0


def _severity_rank(level):
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}[level]


def load_and_clean_scada(rows):
    """清洗 SCADA 原始行, 返回可用于预警分析的记录。"""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    required = ("turbine_id", "timestamp", "wind_speed", "active_power_kw", "gearbox_temp_c", "vibration_mms")
    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or any(key not in row for key in required):
            continue
        try:
            item = {
                "turbine_id": str(row["turbine_id"]),
                "timestamp": str(row["timestamp"]),
                "wind_speed": _num(row["wind_speed"]),
                "active_power_kw": _num(row["active_power_kw"]),
                "gearbox_temp_c": _num(row["gearbox_temp_c"]),
                "vibration_mms": _num(row["vibration_mms"]),
                "ambient_temp_c": _num(row.get("ambient_temp_c", 25.0)),
                "status": str(row.get("status", "normal")).strip().upper(),
            }
        except (TypeError, ValueError):
            continue
        if item["wind_speed"] < 0 or item["active_power_kw"] < 0 or item["gearbox_temp_c"] > 120 or item["vibration_mms"] < 0:
            continue
        key = (item["turbine_id"], item["timestamp"])
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return sorted(cleaned, key=lambda item: (item["turbine_id"], item["timestamp"]))


def build_health_features(readings, window_size=3):
    """按机组生成滚动健康特征。"""
    if not isinstance(readings, list):
        raise ValueError("readings must be a list")
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError("window_size must be a positive integer")
    by_turbine = {}
    for row in readings:
        if not isinstance(row, dict):
            continue
        try:
            item = {
                "turbine_id": str(row["turbine_id"]),
                "timestamp": str(row["timestamp"]),
                "gearbox_temp_c": _num(row["gearbox_temp_c"]),
                "vibration_mms": _num(row["vibration_mms"]),
                "active_power_kw": _num(row.get("active_power_kw", 0.0)),
                "ambient_temp_c": _num(row.get("ambient_temp_c", 25.0)),
                "status": str(row.get("status", "NORMAL")).upper(),
            }
        except (KeyError, TypeError, ValueError):
            continue
        by_turbine.setdefault(item["turbine_id"], []).append(item)
    output = []
    for turbine_id in sorted(by_turbine):
        group = sorted(by_turbine[turbine_id], key=lambda item: item["timestamp"])
        for index, item in enumerate(group):
            window = group[max(0, index - window_size + 1):index + 1]
            temps = [r["gearbox_temp_c"] for r in window]
            vibes = [r["vibration_mms"] for r in window]
            powers = [r["active_power_kw"] for r in window]
            anomaly_count = sum(1 for r in window if r["status"] in {"WARNING", "ALERT", "FAULT"})
            output.append({
                "turbine_id": item["turbine_id"],
                "timestamp": item["timestamp"],
                "temp_avg": round(_avg(temps), 3),
                "temp_delta": round(item["gearbox_temp_c"] - item["ambient_temp_c"], 3),
                "vibration_max": round(max(vibes), 3),
                "power_avg": round(_avg(powers), 3),
                "anomaly_count": anomaly_count,
                "hot_flag": item["gearbox_temp_c"] >= 75,
                "vibration_flag": item["vibration_mms"] >= 5,
            })
    return output


def score_fault_risk(features, weights=None):
    """根据健康特征输出故障风险分数和风险等级。"""
    if not isinstance(features, list):
        raise ValueError("features must be a list")
    weights = weights or {"temp": 0.35, "vibration": 0.35, "anomaly": 0.2, "power": 0.1}
    output = []
    for row in features:
        if not isinstance(row, dict):
            continue
        try:
            temp = max(0.0, min(1.0, (_num(row.get("temp_avg", 0)) - 60.0) / 25.0))
            vibe = max(0.0, min(1.0, (_num(row.get("vibration_max", 0)) - 3.0) / 4.0))
            anomaly = max(0.0, min(1.0, _num(row.get("anomaly_count", 0)) / 3.0))
            power = 1.0 if _num(row.get("power_avg", 0)) <= 100 else 0.0
        except (TypeError, ValueError):
            continue
        risk = round(temp * weights["temp"] + vibe * weights["vibration"] + anomaly * weights["anomaly"] + power * weights["power"], 4)
        if row.get("hot_flag") and row.get("vibration_flag"):
            risk = max(risk, 0.82)
        level = "critical" if risk >= 0.8 else "high" if risk >= 0.6 else "medium" if risk >= 0.35 else "low"
        output.append({
            "turbine_id": str(row["turbine_id"]),
            "timestamp": str(row["timestamp"]),
            "risk_score": risk,
            "risk_level": level,
            "drivers": sorted([
                name for name, active in {
                    "temperature": temp >= 0.6 or bool(row.get("hot_flag")),
                    "vibration": vibe >= 0.5 or bool(row.get("vibration_flag")),
                    "anomaly": anomaly > 0,
                    "low_power": power > 0,
                }.items() if active
            ]),
        })
    return sorted(output, key=lambda item: (item["turbine_id"], item["timestamp"]))


def generate_maintenance_plan(risks, specs, max_daily_tasks=2):
    """根据风险结果生成维护排期。"""
    if not isinstance(risks, list) or not isinstance(specs, list):
        raise ValueError("risks and specs must be lists")
    if not isinstance(max_daily_tasks, int) or max_daily_tasks <= 0:
        raise ValueError("max_daily_tasks must be positive")
    spec_map = {str(s.get("turbine_id")): s for s in specs if isinstance(s, dict) and s.get("turbine_id")}
    latest = {}
    for risk in risks:
        if not isinstance(risk, dict) or not risk.get("turbine_id"):
            continue
        turbine_id = str(risk["turbine_id"])
        score = float(risk.get("risk_score", 0))
        level = str(risk.get("risk_level", "low")).lower()
        if level not in {"critical", "high", "medium", "low"}:
            level = "low"
        current = latest.get(turbine_id)
        if current is None or _severity_rank(level) > _severity_rank(current["risk_level"]) or score > current["risk_score"]:
            latest[turbine_id] = {
                "turbine_id": turbine_id,
                "risk_score": round(score, 4),
                "risk_level": level,
                "drivers": sorted(risk.get("drivers", [])),
            }
    ordered = sorted(latest.values(), key=lambda item: (-_severity_rank(item["risk_level"]), -item["risk_score"], item["turbine_id"]))
    plans = []
    for index, item in enumerate(ordered):
        spec = spec_map.get(item["turbine_id"], {})
        hours = {"critical": 8, "high": 6, "medium": 4, "low": 2}[item["risk_level"]]
        plans.append({
            "turbine_id": item["turbine_id"],
            "risk_level": item["risk_level"],
            "risk_score": item["risk_score"],
            "priority_rank": index + 1,
            "scheduled_day": index // max_daily_tasks + 1,
            "site": str(spec.get("site", "UNKNOWN")),
            "action": {
                "critical": "shutdown_and_inspect",
                "high": "field_inspection",
                "medium": "planned_check",
                "low": "monitor",
            }[item["risk_level"]],
            "estimated_hours": hours,
            "drivers": item["drivers"],
        })
    return plans


def summarize_warning_report(plans):
    """汇总维护计划, 返回管理层报告指标。"""
    if not isinstance(plans, list):
        raise ValueError("plans must be a list")
    site_counts = {}
    level_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_hours = 0.0
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        site = str(plan.get("site", "UNKNOWN"))
        level = str(plan.get("risk_level", plan.get("severity", "low"))).lower()
        site_counts[site] = site_counts.get(site, 0) + 1
        if level in level_counts:
            level_counts[level] += 1
        total_hours += float(plan.get("estimated_hours", 0))
    return {
        "total_tasks": sum(site_counts.values()),
        "high_priority": level_counts["critical"] + level_counts["high"],
        "level_counts": level_counts,
        "site_counts": dict(sorted(site_counts.items())),
        "total_estimated_hours": round(total_hours, 2),
    }
