def build_customer_profiles(customers, transactions, as_of_date=None):
    if not isinstance(customers, list):
        return []
    return [
        {
            "customer_id": "",
            "age_group": "",
            "risk_level": "",
            "aum": 0.0,
            "transaction_count": 0,
            "last_transaction_days": None,
            "main_fund_type": "unknown",
            "rfm_segment": "low_value",
            "marketing_tag": "observe",
        }
        for _ in customers
    ]
