def analyze_financial_ratios(statements):
    if not isinstance(statements, list):
        return []
    return [
        {
            "period": "",
            "revenue_growth": None,
            "gross_margin": 0.0,
            "net_margin": 0.0,
            "current_ratio": 0.0,
            "debt_to_asset": 0.0,
            "roe": 0.0,
            "quality_level": "weak",
        }
        for _ in statements
    ]
