def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _level(score):
    if score >= 0.75:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _action(level, drivers):
    if level == "critical":
        return "advisor_call_with_retention_offer"
    if "negative_feedback" in drivers:
        return "service_recovery"
    if "inactive" in drivers:
        return "reactivation_campaign"
    if "low_engagement" in drivers:
        return "education_content"
    return "observe"


def predict_churn_risk(profiles, interactions=None):
    """预测基金客户流失风险, 输出挽留优先级。"""
    if not isinstance(profiles, list):
        raise ValueError("profiles must be a list")
    if interactions is not None and not isinstance(interactions, list):
        raise ValueError("interactions must be a list")
    interactions = interactions or []
    interaction_map = {}
    for row in interactions:
        if not isinstance(row, dict) or not row.get("customer_id"):
            continue
        cid = str(row["customer_id"])
        item = interaction_map.setdefault(cid, {"contacts": 0, "clicks": 0, "complaints": 0})
        item["contacts"] += int(_num(row.get("contacts"), 0))
        item["clicks"] += int(_num(row.get("clicks"), 0))
        item["complaints"] += int(_num(row.get("complaints"), 0))
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        cid = str(profile["customer_id"])
        recency = profile.get("last_transaction_days")
        recency = 999 if recency is None else _num(recency, 999)
        aum = _num(profile.get("aum"), 0.0)
        segment = str(profile.get("rfm_segment", "low_value"))
        risk = 0.12
        drivers = []
        if recency > 180:
            risk += 0.35
            drivers.append("inactive")
        elif recency > 90:
            risk += 0.2
            drivers.append("cooling")
        if segment == "high_value_watch":
            risk += 0.18
            drivers.append("high_value_watch")
        elif segment == "low_value":
            risk += 0.1
            drivers.append("low_value")
        if aum >= 50000:
            risk += 0.06
            drivers.append("large_aum")
        metrics = interaction_map.get(cid, {"contacts": 0, "clicks": 0, "complaints": 0})
        if metrics["contacts"] > 0 and metrics["clicks"] == 0:
            risk += 0.14
            drivers.append("low_engagement")
        if metrics["complaints"] > 0:
            risk += 0.22
            drivers.append("negative_feedback")
        if metrics["clicks"] >= 3:
            risk -= 0.12
            drivers.append("recent_interest")
        score = max(0.0, min(1.0, round(risk, 4)))
        level = _level(score)
        output.append({
            "customer_id": cid,
            "churn_risk": score,
            "risk_level": level,
            "drivers": sorted(set(drivers)),
            "retention_action": _action(level, drivers),
        })
    return sorted(output, key=lambda item: (-item["churn_risk"], item["customer_id"]))
