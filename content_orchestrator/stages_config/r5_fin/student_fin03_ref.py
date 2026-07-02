def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def detect_financial_risks(metrics, cash_flows):
    """结合财务比率和现金流指标输出风险预警。"""
    if not isinstance(metrics, list) or not isinstance(cash_flows, list):
        raise ValueError("metrics and cash_flows must be lists")
    cash_map = {str(row.get("period")): row for row in cash_flows if isinstance(row, dict) and row.get("period")}
    output = []
    seen = set()
    for row in metrics:
        if not isinstance(row, dict) or not row.get("period"):
            continue
        period = str(row["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        cash = cash_map.get(period, {})
        signals = []
        score = 0
        if row.get("revenue_growth") is not None and _num(row.get("revenue_growth")) < -0.15:
            score += 22; signals.append("revenue_decline")
        if row.get("net_margin") is not None and _num(row.get("net_margin")) < 0.03:
            score += 18; signals.append("thin_profit")
        if row.get("current_ratio") is not None and _num(row.get("current_ratio")) < 1.0:
            score += 18; signals.append("liquidity_pressure")
        if row.get("debt_to_asset") is not None and _num(row.get("debt_to_asset")) > 0.7:
            score += 18; signals.append("high_leverage")
        if row.get("roe") is not None and _num(row.get("roe")) < 0:
            score += 12; signals.append("negative_return")
        if _num(cash.get("free_cash_flow"), 0) < 0:
            score += 16; signals.append("negative_free_cash_flow")
        if cash.get("runway_months") is not None and _num(cash.get("runway_months")) < 6:
            score += 12; signals.append("short_cash_runway")
        score = min(100, score)
        level = "critical" if score >= 70 else "high" if score >= 45 else "medium" if score >= 20 else "low"
        action = "board_level_turnaround" if level == "critical" else "cash_and_debt_recovery_plan" if level == "high" else "monthly_monitoring" if level == "medium" else "routine_monitoring"
        output.append({"period": period, "risk_score": score, "risk_level": level, "signals": sorted(signals), "recommended_action": action})
    return sorted(output, key=lambda item: (-item["risk_score"], item["period"]))
