def analyze_recruiting_funnel(candidates):
    if not isinstance(candidates, list):
        return []
    return [{"role": "", "applied": 0, "screen_rate": 0.0, "interview_rate": 0.0, "offer_rate": 0.0, "hire_rate": 0.0, "bottleneck": "screen"} for _ in candidates]
