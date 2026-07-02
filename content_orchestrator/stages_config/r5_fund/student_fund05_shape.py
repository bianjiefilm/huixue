def build_customer_profiles(customers, transactions, as_of_date=None):
    return [{"customer_id": "", "age_group": "", "risk_level": "", "aum": 0.0, "transaction_count": 0, "last_transaction_days": None, "main_fund_type": "unknown", "rfm_segment": "low_value", "marketing_tag": "observe"} for _ in customers] if isinstance(customers, list) else []


def rank_marketing_responses(profiles, campaigns, response_history=None):
    return [{"customer_id": "", "campaign_id": "", "propensity_score": 0.0, "priority": "low", "reason": []} for _ in profiles] if isinstance(profiles, list) else []


def predict_churn_risk(profiles, interactions=None):
    return [{"customer_id": "", "churn_risk": 0.0, "risk_level": "low", "drivers": [], "retention_action": "observe"} for _ in profiles] if isinstance(profiles, list) else []


def recommend_fund_products(profiles, churn_risks, products, top_n=2):
    return [{"customer_id": "", "recommendations": [{"product_id": "", "score": 0.0, "reason": []}]} for _ in profiles] if isinstance(profiles, list) else []


def summarize_marketing_report(profiles, responses, churn_risks, recommendations):
    return {"total_customers": 0, "high_value_customers": 0, "high_churn_customers": 0, "high_priority_responses": 0, "top_product_counts": {}, "action_mix": {}}
