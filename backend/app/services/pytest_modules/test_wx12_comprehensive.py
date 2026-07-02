"""WX12 综合关 pytest_module 协议测试模块.

import student_wx12 (学生提交模块) 后跑 4 个函数 28 cases.
backend execute_pytest_module 解析 stdout 末行 'X passed, Y failed in Zs'.
"""
import pytest
from student_wx12 import (
    validate_pipeline_input,
    get_cleaning_step_for_issue,
    compute_pipeline_health_score,
    combine_cleaning_report,
)

TOL = 1e-6


# ============================================================
# F1: validate_pipeline_input (8 cases)
# ============================================================

def test_vpi_all_keys_present():
    rows = [{"id": 1, "amt": 10, "ts": "2025-01-01"}]
    assert validate_pipeline_input(rows, ["id", "amt"]) is True


def test_vpi_missing_key():
    rows = [{"id": 1, "amt": 10}, {"id": 2}]
    assert validate_pipeline_input(rows, ["id", "amt"]) is False


def test_vpi_extra_keys_allowed():
    rows = [{"id": 1, "amt": 10, "extra": "x"}]
    assert validate_pipeline_input(rows, ["id"]) is True


def test_vpi_empty_rows():
    assert validate_pipeline_input([], ["id", "amt"]) is True


def test_vpi_empty_keys():
    assert validate_pipeline_input([{"x": 1}], []) is True


def test_vpi_raises_on_non_list_rows():
    with pytest.raises(TypeError):
        validate_pipeline_input("abc", ["id"])


def test_vpi_raises_on_non_list_keys():
    with pytest.raises(TypeError):
        validate_pipeline_input([], "id")


def test_vpi_raises_on_non_dict_row():
    with pytest.raises(TypeError):
        validate_pipeline_input(["not a dict"], ["id"])


# ============================================================
# F2: get_cleaning_step_for_issue (7 cases)
# ============================================================

def test_gcs_missing():
    assert get_cleaning_step_for_issue("missing") == "fillna"


def test_gcs_duplicate():
    assert get_cleaning_step_for_issue("duplicate") == "drop_dup"


def test_gcs_outlier():
    assert get_cleaning_step_for_issue("outlier") == "clip"


def test_gcs_format():
    assert get_cleaning_step_for_issue("format") == "normalize"


def test_gcs_consistency():
    assert get_cleaning_step_for_issue("consistency") == "validate_fk"


def test_gcs_raises_on_unknown():
    with pytest.raises(ValueError):
        get_cleaning_step_for_issue("unknown_issue")


def test_gcs_raises_on_non_str():
    with pytest.raises(TypeError):
        get_cleaning_step_for_issue(123)


# ============================================================
# F3: compute_pipeline_health_score (7 cases)
# ============================================================

def test_cphs_default_weights_avg():
    q = {"completeness": 0.8, "uniqueness": 0.9, "validity": 0.7}
    assert abs(compute_pipeline_health_score(q) - 0.8) < TOL


def test_cphs_perfect():
    q = {"completeness": 1.0, "uniqueness": 1.0, "validity": 1.0}
    assert abs(compute_pipeline_health_score(q) - 1.0) < TOL


def test_cphs_zero():
    q = {"completeness": 0.0, "uniqueness": 0.0, "validity": 0.0}
    assert abs(compute_pipeline_health_score(q) - 0.0) < TOL


def test_cphs_with_weights():
    q = {"completeness": 0.5, "uniqueness": 1.0, "validity": 0.5}
    w = {"completeness": 2, "uniqueness": 1, "validity": 1}
    # (2*0.5 + 1*1.0 + 1*0.5) / 4 = 2.5/4 = 0.625
    assert abs(compute_pipeline_health_score(q, w) - 0.625) < TOL


def test_cphs_raises_on_out_of_range():
    q = {"completeness": 1.5, "uniqueness": 0.5, "validity": 0.5}
    with pytest.raises(ValueError):
        compute_pipeline_health_score(q)


def test_cphs_raises_on_missing_key():
    q = {"completeness": 0.5, "uniqueness": 0.5}  # missing validity
    with pytest.raises(ValueError):
        compute_pipeline_health_score(q)


def test_cphs_raises_on_non_positive_weight():
    q = {"completeness": 0.5, "uniqueness": 0.5, "validity": 0.5}
    w = {"completeness": 0, "uniqueness": 1, "validity": 1}
    with pytest.raises(ValueError):
        compute_pipeline_health_score(q, w)


# ============================================================
# F4: combine_cleaning_report (6 cases)
# ============================================================

def test_ccr_basic():
    r = combine_cleaning_report(100, 95, {"missing": 3, "duplicate": 2})
    assert r["rows_in"] == 100
    assert r["rows_out"] == 95
    assert r["rows_dropped"] == 5
    assert r["issues_fixed"] == {"missing": 3, "duplicate": 2}
    assert r["total_issues"] == 5


def test_ccr_no_drops():
    r = combine_cleaning_report(50, 50, {})
    assert r["rows_dropped"] == 0
    assert r["total_issues"] == 0


def test_ccr_all_dropped():
    r = combine_cleaning_report(10, 0, {"outlier": 10})
    assert r["rows_dropped"] == 10


def test_ccr_raises_on_negative():
    with pytest.raises(ValueError):
        combine_cleaning_report(-1, 0, {})


def test_ccr_raises_on_out_gt_in():
    with pytest.raises(ValueError):
        combine_cleaning_report(10, 20, {})


def test_ccr_raises_on_negative_count():
    with pytest.raises(ValueError):
        combine_cleaning_report(10, 5, {"missing": -1})
