def analyze_cash_flows(records):
    if not isinstance(records, list):
        return []
    return [{"period": "", "net_cash_flow": 0.0, "free_cash_flow": 0.0, "cash_conversion": None, "runway_months": None, "risk_level": "high"} for _ in records]
