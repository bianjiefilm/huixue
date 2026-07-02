STAGES = ["applied", "screen", "interview", "offer", "hired"]


def analyze_recruiting_funnel(candidates):
    """按岗位统计招聘漏斗转化率和瓶颈环节。"""
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")
    buckets = {}
    for row in candidates:
        if not isinstance(row, dict) or not row.get("role"):
            continue
        role = str(row["role"]).strip()
        stage = str(row.get("stage", "")).strip()
        if not role or stage not in STAGES:
            continue
        counts = buckets.setdefault(role, {name: 0 for name in STAGES})
        start = STAGES.index(stage)
        for name in STAGES[: start + 1]:
            counts[name] += 1
    output = []
    for role, counts in buckets.items():
        applied = counts["applied"]
        rates = {
            "screen_rate": 0.0 if applied == 0 else counts["screen"] / applied,
            "interview_rate": 0.0 if counts["screen"] == 0 else counts["interview"] / counts["screen"],
            "offer_rate": 0.0 if counts["interview"] == 0 else counts["offer"] / counts["interview"],
            "hire_rate": 0.0 if counts["offer"] == 0 else counts["hired"] / counts["offer"],
        }
        order = {"screen_rate": 0, "interview_rate": 1, "offer_rate": 2, "hire_rate": 3}
        bottleneck = min(rates.items(), key=lambda item: (item[1], order[item[0]]))[0].replace("_rate", "")
        output.append({
            "role": role,
            "applied": applied,
            "screen_rate": round(rates["screen_rate"], 4),
            "interview_rate": round(rates["interview_rate"], 4),
            "offer_rate": round(rates["offer_rate"], 4),
            "hire_rate": round(rates["hire_rate"], 4),
            "bottleneck": bottleneck,
        })
    return sorted(output, key=lambda item: (-item["applied"], item["role"]))
