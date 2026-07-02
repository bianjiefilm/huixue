"""学生学业表现基础统计 - 参考实现 (内部用, 不发学生).

仅供 ref 跑测验证 task_tests 正确性, 不入库, 不暴露给学生。
"""
from typing import List, Dict


def compute_pass_rate(grades: List[Dict], threshold: float = 60) -> Dict:
    if not isinstance(grades, list):
        raise TypeError("grades must be list")
    if len(grades) == 0:
        raise ValueError("grades must not be empty")
    pass_count = 0
    for g in grades:
        if not isinstance(g, dict) or "score" not in g:
            raise TypeError("each grade must be dict with 'score'")
        s = g["score"]
        if not isinstance(s, (int, float)) or isinstance(s, bool):
            raise TypeError("score must be numeric")
        if s >= threshold:
            pass_count += 1
    fail_count = len(grades) - pass_count
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_count / len(grades),
    }


def item_difficulty(scores: List[float], max_score: float = 100) -> float:
    if not isinstance(scores, list):
        raise TypeError("scores must be list")
    if len(scores) == 0:
        raise ValueError("scores must not be empty")
    if max_score <= 0:
        raise ValueError("max_score must be positive")
    for s in scores:
        if not isinstance(s, (int, float)) or isinstance(s, bool):
            raise TypeError("score must be numeric")
        if s < 0 or s > max_score:
            raise ValueError(f"score {s} out of range [0, {max_score}]")
    return sum(scores) / len(scores) / max_score


def enrollment_concentration(courses: List[Dict]) -> float:
    if not isinstance(courses, list):
        raise TypeError("courses must be list")
    if len(courses) == 0:
        raise ValueError("courses must not be empty")
    counts = []
    for c in courses:
        if not isinstance(c, dict) or "enroll_count" not in c:
            raise TypeError("each course must be dict with 'enroll_count'")
        ec = c["enroll_count"]
        if not isinstance(ec, (int, float)) or isinstance(ec, bool):
            raise TypeError("enroll_count must be numeric")
        if ec < 0:
            raise ValueError("enroll_count must be >= 0")
        counts.append(ec)
    total = sum(counts)
    if total == 0:
        raise ValueError("total enrollment cannot be zero")
    return sum((c / total) ** 2 for c in counts)


def gpa_distribution_buckets(gpas: List[float], buckets: List[float]) -> Dict:
    if not isinstance(gpas, list):
        raise TypeError("gpas must be list")
    if not isinstance(buckets, list):
        raise TypeError("buckets must be list")
    if len(gpas) == 0:
        raise ValueError("gpas must not be empty")
    if len(buckets) < 2:
        raise ValueError("buckets must have at least 2 elements")
    for i in range(len(buckets) - 1):
        if buckets[i] >= buckets[i + 1]:
            raise ValueError("buckets must be strictly increasing")
    for g in gpas:
        if not isinstance(g, (int, float)) or isinstance(g, bool):
            raise TypeError("gpa must be numeric")

    result = {}
    for i in range(len(buckets) - 1):
        key = f"{buckets[i]:.2f}-{buckets[i+1]:.2f}"
        result[key] = 0

    for g in gpas:
        for i in range(len(buckets) - 1):
            lo, hi = buckets[i], buckets[i + 1]
            if i == len(buckets) - 2:
                # 最后一桶闭区间
                if lo <= g <= hi:
                    key = f"{lo:.2f}-{hi:.2f}"
                    result[key] += 1
                    break
            else:
                if lo <= g < hi:
                    key = f"{lo:.2f}-{hi:.2f}"
                    result[key] += 1
                    break
    return result


# ============ 自检 ============
if __name__ == "__main__":
    # F1
    grades = [{"student_id": f"S{i:03d}", "score": s} for i, s in enumerate([75, 88, 60, 45, 92, 70, 58, 80, 65, 71])]
    r = compute_pass_rate(grades, 60)
    print(f"F1: {r}")
    assert r == {"pass_count": 8, "fail_count": 2, "pass_rate": 0.8}

    # F2
    p = item_difficulty([60, 70, 80], 100)
    print(f"F2: {p}")
    assert abs(p - 0.7) < 1e-9

    # F3
    courses = [{"course_id": f"C{i}", "enroll_count": ec} for i, ec in enumerate([40, 30, 15, 10, 5])]
    h = enrollment_concentration(courses)
    print(f"F3: {h}")
    assert abs(h - 0.285) < 1e-9

    # F4
    gpas = [0.5, 1.5, 2.5, 3.0, 3.5, 4.0, 2.0, 1.0, 3.2, 2.8]
    buckets = [0, 1.0, 2.0, 3.0, 4.0]
    d = gpa_distribution_buckets(gpas, buckets)
    print(f"F4: {d}")
    # 0.5 ∈ [0,1) → 1; 1.0,1.5 ∈ [1,2) → 2; 2.0,2.5,2.8 ∈ [2,3) → 3; 3.0,3.2,3.5,4.0 ∈ [3,4] → 4
    assert d == {"0.00-1.00": 1, "1.00-2.00": 2, "2.00-3.00": 3, "3.00-4.00": 4}

    print("All ref self-checks passed!")
