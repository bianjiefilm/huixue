def _num(value):
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _corr(xs, ys):
    if len(xs) < 2:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (vx * vy) ** 0.5


def analyze_course_correlation(course_scores):
    """分析课程成绩之间的相关性。"""
    if not isinstance(course_scores, list):
        raise ValueError("course_scores must be a list")
    courses = sorted({c for row in course_scores if isinstance(row, dict) for c in row.get("scores", {}) if isinstance(row.get("scores"), dict)})
    pairs = []
    for i, a in enumerate(courses):
        for b in courses[i + 1:]:
            xs, ys = [], []
            for row in course_scores:
                scores = row.get("scores") if isinstance(row, dict) else None
                if not isinstance(scores, dict):
                    continue
                va, vb = _num(scores.get(a)), _num(scores.get(b))
                if va is not None and vb is not None:
                    xs.append(va); ys.append(vb)
            coef = round(_corr(xs, ys), 4)
            strength = "strong" if abs(coef) >= 0.75 else "medium" if abs(coef) >= 0.4 else "weak"
            pairs.append({"course_pair": [a, b], "sample_size": len(xs), "correlation": coef, "strength": strength})
    return sorted(pairs, key=lambda r: (-abs(r["correlation"]), r["course_pair"]))
