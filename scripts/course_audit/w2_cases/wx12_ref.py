def validate_pipeline_input(rows, required_keys):
    if not isinstance(rows, list) or not isinstance(required_keys, list):
        raise TypeError("rows and required_keys must be list")
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("each row must be dict")
        for key in required_keys:
            if key not in row:
                return False
    return True


def get_cleaning_step_for_issue(issue_type):
    if not isinstance(issue_type, str):
        raise TypeError("issue_type must be str")
    mapping = {
        "missing": "fillna",
        "duplicate": "drop_dup",
        "outlier": "clip",
        "format": "normalize",
        "consistency": "validate_fk",
    }
    if issue_type not in mapping:
        raise ValueError("unknown issue")
    return mapping[issue_type]


def compute_pipeline_health_score(q, weights=None):
    required = ["completeness", "uniqueness", "validity"]
    if not isinstance(q, dict):
        raise TypeError("q must be dict")
    for key in required:
        if key not in q:
            raise ValueError("missing key")
        if q[key] < 0 or q[key] > 1:
            raise ValueError("quality out of range")
    if weights is None:
        weights = {key: 1 for key in required}
    total_weight = 0
    weighted_sum = 0
    for key in required:
        weight = weights.get(key, 1)
        if weight <= 0:
            raise ValueError("weight must be positive")
        total_weight += weight
        weighted_sum += q[key] * weight
    return weighted_sum / total_weight


def combine_cleaning_report(rows_in, rows_out, issues_fixed):
    if rows_in < 0 or rows_out < 0 or rows_out > rows_in:
        raise ValueError("invalid rows")
    total_issues = 0
    for count in issues_fixed.values():
        if count < 0:
            raise ValueError("invalid issue count")
        total_issues += count
    return {
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rows_dropped": rows_in - rows_out,
        "issues_fixed": issues_fixed,
        "total_issues": total_issues,
    }
