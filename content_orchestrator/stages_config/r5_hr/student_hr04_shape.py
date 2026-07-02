def evaluate_performance_reviews(reviews):
    if not isinstance(reviews, list):
        return []
    return [{"employee_id": "", "performance_score": 0.0, "rating": "C", "bonus_multiplier": 0.0, "development_focus": []} for _ in reviews]
