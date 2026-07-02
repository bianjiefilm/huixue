def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio(a, b):
    b = _num(b, 0.0)
    if b == 0:
        return None
    return round(_num(a, 0.0) / b, 4)


def _risk(net_cash, free_cash, conversion, runway):
    score = 0
    if net_cash < 0:
        score += 1
    if free_cash < 0:
        score += 1
    if conversion is not None and conversion < 0.7:
        score += 1
    if runway is not None and runway < 6:
        score += 1
    return "critical" if score >= 3 else "high" if score == 2 else "medium" if score == 1 else "low"


def analyze_cash_flows(records):
    """分析现金流质量、自由现金流和资金安全垫。"""
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    output = []
    seen = set()
    for item in records:
        if not isinstance(item, dict) or not item.get("period"):
            continue
        period = str(item["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        operating = _num(item.get("operating_cash_in"), 0.0) - _num(item.get("operating_cash_out"), 0.0)
        investing = _num(item.get("investing_cash_flow"), 0.0)
        financing = _num(item.get("financing_cash_flow"), 0.0)
        capex = abs(_num(item.get("capex"), 0.0))
        net_profit = _num(item.get("net_profit"), 0.0)
        cash_balance = _num(item.get("cash_balance"), 0.0)
        monthly_burn = max(_num(item.get("monthly_burn"), 0.0), 0.0)
        free_cash = operating - capex
        net_cash = operating + investing + financing
        conversion = _ratio(operating, net_profit)
        runway = None if monthly_burn == 0 else round(cash_balance / monthly_burn, 2)
        output.append({
            "period": period,
            "net_cash_flow": round(net_cash, 2),
            "free_cash_flow": round(free_cash, 2),
            "cash_conversion": conversion,
            "runway_months": runway,
            "risk_level": _risk(net_cash, free_cash, conversion, runway),
        })
    return sorted(output, key=lambda row: row["period"])
