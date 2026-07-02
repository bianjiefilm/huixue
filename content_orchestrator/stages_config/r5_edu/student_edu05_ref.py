def _num(value, default=0.0):
    if isinstance(value, bool): return default
    try: return float(value)
    except (TypeError, ValueError): return default


def load_and_clean_school_records(records):
    """清洗校情学习记录。"""
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    out = []
    for row in records:
        if not isinstance(row, dict) or not row.get("student_id") or not row.get("course"):
            continue
        score = max(0.0, min(100.0, _num(row.get("score"))))
        completion = max(0.0, min(1.0, _num(row.get("completion"))))
        minutes = max(0.0, _num(row.get("minutes")))
        out.append({"student_id": str(row["student_id"]), "course": str(row["course"]), "score": score, "completion": completion, "minutes": minutes, "grade": str(row.get("grade", "unknown"))})
    return sorted(out, key=lambda r: (r["student_id"], r["course"]))


def build_course_insights(records):
    """生成课程维度洞察。"""
    buckets = {}
    for row in records:
        if not isinstance(row, dict) or not row.get("course"):
            continue
        buckets.setdefault(row["course"], []).append(row)
    result = []
    for course, rows in buckets.items():
        avg_score = sum(_num(r.get("score")) for r in rows) / len(rows)
        avg_completion = sum(_num(r.get("completion")) for r in rows) / len(rows)
        active = sum(1 for r in rows if _num(r.get("minutes")) >= 30)
        result.append({"course": course, "student_count": len(rows), "avg_score": round(avg_score, 2), "avg_completion": round(avg_completion, 4), "active_rate": round(active / len(rows), 4)})
    return sorted(result, key=lambda r: (-r["avg_score"], r["course"]))


def score_student_risk(records):
    """计算学生综合风险。"""
    buckets = {}
    for row in records:
        if isinstance(row, dict) and row.get("student_id"):
            buckets.setdefault(row["student_id"], []).append(row)
    result = []
    for sid, rows in buckets.items():
        avg_score = sum(_num(r.get("score")) for r in rows) / len(rows)
        avg_completion = sum(_num(r.get("completion")) for r in rows) / len(rows)
        total_minutes = sum(_num(r.get("minutes")) for r in rows)
        risk_score = max(0, 70 - avg_score) + max(0, 0.75 - avg_completion) * 50 + (10 if total_minutes < 60 else 0)
        level = "high" if risk_score >= 35 else "medium" if risk_score >= 15 else "low"
        result.append({"student_id": sid, "risk_score": round(risk_score, 2), "risk_level": level, "weak_courses": sorted(r["course"] for r in rows if _num(r.get("score")) < 60 or _num(r.get("completion")) < 0.6)})
    return sorted(result, key=lambda r: (-r["risk_score"], r["student_id"]))


def recommend_learning_paths(risk_rows, path_catalog):
    """基于风险画像推荐学习路径。"""
    if not isinstance(risk_rows, list) or not isinstance(path_catalog, list):
        raise ValueError("invalid inputs")
    catalog = [p for p in path_catalog if isinstance(p, dict) and p.get("path_id")]
    result = []
    for risk in risk_rows:
        if not isinstance(risk, dict) or not risk.get("student_id"):
            continue
        weak = set(risk.get("weak_courses") or [])
        ranked = []
        for path in catalog:
            tags = set(path.get("target_courses") or [])
            priority = len(weak & tags) * 20 + _num(path.get("base_priority"), 0)
            if risk.get("risk_level") == "high": priority += 10
            ranked.append({"path_id": str(path["path_id"]), "priority": round(priority, 2)})
        ranked = sorted(ranked, key=lambda r: (-r["priority"], r["path_id"]))[:2]
        result.append({"student_id": str(risk["student_id"]), "recommendations": ranked})
    return sorted(result, key=lambda r: r["student_id"])


def summarize_campus_report(records, risk_rows, recommendations):
    """汇总校情分析报告。"""
    students = {r.get("student_id") for r in records if isinstance(r, dict) and r.get("student_id")}
    courses = {r.get("course") for r in records if isinstance(r, dict) and r.get("course")}
    high = sum(1 for r in risk_rows if isinstance(r, dict) and r.get("risk_level") == "high")
    medium = sum(1 for r in risk_rows if isinstance(r, dict) and r.get("risk_level") == "medium")
    rec_count = sum(len(r.get("recommendations", [])) for r in recommendations if isinstance(r, dict))
    rate = 0.0 if not risk_rows else high / len(risk_rows)
    status = "urgent" if rate >= 0.3 else "watch" if rate > 0 else "stable"
    return {"student_count": len(students), "course_count": len(courses), "high_risk_students": high, "medium_risk_students": medium, "recommendation_count": rec_count, "campus_status": status}
