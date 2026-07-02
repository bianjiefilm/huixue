def detect_financial_risks(metrics, cash_flows):
    if not isinstance(metrics, list):
        return []
    return [{"period": "", "risk_score": 0, "risk_level": "low", "signals": [], "recommended_action": "monitor"} for _ in metrics]
