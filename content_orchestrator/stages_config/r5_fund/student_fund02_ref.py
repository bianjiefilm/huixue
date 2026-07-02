def _num(value, default=0.0):
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _priority(score):
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _history_penalty(history, customer_id, campaign_id):
    if not isinstance(history, list):
        return 0.0
    penalty = 0.0
    for row in history:
        if not isinstance(row, dict):
            continue
        if str(row.get("customer_id")) != customer_id:
            continue
        if str(row.get("campaign_id")) == campaign_id and row.get("responded") is False:
            penalty += 0.08
        if row.get("responded") is True:
            penalty -= 0.04
    return penalty


def _score(profile, campaign, history):
    segment = str(profile.get("rfm_segment", "low_value"))
    risk = str(profile.get("risk_level", "defensive"))
    main_type = str(profile.get("main_fund_type", "unknown"))
    tag = str(profile.get("marketing_tag", "observe"))
    target_segments = set(campaign.get("target_segments", []))
    target_risks = set(campaign.get("target_risk_levels", []))
    fund_types = set(campaign.get("fund_types", []))
    score = _num(campaign.get("base_score"), 0.2)
    reasons = []
    if segment in target_segments:
        score += 0.22
        reasons.append("segment_match")
    if risk in target_risks:
        score += 0.18
        reasons.append("risk_match")
    if main_type in fund_types:
        score += 0.15
        reasons.append("fund_type_match")
    if tag == campaign.get("preferred_tag"):
        score += 0.12
        reasons.append("tag_match")
    if _num(profile.get("aum"), 0.0) >= _num(campaign.get("min_aum"), 0.0):
        score += 0.08
        reasons.append("aum_ready")
    score -= _history_penalty(history, str(profile.get("customer_id")), str(campaign.get("campaign_id")))
    return max(0.0, min(1.0, round(score, 4))), sorted(reasons)


def rank_marketing_responses(profiles, campaigns, response_history=None):
    """为每个客户选择最合适的基金营销活动并给出响应概率。"""
    if not isinstance(profiles, list) or not isinstance(campaigns, list):
        raise ValueError("profiles and campaigns must be lists")
    if response_history is not None and not isinstance(response_history, list):
        raise ValueError("response_history must be a list")
    valid_campaigns = [c for c in campaigns if isinstance(c, dict) and c.get("campaign_id")]
    output = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("customer_id"):
            continue
        best = None
        for campaign in valid_campaigns:
            score, reasons = _score(profile, campaign, response_history)
            item = {
                "customer_id": str(profile["customer_id"]),
                "campaign_id": str(campaign["campaign_id"]),
                "propensity_score": score,
                "priority": _priority(score),
                "reason": reasons,
            }
            if best is None or (item["propensity_score"], item["campaign_id"]) > (best["propensity_score"], best["campaign_id"]):
                best = item
        if best is not None:
            output.append(best)
    return sorted(output, key=lambda item: (-item["propensity_score"], item["customer_id"]))
