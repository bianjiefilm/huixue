def analyze_salary_structure(employees):
    if not isinstance(employees, list):
        return []
    return [{"department": "", "employee_count": 0, "avg_salary": 0.0, "median_salary": 0.0, "pay_gap": 0.0, "salary_band": "low"} for _ in employees]
