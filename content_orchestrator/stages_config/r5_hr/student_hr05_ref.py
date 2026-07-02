STAGES = ["applied", "screen", "interview", "offer", "hired"]


def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _median(values):
    vals = sorted(values)
    if not vals:
        return 0.0
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def analyze_salary_structure(employees):
    if not isinstance(employees, list):
        raise ValueError("employees must be a list")
    buckets = {}
    for row in employees:
        if not isinstance(row, dict) or not row.get("department"):
            continue
        salary = _num(row.get("salary"), None)
        dept = str(row["department"]).strip()
        if salary is None or salary <= 0 or not dept:
            continue
        buckets.setdefault(dept, []).append(salary)
    output = []
    for dept, salaries in buckets.items():
        avg, med = sum(salaries) / len(salaries), _median(salaries)
        output.append({"department": dept, "employee_count": len(salaries), "avg_salary": round(avg, 2), "median_salary": round(med, 2), "pay_gap": round(0.0 if med == 0 else (max(salaries) - min(salaries)) / med, 4), "salary_band": "high" if avg >= 30000 else "medium" if avg >= 18000 else "low"})
    return sorted(output, key=lambda item: (-item["avg_salary"], item["department"]))


def analyze_recruiting_funnel(candidates):
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    buckets = {}
    for row in candidates:
        if not isinstance(row, dict) or not row.get("role"):
            continue
        role, stage = str(row["role"]).strip(), str(row.get("stage", "")).strip()
        if not role or stage not in STAGES:
            continue
        counts = buckets.setdefault(role, {name: 0 for name in STAGES})
        for name in STAGES[: STAGES.index(stage) + 1]:
            counts[name] += 1
    output = []
    for role, c in buckets.items():
        rates = {"screen_rate": 0.0 if c["applied"] == 0 else c["screen"] / c["applied"], "interview_rate": 0.0 if c["screen"] == 0 else c["interview"] / c["screen"], "offer_rate": 0.0 if c["interview"] == 0 else c["offer"] / c["interview"], "hire_rate": 0.0 if c["offer"] == 0 else c["hired"] / c["offer"]}
        order = {"screen_rate": 0, "interview_rate": 1, "offer_rate": 2, "hire_rate": 3}
        output.append({"role": role, "applied": c["applied"], **{k: round(v, 4) for k, v in rates.items()}, "bottleneck": min(rates.items(), key=lambda item: (item[1], order[item[0]]))[0].replace("_rate", "")})
    return sorted(output, key=lambda item: (-item["applied"], item["role"]))


def predict_attrition_risk(employees, engagement=None):
    if not isinstance(employees, list):
        raise ValueError("employees must be a list")
    if engagement is not None and not isinstance(engagement, list):
        raise ValueError("engagement must be a list")
    eng = {str(row.get("employee_id")): row for row in (engagement or []) if isinstance(row, dict) and row.get("employee_id")}
    output, seen = [], set()
    for row in employees:
        if not isinstance(row, dict) or not row.get("employee_id"):
            continue
        eid = str(row["employee_id"]).strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        score, drivers = 0.12, []
        checks = [("new_hire", _num(row.get("tenure_months")) < 6, 0.18), ("below_market_pay", _num(row.get("salary_market_ratio"), 1) < 0.9, 0.22), ("high_overtime", _num(row.get("overtime_hours")) >= 45, 0.2), ("promotion_stagnation", _num(row.get("months_since_promotion")) >= 24, 0.16)]
        e = eng.get(eid, {})
        checks += [("low_engagement", _num(e.get("engagement_score"), 100) < 60, 0.22), ("manager_risk", _num(e.get("manager_score"), 100) < 60, 0.14)]
        for name, matched, weight in checks:
            if matched:
                score += weight; drivers.append(name)
        score = min(1.0, round(score, 4))
        level = "critical" if score >= 0.75 else "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
        action = "executive_retention_plan" if level == "critical" else "manager_intervention" if "manager_risk" in drivers else "compensation_review" if "below_market_pay" in drivers else "career_conversation" if "promotion_stagnation" in drivers else "observe"
        output.append({"employee_id": eid, "attrition_score": score, "risk_level": level, "drivers": sorted(drivers), "retention_action": action})
    return sorted(output, key=lambda item: (-item["attrition_score"], item["employee_id"]))


def evaluate_performance_reviews(reviews):
    if not isinstance(reviews, list):
        raise ValueError("reviews must be a list")
    output, seen = [], set()
    for row in reviews:
        if not isinstance(row, dict) or not row.get("employee_id"):
            continue
        eid = str(row["employee_id"]).strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        score = round(_num(row.get("goal_score")) * 0.4 + _num(row.get("competency_score")) * 0.3 + _num(row.get("values_score")) * 0.2 + _num(row.get("peer_score")) * 0.1, 2)
        rating = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
        focus = []
        for key, name in [("goal_score", "goal_execution"), ("competency_score", "skill_growth"), ("values_score", "culture_alignment"), ("peer_score", "collaboration")]:
            if _num(row.get(key)) < 75:
                focus.append(name)
        output.append({"employee_id": eid, "performance_score": score, "rating": rating, "bonus_multiplier": 1.5 if rating == "A" else 1.1 if rating == "B" else 0.7 if rating == "C" else 0.0, "development_focus": sorted(focus)})
    return sorted(output, key=lambda item: (-item["performance_score"], item["employee_id"]))


def summarize_hr_report(salary, funnel, attrition, performance):
    if not all(isinstance(value, list) for value in (salary, funnel, attrition, performance)):
        raise ValueError("all inputs must be lists")
    return {"departments": len([x for x in salary if isinstance(x, dict)]), "high_salary_departments": sum(1 for x in salary if isinstance(x, dict) and x.get("salary_band") == "high"), "open_roles": len([x for x in funnel if isinstance(x, dict)]), "critical_attrition": sum(1 for x in attrition if isinstance(x, dict) and x.get("risk_level") == "critical"), "a_players": sum(1 for x in performance if isinstance(x, dict) and x.get("rating") == "A"), "overall_status": "retention_emergency" if any(isinstance(x, dict) and x.get("risk_level") == "critical" for x in attrition) else "talent_growth_ready" if any(isinstance(x, dict) and x.get("rating") == "A" for x in performance) else "stable"}
