def classify_value_status(value, min_value, max_value, missing_marker=None):
    if not isinstance(min_value, (int, float)) or not isinstance(max_value, (int, float)):
        raise TypeError("bounds must be numeric")
    if value is None or value == "" or value == missing_marker:
        return "missing"
    if not isinstance(value, (int, float)):
        raise TypeError("value must be numeric")
    return "valid" if min_value <= value <= max_value else "out_of_range"


def compute_quality_ratio(valid_count, total_count):
    if not isinstance(valid_count, int) or not isinstance(total_count, int):
        raise TypeError("counts must be int")
    if total_count <= 0 or valid_count < 0 or valid_count > total_count:
        raise ValueError("invalid counts")
    return valid_count / total_count


def get_cleaning_priority(issue_type):
    if not isinstance(issue_type, str):
        raise TypeError("issue_type must be str")
    priorities = {
        "missing": 1,
        "duplicate": 2,
        "outlier": 3,
        "format": 4,
        "consistency": 5,
    }
    if issue_type not in priorities:
        raise ValueError("unknown issue")
    return priorities[issue_type]


def decide_drop_or_fill(missing_count, total_count, threshold=0.5):
    if not isinstance(missing_count, int) or not isinstance(total_count, int):
        raise TypeError("counts must be int")
    if total_count <= 0 or missing_count < 0 or missing_count > total_count:
        raise ValueError("invalid counts")
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
        raise ValueError("invalid threshold")
    return "drop" if (missing_count / total_count) > threshold else "fill"
