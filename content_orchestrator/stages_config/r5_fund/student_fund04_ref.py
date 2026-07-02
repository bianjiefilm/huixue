def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _risk_rank(level):
    return {"defensive": 1, "conservative": 2, "balanced": 3, "aggressive": 4}.get(str(level), 1)


def _score(profile, churn, product):
    score = _num(product.get("base_score"), 0.2)
    reasons = []
    if str(profile.get("risk_level")) in set(product.get("suitable_risk_levels", [])):
        score += 0.22
        reasons.append("risk_fit")
    if str(profile.get("main_fund_type")) == str(product.get("fund_type")):
        score += 0.16
        reasons.append("type_continuity")
    if _num(profile.get("aum"), 0.0) >= _num(product.get("min_aum"), 0.0):
        score += 0.1
        reasons.append("aum_fit")
    if churn >= 0.55 and product.get("retention_product"):
        score += 0.18
        reasons.append("retention_fit")
    if _risk_rank(profile.get("risk_level")) < _risk_rank(product.get("risk_level")):
        score -= 0.18
        reasons.append("risk_gap")
    if str(profile.get("marketing_tag")) == "stable_income" and product.get("fund_type") in {"bond", "money_market"}:
        score += 0.1
        reasons.append("income_preference")
    return max(0.0, min(1.0, round(score, 4))), sorted(set(reasons))


def recommend_fund_products(profiles, churn_risks, products, top_n=2):
    """根据客户画像和流失风险生成基金产品推荐。"""
    if not isinstance(profiles, list) or not isinstance(churn_risks, list) or not isinstance(products, list):
        raise ValueError("profiles, churn_risks and products must be lists")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n must be a positive integer")
    risk_map = {str(row.get("customer_id")): _num(row.get("churn_risk"), 0.0) for row in churn_risks if isinstance(row, dict) and row.get("customer_id")}
    valid_products = [row for row in products if isinstance(row, dict) and row.get("product_id")]
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        cid = str(profile["customer_id"])
        churn = risk_map.get(cid, 0.0)
        recs = []
        for product in valid_products:
            score, reasons = _score(profile, churn, product)
            recs.append({"product_id": str(product["product_id"]), "score": score, "reason": reasons})
        recs.sort(key=lambda item: (-item["score"], item["product_id"]))
        output.append({"customer_id": cid, "recommendations": recs[:top_n]})
    return sorted(output, key=lambda item: item["customer_id"])
