"""WX12 ref 实现 — 电商订单数据清洗流水线 4 函数."""
from typing import List, Dict, Optional


def validate_pipeline_input(rows, required_keys):
    if not isinstance(rows, list):
        raise TypeError("rows must be list")
    if not isinstance(required_keys, list):
        raise TypeError("required_keys must be list")
    if not rows or not required_keys:
        return True
    keys_set = set(required_keys)
    for r in rows:
        if not isinstance(r, dict):
            raise TypeError("row must be dict")
        if not keys_set.issubset(r.keys()):
            return False
    return True


def get_cleaning_step_for_issue(issue):
    if not isinstance(issue, str):
        raise TypeError("issue must be str")
    mapping = {
        'missing': 'fillna',
        'duplicate': 'drop_dup',
        'outlier': 'clip',
        'format': 'normalize',
        'consistency': 'validate_fk',
    }
    if issue not in mapping:
        raise ValueError(f"unknown issue: {issue}")
    return mapping[issue]


def compute_pipeline_health_score(quality_dict, weights=None):
    if not isinstance(quality_dict, dict):
        raise TypeError("quality_dict must be dict")
    required = {'completeness', 'uniqueness', 'validity'}
    if not required.issubset(quality_dict.keys()):
        raise ValueError("quality_dict missing required keys")
    for k in required:
        v = quality_dict[k]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise TypeError(f"quality value must be number: {k}")
        if v < 0 or v > 1:
            raise ValueError(f"quality {k} out of [0,1]: {v}")
    if weights is None:
        weights = {k: 1.0 for k in required}
    if not isinstance(weights, dict):
        raise TypeError("weights must be dict")
    if not required.issubset(weights.keys()):
        raise ValueError("weights missing required keys")
    for k in required:
        w = weights[k]
        if not isinstance(w, (int, float)) or isinstance(w, bool):
            raise TypeError(f"weight must be number: {k}")
        if w <= 0:
            raise ValueError(f"weight must be positive: {k}={w}")
    sum_w = sum(weights[k] for k in required)
    return sum(weights[k] * quality_dict[k] for k in required) / sum_w


def combine_cleaning_report(rows_in, rows_out, issues_fixed):
    if not isinstance(rows_in, int) or isinstance(rows_in, bool):
        raise TypeError("rows_in must be int")
    if not isinstance(rows_out, int) or isinstance(rows_out, bool):
        raise TypeError("rows_out must be int")
    if not isinstance(issues_fixed, dict):
        raise TypeError("issues_fixed must be dict")
    if rows_in < 0 or rows_out < 0:
        raise ValueError("rows_in/rows_out must be >= 0")
    if rows_out > rows_in:
        raise ValueError("rows_out cannot exceed rows_in")
    for k, v in issues_fixed.items():
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError(f"issues_fixed[{k}] must be non-negative int")
    return {
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rows_dropped': rows_in - rows_out,
        'issues_fixed': issues_fixed,
        'total_issues': sum(issues_fixed.values()),
    }
