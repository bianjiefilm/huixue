def evaluate_investment_returns(projects, discount_rate=0.1):
    if not isinstance(projects, list):
        return []
    return [{"project_id": "", "roi": 0.0, "payback_period": None, "npv": 0.0, "priority": "defer"} for _ in projects]
