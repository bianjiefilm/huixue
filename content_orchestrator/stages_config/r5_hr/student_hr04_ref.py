def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_performance_reviews(reviews):
    """汇总绩效评分、评级、奖金系数和发展重点。"""
    if not isinstance(reviews, list):
        raise ValueError("reviews must be a list")
    output = []
    seen = set()
    for row in reviews:
        if not isinstance(row, dict) or not row.get("employee_id"):
            continue
        eid = str(row["employee_id"]).strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        goal = _num(row.get("goal_score"), 0)
        competency = _num(row.get("competency_score"), 0)
        values = _num(row.get("values_score"), 0)
        peer = _num(row.get("peer_score"), 0)
        score = round(goal * 0.4 + competency * 0.3 + values * 0.2 + peer * 0.1, 2)
        rating = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
        multiplier = 1.5 if rating == "A" else 1.1 if rating == "B" else 0.7 if rating == "C" else 0.0
        focus = []
        if goal < 75:
            focus.append("goal_execution")
        if competency < 75:
            focus.append("skill_growth")
        if values < 75:
            focus.append("culture_alignment")
        if peer < 75:
            focus.append("collaboration")
        output.append({"employee_id": eid, "performance_score": score, "rating": rating, "bonus_multiplier": multiplier, "development_focus": sorted(focus)})
    return sorted(output, key=lambda item: (-item["performance_score"], item["employee_id"]))
