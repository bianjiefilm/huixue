def _num(value, default=0.0):
    if isinstance(value, bool): return default
    try: return float(value)
    except (TypeError, ValueError): return default


def recommend_advancement_paths(student_profile, path_catalog):
    """为学生推荐升学路径。"""
    if not isinstance(student_profile, dict) or not isinstance(path_catalog, list):
        raise ValueError("invalid inputs")
    interests = set(student_profile.get("interests") or [])
    skills = set(student_profile.get("skills") or [])
    score = _num(student_profile.get("avg_score"))
    budget = _num(student_profile.get("budget"), 10**9)
    result = []
    for path in path_catalog:
        if not isinstance(path, dict) or not path.get("path_id"):
            continue
        min_score = _num(path.get("min_score"))
        cost = _num(path.get("cost"))
        if score < min_score or cost > budget:
            continue
        tags = set(path.get("tags") or [])
        required = set(path.get("required_skills") or [])
        interest_match = len(interests & tags)
        skill_match = len(skills & required)
        missing = sorted(required - skills)
        fit = 50 + interest_match * 12 + skill_match * 10 + min(20, max(0, score - min_score) * 0.5) - len(missing) * 4
        result.append({"path_id": str(path["path_id"]), "fit_score": round(fit, 2), "missing_skills": missing, "reason_tags": sorted(interests & tags)})
    return sorted(result, key=lambda r: (-r["fit_score"], r["path_id"]))[:3]
