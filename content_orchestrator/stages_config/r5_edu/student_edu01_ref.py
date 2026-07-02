def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def summarize_learning_progress(records):
    """返回班级学情统计摘要。"""
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    clean = []
    for row in records:
        if not isinstance(row, dict) or not row.get("student_id"):
            continue
        total = _num(row.get("total_tasks"), None)
        done = _num(row.get("completed_tasks"), None)
        score = _num(row.get("avg_score"), None)
        minutes = _num(row.get("learning_minutes"), 0.0)
        if total is None or done is None or score is None or total <= 0 or done < 0:
            continue
        done = min(done, total)
        completion = done / total
        clean.append({"student_id": str(row["student_id"]), "completion": completion, "score": score, "minutes": max(minutes, 0.0)})
    if not clean:
        return {"student_count": 0, "avg_completion": 0.0, "avg_score": 0.0, "active_students": 0, "at_risk_students": [], "top_students": []}
    avg_completion = sum(r["completion"] for r in clean) / len(clean)
    avg_score = sum(r["score"] for r in clean) / len(clean)
    active = sum(1 for r in clean if r["minutes"] >= 30)
    at_risk = sorted(r["student_id"] for r in clean if r["completion"] < 0.6 or r["score"] < 60)
    top = sorted(clean, key=lambda r: (-r["score"], -r["completion"], r["student_id"]))[:3]
    return {"student_count": len(clean), "avg_completion": round(avg_completion, 4), "avg_score": round(avg_score, 2), "active_students": active, "at_risk_students": at_risk, "top_students": [r["student_id"] for r in top]}
