def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _payback(initial, flows):
    cumulative = 0.0
    for idx, flow in enumerate(flows, 1):
        previous = cumulative
        cumulative += flow
        if cumulative >= initial:
            if flow == 0:
                return float(idx)
            return round((idx - 1) + (initial - previous) / flow, 2)
    return None


def evaluate_investment_returns(projects, discount_rate=0.1):
    """评估投资项目 ROI、回收期、NPV 和优先级。"""
    if not isinstance(projects, list):
        raise ValueError("projects must be a list")
    rate = _num(discount_rate, 0.1)
    if rate <= -1:
        raise ValueError("discount_rate must be greater than -1")
    output = []
    seen = set()
    for item in projects:
        if not isinstance(item, dict) or not item.get("project_id"):
            continue
        pid = str(item["project_id"]).strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        initial = abs(_num(item.get("initial_investment"), 0.0))
        flows = item.get("cash_flows", [])
        flows = [_num(value, 0.0) for value in flows] if isinstance(flows, list) else []
        total_return = sum(flows) - initial
        roi = None if initial == 0 else round(total_return / initial, 4)
        npv = -initial + sum(flow / ((1 + rate) ** idx) for idx, flow in enumerate(flows, 1))
        payback = _payback(initial, flows) if initial > 0 else 0.0
        priority = "invest" if (roi is not None and roi >= 0.25 and npv > 0 and payback is not None and payback <= 3) else "watch" if (roi is not None and roi >= 0 and npv >= 0) else "defer"
        output.append({"project_id": pid, "roi": roi, "payback_period": payback, "npv": round(npv, 2), "priority": priority})
    return sorted(output, key=lambda row: (-row["npv"], row["project_id"]))
