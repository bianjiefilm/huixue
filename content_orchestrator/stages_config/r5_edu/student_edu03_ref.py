def _num(value, default=0.0):
    if isinstance(value, bool): return default
    try: return float(value)
    except (TypeError, ValueError): return default


def predict_academic_risk(students):
    """根据学业画像预测风险等级。"""
    if not isinstance(students, list):
        raise ValueError("students must be a list")
    result = []
    for row in students:
        if not isinstance(row, dict) or not row.get("student_id"):
            continue
        score = _num(row.get("avg_score"))
        completion = _num(row.get("completion_rate"))
        attendance = _num(row.get("attendance_rate"))
        late = _num(row.get("late_submissions"))
        trend = _num(row.get("score_trend"))
        risk_score = 0
        risk_score += max(0, (70 - score) * 0.9)
        risk_score += max(0, (0.8 - completion) * 50)
        risk_score += max(0, (0.85 - attendance) * 40)
        risk_score += min(late, 10) * 2
        risk_score += max(0, -trend) * 1.5
        level = "high" if risk_score >= 45 else "medium" if risk_score >= 22 else "low"
        actions = []
        if score < 60: actions.append("安排基础补学")
        if completion < 0.7: actions.append("跟进任务完成")
        if attendance < 0.8: actions.append("联系辅导员")
        if not actions: actions.append("保持常规观察")
        result.append({"student_id": str(row["student_id"]), "risk_score": round(risk_score, 2), "risk_level": level, "recommended_actions": actions})
    return sorted(result, key=lambda r: (-r["risk_score"], r["student_id"]))
