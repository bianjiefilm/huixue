"""WX12 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx12 import (
    validate_pipeline_input,
    get_cleaning_step_for_issue,
    compute_pipeline_health_score,
    combine_cleaning_report,
)

TOL = 1e-6


# F1: validate_pipeline_input
def test_validate_all_present():
    rows = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    assert validate_pipeline_input(rows, ["id", "name"]) is True

def test_validate_extra_keys_ok():
    """额外字段允许"""
    rows = [{"id": 1, "name": "a", "x": 99}]
    assert validate_pipeline_input(rows, ["id", "name"]) is True

def test_validate_missing_one_key():
    rows = [{"id": 1}, {"id": 2, "name": "b"}]
    assert validate_pipeline_input(rows, ["id", "name"]) is False

def test_validate_missing_in_first_row():
    rows = [{"id": 1, "name": "a"}, {"name": "b"}]
    assert validate_pipeline_input(rows, ["id", "name"]) is False

def test_validate_empty_rows():
    """空 rows → True (vacuously)"""
    assert validate_pipeline_input([], ["id"]) is True

def test_validate_raises_on_non_list():
    with pytest.raises(TypeError):
        validate_pipeline_input("rows", ["id"])


# F2: get_cleaning_step_for_issue
def test_step_missing():
    assert get_cleaning_step_for_issue("missing") == "fillna"

def test_step_duplicate():
    assert get_cleaning_step_for_issue("duplicate") == "drop_dup"

def test_step_outlier():
    assert get_cleaning_step_for_issue("outlier") == "clip"

def test_step_format():
    assert get_cleaning_step_for_issue("format") == "normalize"

def test_step_consistency():
    assert get_cleaning_step_for_issue("consistency") == "validate_fk"

def test_step_raises_on_unknown():
    with pytest.raises(ValueError):
        get_cleaning_step_for_issue("unknown")

def test_step_raises_on_empty():
    with pytest.raises(ValueError):
        get_cleaning_step_for_issue("")

def test_step_raises_on_non_string():
    with pytest.raises(TypeError):
        get_cleaning_step_for_issue(123)


# F3: compute_pipeline_health_score
def test_health_default_weights():
    """default weights = (1+1+1)/3 = 简单平均"""
    q = {"completeness": 0.9, "uniqueness": 0.5, "validity": 0.8}
    assert abs(compute_pipeline_health_score(q) - (0.9 + 0.5 + 0.8) / 3) < TOL

def test_health_custom_weights():
    """weights={c:2, u:1, v:1}: (2*0.9 + 1*0.5 + 1*0.8) / 4 = 3.1/4 = 0.775"""
    q = {"completeness": 0.9, "uniqueness": 0.5, "validity": 0.8}
    w = {"completeness": 2, "uniqueness": 1, "validity": 1}
    assert abs(compute_pipeline_health_score(q, w) - 3.1 / 4) < TOL

def test_health_extreme_weight():
    """w={c:1, u:0.001, v:0.001}: 几乎完全是 completeness"""
    q = {"completeness": 1.0, "uniqueness": 0.0, "validity": 0.0}
    w = {"completeness": 1, "uniqueness": 0.001, "validity": 0.001}
    expected = (1*1.0 + 0.001*0.0 + 0.001*0.0) / (1 + 0.001 + 0.001)
    assert abs(compute_pipeline_health_score(q, w) - expected) < TOL

def test_health_perfect():
    q = {"completeness": 1.0, "uniqueness": 1.0, "validity": 1.0}
    assert abs(compute_pipeline_health_score(q) - 1.0) < TOL

def test_health_raises_on_missing_key():
    q = {"completeness": 0.5, "uniqueness": 0.5}  # 缺 validity
    with pytest.raises(ValueError):
        compute_pipeline_health_score(q)

def test_health_raises_on_quality_out_of_range():
    q = {"completeness": 1.5, "uniqueness": 0.5, "validity": 0.5}
    with pytest.raises(ValueError):
        compute_pipeline_health_score(q)

def test_health_raises_on_non_dict():
    with pytest.raises(TypeError):
        compute_pipeline_health_score([0.5, 0.5, 0.5])


# F4: combine_cleaning_report
def test_report_basic():
    r = combine_cleaning_report(1000, 950, {"missing": 30, "duplicate": 20})
    assert r["rows_in"] == 1000
    assert r["rows_out"] == 950
    assert r["rows_dropped"] == 50
    assert r["issues_fixed"] == {"missing": 30, "duplicate": 20}
    assert r["total_issues"] == 50

def test_report_all_5_keys():
    r = combine_cleaning_report(100, 80, {"missing": 20})
    assert "rows_in" in r
    assert "rows_out" in r
    assert "rows_dropped" in r
    assert "issues_fixed" in r
    assert "total_issues" in r

def test_report_no_drops():
    """rows_in == rows_out → dropped=0"""
    r = combine_cleaning_report(100, 100, {"missing": 5})
    assert r["rows_dropped"] == 0
    assert r["total_issues"] == 5

def test_report_empty_issues():
    """issues_fixed 空 → total=0"""
    r = combine_cleaning_report(100, 80, {})
    assert r["total_issues"] == 0

def test_report_multiple_issues():
    r = combine_cleaning_report(1000, 800, {"missing": 100, "duplicate": 50, "outlier": 30, "format": 20})
    assert r["total_issues"] == 200
    assert r["rows_dropped"] == 200

def test_report_raises_on_negative_rows():
    with pytest.raises(ValueError):
        combine_cleaning_report(-1, 0, {})

def test_report_raises_on_rows_out_gt_in():
    with pytest.raises(ValueError):
        combine_cleaning_report(100, 200, {})

def test_report_raises_on_negative_issue_count():
    with pytest.raises(ValueError):
        combine_cleaning_report(100, 50, {"missing": -10})

def test_report_raises_on_non_int():
    with pytest.raises(TypeError):
        combine_cleaning_report(100.0, 50, {})
