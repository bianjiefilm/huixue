from datetime import date


def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _age_group(age):
    return "young" if age < 30 else "core" if age < 45 else "mature" if age < 60 else "senior"


def _risk_level(score):
    return "aggressive" if score >= 80 else "balanced" if score >= 55 else "conservative" if score >= 30 else "defensive"


def build_customer_profiles(customers, transactions, as_of_date=None):
    """构建基金客户画像。"""
    if not isinstance(customers, list) or not isinstance(transactions, list):
        raise ValueError("customers and transactions must be lists")
    today = _parse_date(as_of_date) or date(2026, 5, 1)
    tx_map = {}
    for tx in transactions:
        if not isinstance(tx, dict) or not tx.get("customer_id"):
            continue
        amount, tx_date = _num(tx.get("amount"), None), _parse_date(tx.get("date"))
        if amount is None or amount <= 0 or tx_date is None:
            continue
        tx_map.setdefault(str(tx["customer_id"]).strip(), []).append({"amount": amount, "date": tx_date, "fund_type": str(tx.get("fund_type", "unknown"))})
    profiles, seen = [], set()
    for customer in customers:
        if not isinstance(customer, dict) or not customer.get("customer_id"):
            continue
        cid = str(customer["customer_id"]).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        rows = tx_map.get(cid, [])
        aum = sum(row["amount"] for row in rows)
        last_date = max((row["date"] for row in rows), default=None)
        recency = (today - last_date).days if last_date else None
        type_amounts = {}
        for row in rows:
            type_amounts[row["fund_type"]] = type_amounts.get(row["fund_type"], 0.0) + row["amount"]
        main_type = max(type_amounts.items(), key=lambda item: (item[1], item[0]))[0] if type_amounts else "unknown"
        segment = "high_value_active" if aum >= 50000 and len(rows) >= 3 and (recency is None or recency <= 60) else "high_value_watch" if aum >= 20000 else "growth_active" if len(rows) >= 2 and recency is not None and recency <= 90 else "low_value"
        risk = _risk_level(_num(customer.get("risk_score"), 0))
        tag = "wealth_upgrade" if segment == "high_value_active" and risk in {"balanced", "aggressive"} else "relationship_reactivation" if segment == "high_value_watch" else "stable_income" if main_type == "money_market" or risk == "defensive" else "fund_education" if segment == "growth_active" else "observe"
        profiles.append({"customer_id": cid, "age_group": _age_group(int(_num(customer.get("age"), 0))), "risk_level": risk, "aum": round(aum, 2), "transaction_count": len(rows), "last_transaction_days": recency, "main_fund_type": main_type, "rfm_segment": segment, "marketing_tag": tag})
    return sorted(profiles, key=lambda item: item["customer_id"])


def rank_marketing_responses(profiles, campaigns, response_history=None):
    """为客户选择最可能响应的营销活动。"""
    if not isinstance(profiles, list) or not isinstance(campaigns, list):
        raise ValueError("profiles and campaigns must be lists")
    if response_history is not None and not isinstance(response_history, list):
        raise ValueError("response_history must be a list")
    history = response_history or []
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        best = None
        for campaign in [c for c in campaigns if isinstance(c, dict) and c.get("campaign_id")]:
            score, reasons = _num(campaign.get("base_score"), 0.2), []
            if profile.get("rfm_segment") in campaign.get("target_segments", []):
                score += 0.22; reasons.append("segment_match")
            if profile.get("risk_level") in campaign.get("target_risk_levels", []):
                score += 0.18; reasons.append("risk_match")
            if profile.get("main_fund_type") in campaign.get("fund_types", []):
                score += 0.15; reasons.append("fund_type_match")
            if profile.get("marketing_tag") == campaign.get("preferred_tag"):
                score += 0.12; reasons.append("tag_match")
            if _num(profile.get("aum"), 0) >= _num(campaign.get("min_aum"), 0):
                score += 0.08; reasons.append("aum_ready")
            for row in history:
                if isinstance(row, dict) and str(row.get("customer_id")) == str(profile["customer_id"]):
                    score += 0.04 if row.get("responded") is True else -0.08 if str(row.get("campaign_id")) == str(campaign["campaign_id"]) else 0.0
            score = max(0.0, min(1.0, round(score, 4)))
            item = {"customer_id": str(profile["customer_id"]), "campaign_id": str(campaign["campaign_id"]), "propensity_score": score, "priority": "high" if score >= 0.75 else "medium" if score >= 0.5 else "low", "reason": sorted(reasons)}
            if best is None or (item["propensity_score"], item["campaign_id"]) > (best["propensity_score"], best["campaign_id"]):
                best = item
        if best:
            output.append(best)
    return sorted(output, key=lambda item: (-item["propensity_score"], item["customer_id"]))


