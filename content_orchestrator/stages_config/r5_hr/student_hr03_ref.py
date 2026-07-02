def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def predict_attrition_risk(employees, engagement=None):
    """预测员工离职风险并给出留才动作。"""
    if not isinstance(employees, list):
        raise ValueError("employees must be a list")
    if engagement is not None and not isinstance(engagement, list):
        raise ValueError("engagement must be a list")
    eng = {str(row.get("employee_id")): row for row in (engagement or []) if isinstance(row, dict) and row.get("employee_id")}
    output = []
    seen = set()
    for row in employees:
        if not isinstance(row, dict) or not row.get("employee_id"):
            continue
        eid = str(row["employee_id"]).strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        score, drivers = 0.12, []
        tenure = _num(row.get("tenure_months"), 0)
        salary_ratio = _num(row.get("salary_market_ratio"), 1)
        overtime = _num(row.get("overtime_hours"), 0)
        promotion_gap = _num(row.get("months_since_promotion"), 0)
        if tenure < 6:
            score += 0.18; drivers.append("new_hire")
        if salary_ratio < 0.9:
            score += 0.22; drivers.append("below_market_pay")
        if overtime >= 45:
            score += 0.2; drivers.append("high_overtime")
        if promotion_gap >= 24:
            score += 0.16; drivers.append("promotion_stagnation")
        e = eng.get(eid, {})
        if _num(e.get("engagement_score"), 100) < 60:
            score += 0.22; drivers.append("low_engagement")
        if _num(e.get("manager_score"), 100) < 60:
            score += 0.14; drivers.append("manager_risk")
        score = max(0.0, min(1.0, round(score, 4)))
        level = "critical" if score >= 0.75 else "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
        action = "executive_retention_plan" if level == "critical" else "manager_intervention" if "manager_risk" in drivers else "compensation_review" if "below_market_pay" in drivers else "career_conversation" if "promotion_stagnation" in drivers else "observe"
        output.append({"employee_id": eid, "attrition_score": score, "risk_level": level, "drivers": sorted(drivers), "retention_action": action})
    return sorted(output, key=lambda item: (-item["attrition_score"], item["employee_id"]))
