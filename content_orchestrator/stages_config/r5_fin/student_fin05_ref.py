def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio(a, b):
    b = _num(b, 0.0)
    return None if b == 0 else round(_num(a, 0.0) / b, 4)


def analyze_financial_ratios(statements):
    if not isinstance(statements, list):
        raise ValueError("statements must be a list")
    rows, seen = [], set()
    for item in statements:
        if not isinstance(item, dict) or not item.get("period"):
            continue
        period = str(item["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        rows.append({k: _num(item.get(k), 0.0) for k in ("revenue", "cost", "net_profit", "current_assets", "current_liabilities", "total_assets", "total_liabilities", "equity")} | {"period": period})
    rows.sort(key=lambda row: row["period"])
    output, previous = [], None
    for row in rows:
        result = {
            "period": row["period"],
            "revenue_growth": None if previous in (None, 0) else round((row["revenue"] - previous) / previous, 4),
            "gross_margin": _ratio(row["revenue"] - row["cost"], row["revenue"]),
            "net_margin": _ratio(row["net_profit"], row["revenue"]),
            "current_ratio": _ratio(row["current_assets"], row["current_liabilities"]),
            "debt_to_asset": _ratio(row["total_liabilities"], row["total_assets"]),
            "roe": _ratio(row["net_profit"], row["equity"]),
        }
        previous = row["revenue"]
        score = sum([result["gross_margin"] is not None and result["gross_margin"] >= 0.35, result["net_margin"] is not None and result["net_margin"] >= 0.12, result["current_ratio"] is not None and result["current_ratio"] >= 1.5, result["debt_to_asset"] is not None and result["debt_to_asset"] <= 0.55, result["roe"] is not None and result["roe"] >= 0.12])
        result["quality_level"] = "excellent" if score >= 4 else "healthy" if score == 3 else "watch" if score == 2 else "weak"
        output.append(result)
    return output


def analyze_cash_flows(records):
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    output, seen = [], set()
    for item in records:
        if not isinstance(item, dict) or not item.get("period"):
            continue
        period = str(item["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        operating = _num(item.get("operating_cash_in")) - _num(item.get("operating_cash_out"))
        capex = abs(_num(item.get("capex")))
        net_cash = operating + _num(item.get("investing_cash_flow")) + _num(item.get("financing_cash_flow"))
        free_cash = operating - capex
        conversion = _ratio(operating, item.get("net_profit"))
        burn = max(_num(item.get("monthly_burn")), 0.0)
        runway = None if burn == 0 else round(_num(item.get("cash_balance")) / burn, 2)
        flags = sum([net_cash < 0, free_cash < 0, conversion is not None and conversion < 0.7, runway is not None and runway < 6])
        output.append({"period": period, "net_cash_flow": round(net_cash, 2), "free_cash_flow": round(free_cash, 2), "cash_conversion": conversion, "runway_months": runway, "risk_level": "critical" if flags >= 3 else "high" if flags == 2 else "medium" if flags == 1 else "low"})
    return sorted(output, key=lambda row: row["period"])


def detect_financial_risks(metrics, cash_flows):
    if not isinstance(metrics, list) or not isinstance(cash_flows, list):
        raise ValueError("metrics and cash_flows must be lists")
    cash_map = {str(row.get("period")): row for row in cash_flows if isinstance(row, dict) and row.get("period")}
    output, seen = [], set()
    for row in metrics:
        if not isinstance(row, dict) or not row.get("period"):
            continue
        period = str(row["period"]).strip()
        if not period or period in seen:
            continue
        seen.add(period)
        cash, signals, score = cash_map.get(period, {}), [], 0
        checks = [
            ("revenue_decline", row.get("revenue_growth") is not None and _num(row.get("revenue_growth")) < -0.15, 22),
            ("thin_profit", row.get("net_margin") is not None and _num(row.get("net_margin")) < 0.03, 18),
            ("liquidity_pressure", row.get("current_ratio") is not None and _num(row.get("current_ratio")) < 1.0, 18),
            ("high_leverage", row.get("debt_to_asset") is not None and _num(row.get("debt_to_asset")) > 0.7, 18),
            ("negative_return", row.get("roe") is not None and _num(row.get("roe")) < 0, 12),
            ("negative_free_cash_flow", _num(cash.get("free_cash_flow"), 0) < 0, 16),
            ("short_cash_runway", cash.get("runway_months") is not None and _num(cash.get("runway_months")) < 6, 12),
        ]
        for name, matched, weight in checks:
            if matched:
                signals.append(name); score += weight
        score = min(100, score)
        level = "critical" if score >= 70 else "high" if score >= 45 else "medium" if score >= 20 else "low"
        output.append({"period": period, "risk_score": score, "risk_level": level, "signals": sorted(signals), "recommended_action": "board_level_turnaround" if level == "critical" else "cash_and_debt_recovery_plan" if level == "high" else "monthly_monitoring" if level == "medium" else "routine_monitoring"})
    return sorted(output, key=lambda row: (-row["risk_score"], row["period"]))


def _payback(initial, flows):
    total = 0.0
    for idx, flow in enumerate(flows, 1):
        previous = total
        total += flow
        if total >= initial:
            return round((idx - 1) + (initial - previous) / flow, 2) if flow else float(idx)
    return None


def evaluate_investment_returns(projects, discount_rate=0.1):
    if not isinstance(projects, list):
        raise ValueError("projects must be a list")
    rate = _num(discount_rate, 0.1)
    if rate <= -1:
        raise ValueError("discount_rate must be greater than -1")
    output, seen = [], set()
    for item in projects:
        if not isinstance(item, dict) or not item.get("project_id"):
            continue
        pid = str(item["project_id"]).strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        initial = abs(_num(item.get("initial_investment")))
        flows = [_num(v) for v in item.get("cash_flows", [])] if isinstance(item.get("cash_flows", []), list) else []
        roi = None if initial == 0 else round((sum(flows) - initial) / initial, 4)
        npv = -initial + sum(flow / ((1 + rate) ** idx) for idx, flow in enumerate(flows, 1))
        payback = _payback(initial, flows) if initial > 0 else 0.0
        priority = "invest" if (roi is not None and roi >= 0.25 and npv > 0 and payback is not None and payback <= 3) else "watch" if (roi is not None and roi >= 0 and npv >= 0) else "defer"
        output.append({"project_id": pid, "roi": roi, "payback_period": payback, "npv": round(npv, 2), "priority": priority})
    return sorted(output, key=lambda row: (-row["npv"], row["project_id"]))


def summarize_financial_report(metrics, cash_flows, risks, investments):
    if not all(isinstance(value, list) for value in (metrics, cash_flows, risks, investments)):
        raise ValueError("all inputs must be lists")
    return {
        "periods": len([row for row in metrics if isinstance(row, dict)]),
        "excellent_periods": sum(1 for row in metrics if isinstance(row, dict) and row.get("quality_level") == "excellent"),
        "negative_free_cash_periods": sum(1 for row in cash_flows if isinstance(row, dict) and _num(row.get("free_cash_flow")) < 0),
        "critical_risk_periods": sum(1 for row in risks if isinstance(row, dict) and row.get("risk_level") == "critical"),
        "invest_projects": sum(1 for row in investments if isinstance(row, dict) and row.get("priority") == "invest"),
        "overall_status": "turnaround_required" if any(isinstance(row, dict) and row.get("risk_level") == "critical" for row in risks) else "growth_ready" if any(isinstance(row, dict) and row.get("priority") == "invest" for row in investments) else "stable",
    }