def predict_churn_risk(profiles, interactions=None):
    """预测客户流失风险。"""
    if not isinstance(profiles, list):
        raise ValueError("profiles must be a list")
    if interactions is not None and not isinstance(interactions, list):
        raise ValueError("interactions must be a list")
    metrics = {}
    for row in interactions or []:
        if isinstance(row, dict) and row.get("customer_id"):
            item = metrics.setdefault(str(row["customer_id"]), {"contacts": 0, "clicks": 0, "complaints": 0})
            item["contacts"] += int(_num(row.get("contacts"), 0)); item["clicks"] += int(_num(row.get("clicks"), 0)); item["complaints"] += int(_num(row.get("complaints"), 0))
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        cid, recency = str(profile["customer_id"]), profile.get("last_transaction_days")
        recency = 999 if recency is None else _num(recency, 999)
        score, drivers = 0.12, []
        if recency > 180:
            score += 0.35; drivers.append("inactive")
        elif recency > 90:
            score += 0.2; drivers.append("cooling")
        if profile.get("rfm_segment") == "high_value_watch":
            score += 0.36; drivers.append("high_value_watch")
        elif profile.get("rfm_segment") == "low_value":
            score += 0.1; drivers.append("low_value")
        if _num(profile.get("aum"), 0) >= 50000:
            score += 0.06; drivers.append("large_aum")
        m = metrics.get(cid, {"contacts": 0, "clicks": 0, "complaints": 0})
        if m["contacts"] > 0 and m["clicks"] == 0:
            score += 0.14; drivers.append("low_engagement")
        if m["complaints"] > 0:
            score += 0.22; drivers.append("negative_feedback")
        if m["clicks"] >= 3:
            score -= 0.12; drivers.append("recent_interest")
        score = max(0.0, min(1.0, round(score, 4)))
        level = "critical" if score >= 0.75 else "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
        action = "advisor_call_with_retention_offer" if level == "critical" else "service_recovery" if "negative_feedback" in drivers else "reactivation_campaign" if "inactive" in drivers else "education_content" if "low_engagement" in drivers else "observe"
        output.append({"customer_id": cid, "churn_risk": score, "risk_level": level, "drivers": sorted(set(drivers)), "retention_action": action})
    return sorted(output, key=lambda item: (-item["churn_risk"], item["customer_id"]))


def recommend_fund_products(profiles, churn_risks, products, top_n=2):
    """生成基金产品推荐。"""
    if not isinstance(profiles, list) or not isinstance(churn_risks, list) or not isinstance(products, list):
        raise ValueError("profiles, churn_risks and products must be lists")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n must be a positive integer")
    churn = {str(row.get("customer_id")): _num(row.get("churn_risk"), 0) for row in churn_risks if isinstance(row, dict)}
    rank = {"defensive": 1, "conservative": 2, "balanced": 3, "aggressive": 4}
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        recs = []
        for product in [p for p in products if isinstance(p, dict) and p.get("product_id")]:
            score, reasons = _num(product.get("base_score"), 0.2), []
            if profile.get("risk_level") in product.get("suitable_risk_levels", []):
                score += 0.22; reasons.append("risk_fit")
            if profile.get("main_fund_type") == product.get("fund_type"):
                score += 0.16; reasons.append("type_continuity")
            if _num(profile.get("aum"), 0) >= _num(product.get("min_aum"), 0):
                score += 0.1; reasons.append("aum_fit")
            if churn.get(str(profile["customer_id"]), 0) >= 0.55 and product.get("retention_product"):
                score += 0.18; reasons.append("retention_fit")
            if rank.get(profile.get("risk_level"), 1) < rank.get(product.get("risk_level"), 1):
                score -= 0.18; reasons.append("risk_gap")
            if profile.get("marketing_tag") == "stable_income" and product.get("fund_type") in {"bond", "money_market"}:
                score += 0.1; reasons.append("income_preference")
            recs.append({"product_id": str(product["product_id"]), "score": max(0.0, min(1.0, round(score, 4))), "reason": sorted(set(reasons))})
        recs.sort(key=lambda item: (-item["score"], item["product_id"]))
        output.append({"customer_id": str(profile["customer_id"]), "recommendations": recs[:top_n]})
    return sorted(output, key=lambda item: item["customer_id"])


def summarize_marketing_report(profiles, responses, churn_risks, recommendations):
    """汇总精准营销闭环指标。"""
    if not all(isinstance(value, list) for value in (profiles, responses, churn_risks, recommendations)):
        raise ValueError("all inputs must be lists")
    top_counts, action_mix = {}, {}
    for row in recommendations:
        if isinstance(row, dict) and row.get("recommendations"):
            product_id = row["recommendations"][0].get("product_id")
            top_counts[product_id] = top_counts.get(product_id, 0) + 1
    for row in churn_risks:
        if isinstance(row, dict):
            action = row.get("retention_action", "observe")
            action_mix[action] = action_mix.get(action, 0) + 1
    return {
        "total_customers": len([p for p in profiles if isinstance(p, dict)]),
        "high_value_customers": sum(1 for p in profiles if isinstance(p, dict) and str(p.get("rfm_segment", "")).startswith("high_value")),
        "high_churn_customers": sum(1 for r in churn_risks if isinstance(r, dict) and r.get("risk_level") in {"critical", "high"}),
        "high_priority_responses": sum(1 for r in responses if isinstance(r, dict) and r.get("priority") == "high"),
        "top_product_counts": dict(sorted(top_counts.items())),
        "action_mix": dict(sorted(action_mix.items())),
    }
