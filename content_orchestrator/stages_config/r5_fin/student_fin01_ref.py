def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio(numerator, denominator):
    denominator = _num(denominator, 0.0)
    if denominator == 0:
        return None
    return round(_num(numerator, 0.0) / denominator, 4)


def _quality(row):
    score = 0
    if row["gross_margin"] is not None and row["gross_margin"] >= 0.35:
        score += 1
    if row["net_margin"] is not None and row["net_margin"] >= 0.12:
        score += 1
    if row["current_ratio"] is not None and row["current_ratio"] >= 1.5:
        score += 1
    if row["debt_to_asset"] is not None and row["debt_to_asset"] <= 0.55:
        score += 1
    if row["roe"] is not None and row["roe"] >= 0.12:
        score += 1
    return "excellent" if score >= 4 else "healthy" if score == 3 else "watch" if score == 2 else "weak"


def analyze_financial_ratios(statements):
    """计算多期财务比率并给出经营质量分层。"""
    if not isinstance(statements, list):
        raise ValueError("statements must be a list")
    rows = []
    seen = set()
    for item in statements:
        if not isinstance(item, dict) or not item.get("period"):
            continue
        period = str(item["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        rows.append({
            "period": period,
            "revenue": _num(item.get("revenue"), 0.0),
            "cost": _num(item.get("cost"), 0.0),
            "net_profit": _num(item.get("net_profit"), 0.0),
            "current_assets": _num(item.get("current_assets"), 0.0),
            "current_liabilities": _num(item.get("current_liabilities"), 0.0),
            "total_assets": _num(item.get("total_assets"), 0.0),
            "total_liabilities": _num(item.get("total_liabilities"), 0.0),
            "equity": _num(item.get("equity"), 0.0),
        })
    rows.sort(key=lambda row: row["period"])
    output = []
    previous_revenue = None
    for row in rows:
        revenue_growth = None if previous_revenue in (None, 0) else round((row["revenue"] - previous_revenue) / previous_revenue, 4)
        previous_revenue = row["revenue"]
        result = {
            "period": row["period"],
            "revenue_growth": revenue_growth,
            "gross_margin": _ratio(row["revenue"] - row["cost"], row["revenue"]),
            "net_margin": _ratio(row["net_profit"], row["revenue"]),
            "current_ratio": _ratio(row["current_assets"], row["current_liabilities"]),
            "debt_to_asset": _ratio(row["total_liabilities"], row["total_assets"]),
            "roe": _ratio(row["net_profit"], row["equity"]),
        }
        result["quality_level"] = _quality(result)
        output.append(result)
    return output
