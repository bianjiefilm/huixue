def recommend_fund_products(profiles, churn_risks, products, top_n=2):
    if not isinstance(profiles, list):
        return []
    return [{"customer_id": "", "recommendations": [{"product_id": "", "score": 0.0, "reason": []}]} for _ in profiles]
