def compute_pass_rate(records, threshold=60):
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not records:
        raise ValueError("records cannot be empty")

    pass_count = sum(1 for record in records if record["score"] >= threshold)
    fail_count = len(records) - pass_count
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_count / len(records),
    }


def item_difficulty(scores, max_score=100):
    if not isinstance(scores, list):
        raise TypeError("scores must be a list")
    if not scores:
        raise ValueError("scores cannot be empty")
    return sum(scores) / len(scores) / max_score


def enrollment_concentration(courses):
    if not courses:
        raise ValueError("courses cannot be empty")
    counts = [course["enroll_count"] for course in courses]
    total = sum(counts)
    if total == 0:
        raise ValueError("total enrollment cannot be zero")
    return sum((count / total) ** 2 for count in counts)


def gpa_distribution_buckets(gpas, buckets):
    if not gpas:
        raise ValueError("gpas cannot be empty")
    if any(buckets[i] >= buckets[i + 1] for i in range(len(buckets) - 1)):
        raise ValueError("buckets must be increasing")

    result = {}
    for index in range(len(buckets) - 1):
        left = buckets[index]
        right = buckets[index + 1]
        label = f"{left:.2f}-{right:.2f}"
        if index == len(buckets) - 2:
            result[label] = sum(1 for gpa in gpas if left <= gpa <= right)
        else:
            result[label] = sum(1 for gpa in gpas if left <= gpa < right)
    return result
