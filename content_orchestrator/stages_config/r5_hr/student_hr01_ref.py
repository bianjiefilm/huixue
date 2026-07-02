def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _median(values):
    if not values:
        return 0.0
    vals = sorted(values)
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def analyze_salary_structure(employees):
    """按部门分析薪资结构、离散程度和薪酬带。"""
    if not isinstance(employees, list):
        raise ValueError("employees must be a list")
    buckets = {}
    for row in employees:
        if not isinstance(row, dict) or not row.get("department"):
            continue
        salary = _num(row.get("salary"), None)
        if salary is None or salary <= 0:
            continue
        dept = str(row["department"]).strip()
        if not dept:
            continue
        buckets.setdefault(dept, []).append(salary)
    result = []
    for dept, salaries in buckets.items():
        avg = sum(salaries) / len(salaries)
        med = _median(salaries)
        gap = 0.0 if med == 0 else (max(salaries) - min(salaries)) / med
        band = "high" if avg >= 30000 else "medium" if avg >= 18000 else "low"
        result.append({
            "department": dept,
            "employee_count": len(salaries),
            "avg_salary": round(avg, 2),
            "median_salary": round(med, 2),
            "pay_gap": round(gap, 4),
            "salary_band": band,
        })
    return sorted(result, key=lambda item: (-item["avg_salary"], item["department"]))
