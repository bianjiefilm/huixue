SEVERITY_SCORE = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _severity(value):
    text = str(value).strip().lower()
    if text not in SEVERITY_SCORE:
        raise ValueError("unknown severity")
    return text


def _to_score(value):
    if isinstance(value, bool):
        return 0.0
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, score))


def _action(severity):
    return {
        "critical": "immediate_shutdown_inspection",
        "high": "priority_field_inspection",
        "medium": "scheduled_condition_check",
        "low": "monitor_next_cycle",
    }[severity]


def _hours(severity, spec):
    base = {"critical": 8, "high": 6, "medium": 4, "low": 2}[severity]
    multiplier = 1.25 if str(spec.get("gearbox_model", "")).upper().endswith("X") else 1.0
    return round(base * multiplier, 2)


def plan_maintenance(alerts, specs, max_daily_tasks=2):
    """根据告警严重度和机组信息生成维护排期。"""
    if not isinstance(alerts, list) or not isinstance(specs, list):
        raise ValueError("alerts and specs must be lists")
    if not isinstance(max_daily_tasks, int) or max_daily_tasks <= 0:
        raise ValueError("max_daily_tasks must be a positive integer")

    spec_map = {
        str(item.get("turbine_id")): item
        for item in specs
        if isinstance(item, dict) and item.get("turbine_id") is not None
    }

    merged = {}
    for alert in alerts:
        if not isinstance(alert, dict) or not alert.get("turbine_id") or not alert.get("severity"):
            continue
        severity = _severity(alert.get("severity"))
        turbine_id = str(alert["turbine_id"])
        risk_score = _to_score(alert.get("risk_score", 0))
        detected_at = str(alert.get("detected_at", ""))
        reason = str(alert.get("reason", severity)).strip() or severity
        current = merged.get(turbine_id)
        candidate = {
            "turbine_id": turbine_id,
            "severity": severity,
            "risk_score": risk_score,
            "detected_at": detected_at,
            "reasons": {reason},
        }
        if current is None:
            merged[turbine_id] = candidate
            continue
        current["reasons"].add(reason)
        if (
            SEVERITY_SCORE[severity] > SEVERITY_SCORE[current["severity"]]
            or (SEVERITY_SCORE[severity] == SEVERITY_SCORE[current["severity"]] and risk_score > current["risk_score"])
        ):
            current["severity"] = severity
            current["risk_score"] = risk_score
            current["detected_at"] = detected_at
        elif risk_score > current["risk_score"]:
            current["risk_score"] = risk_score

    ordered = sorted(
        merged.values(),
        key=lambda item: (
            -SEVERITY_SCORE[item["severity"]],
            -item["risk_score"],
            item["detected_at"],
            item["turbine_id"],
        ),
    )

    plans = []
    for index, item in enumerate(ordered):
        spec = spec_map.get(item["turbine_id"], {})
        severity = item["severity"]
        plans.append({
            "turbine_id": item["turbine_id"],
            "severity": severity,
            "risk_score": round(item["risk_score"], 4),
            "priority_rank": index + 1,
            "scheduled_day": index // max_daily_tasks + 1,
            "site": str(spec.get("site", "UNKNOWN")),
            "gearbox_model": str(spec.get("gearbox_model", "UNKNOWN")),
            "action": _action(severity),
            "estimated_hours": _hours(severity, spec),
            "reasons": sorted(item["reasons"]),
        })
    return plans
