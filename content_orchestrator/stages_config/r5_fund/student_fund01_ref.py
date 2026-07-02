from datetime import date


def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _age_group(age):
    if age < 30:
        return "young"
    if age < 45:
        return "core"
    if age < 60:
        return "mature"
    return "senior"


def _risk_level(score):
    if score >= 80:
        return "aggressive"
    if score >= 55:
        return "balanced"
    if score >= 30:
        return "conservative"
    return "defensive"


def _rfm_segment(aum, tx_count, recency):
    if aum >= 50000 and tx_count >= 3 and (recency is None or recency <= 60):
        return "high_value_active"
    if aum >= 20000:
        return "high_value_watch"
    if tx_count >= 2 and (recency is not None and recency <= 90):
        return "growth_active"
    return "low_value"


def _marketing_tag(segment, risk_level, main_type):
    if segment == "high_value_active" and risk_level in {"balanced", "aggressive"}:
        return "wealth_upgrade"
    if segment == "high_value_watch":
        return "relationship_reactivation"
    if main_type == "money_market" or risk_level == "defensive":
        return "stable_income"
    if segment == "growth_active":
        return "fund_education"
    return "observe"


def build_customer_profiles(customers, transactions, as_of_date=None):
    """构建基金客户画像, 返回 RFM、风险偏好和营销标签。"""
    if not isinstance(customers, list) or not isinstance(transactions, list):
        raise ValueError("customers and transactions must be lists")
    current_date = _parse_date(as_of_date) or date(2026, 5, 1)
    tx_by_customer = {}
    for tx in transactions:
        if not isinstance(tx, dict) or not tx.get("customer_id"):
            continue
        amount = _num(tx.get("amount"), None)
        tx_date = _parse_date(tx.get("date"))
        if amount is None or amount <= 0 or tx_date is None:
            continue
        customer_id = str(tx["customer_id"]).strip()
        if not customer_id:
            continue
        tx_by_customer.setdefault(customer_id, []).append({
            "amount": amount,
            "date": tx_date,
            "fund_type": str(tx.get("fund_type", "unknown")).strip() or "unknown",
        })
    profiles = []
    seen = set()
    for customer in customers:
        if not isinstance(customer, dict) or not customer.get("customer_id"):
            continue
        customer_id = str(customer["customer_id"]).strip()
        if not customer_id or customer_id in seen:
            continue
        seen.add(customer_id)
        age = int(_num(customer.get("age"), 0))
        risk_score = _num(customer.get("risk_score"), 0.0)
        rows = tx_by_customer.get(customer_id, [])
        aum = sum(row["amount"] for row in rows)
        tx_count = len(rows)
        last_date = max((row["date"] for row in rows), default=None)
        recency = (current_date - last_date).days if last_date is not None else None
        type_amounts = {}
        for row in rows:
            type_amounts[row["fund_type"]] = type_amounts.get(row["fund_type"], 0.0) + row["amount"]
        main_type = max(type_amounts.items(), key=lambda item: (item[1], item[0]))[0] if type_amounts else "unknown"
        risk = _risk_level(risk_score)
        segment = _rfm_segment(aum, tx_count, recency)
        profiles.append({
            "customer_id": customer_id,
            "age_group": _age_group(age),
            "risk_level": risk,
            "aum": round(aum, 2),
            "transaction_count": tx_count,
            "last_transaction_days": recency,
            "main_fund_type": main_type,
            "rfm_segment": segment,
            "marketing_tag": _marketing_tag(segment, risk, main_type),
        })
    return sorted(profiles, key=lambda item: item["customer_id"])
