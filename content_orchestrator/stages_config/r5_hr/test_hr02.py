import importlib
import os

import pytest

MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_hr02")
student = importlib.import_module(MODULE_NAME)

CANDIDATES = [
    {"candidate_id": "C1", "role": "Engineer", "stage": "applied"},
    {"candidate_id": "C2", "role": "Engineer", "stage": "screen"},
    {"candidate_id": "C3", "role": "Engineer", "stage": "interview"},
    {"candidate_id": "C4", "role": "Engineer", "stage": "offer"},
    {"candidate_id": "C5", "role": "Engineer", "stage": "hired"},
    {"candidate_id": "C6", "role": "Sales", "stage": "screen"},
    {"candidate_id": "C7", "role": "Sales", "stage": "interview"},
    {"candidate_id": "C8", "role": "Sales", "stage": "interview"},
]


def _result():
    return student.analyze_recruiting_funnel(CANDIDATES)


def test_sorted_by_applied_count():
    assert [row["role"] for row in _result()] == ["Engineer", "Sales"]


def test_fields_present():
    assert set(_result()[0]) == {"role", "applied", "screen_rate", "interview_rate", "offer_rate", "hire_rate", "bottleneck"}


def test_engineer_rates():
    eng = _result()[0]
    assert eng["applied"] == 5
    assert eng["screen_rate"] == 0.8
    assert eng["interview_rate"] == 0.75
    assert eng["offer_rate"] == 0.6667
    assert eng["hire_rate"] == 0.5
    assert eng["bottleneck"] == "hire"


def test_sales_rates():
    sales = _result()[1]
    assert sales["applied"] == 3
    assert sales["screen_rate"] == 1.0
    assert sales["interview_rate"] == 0.6667
    assert sales["offer_rate"] == 0.0
    assert sales["bottleneck"] == "offer"


def test_rejects_non_list():
    with pytest.raises(ValueError):
        student.analyze_recruiting_funnel({})


def test_ignores_bad_rows_and_unknown_stage():
    result = student.analyze_recruiting_funnel(["bad", {}, {"role": ""}, {"role": "A", "stage": "bad"}, {"role": "A", "stage": "hired"}])
    assert result[0]["applied"] == 1
    assert result[0]["hire_rate"] == 1.0


def test_tie_break_by_role_name():
    result = student.analyze_recruiting_funnel([{"role": "B", "stage": "applied"}, {"role": "A", "stage": "applied"}])
    assert [row["role"] for row in result] == ["A", "B"]


def test_single_applied_bottleneck_screen():
    row = student.analyze_recruiting_funnel([{"role": "A", "stage": "applied"}])[0]
    assert row["screen_rate"] == 0.0
    assert row["bottleneck"] == "screen"


def test_offer_without_hire():
    row = student.analyze_recruiting_funnel([{"role": "A", "stage": "offer"}])[0]
    assert row["offer_rate"] == 1.0
    assert row["hire_rate"] == 0.0


def test_interview_stage_counts_prior_stages():
    row = student.analyze_recruiting_funnel([{"role": "A", "stage": "interview"}])[0]
    assert row["screen_rate"] == 1.0
    assert row["interview_rate"] == 1.0


def test_empty_input():
    assert student.analyze_recruiting_funnel([]) == []


def test_whitespace_role_trimmed():
    assert student.analyze_recruiting_funnel([{"role": " A ", "stage": "applied"}])[0]["role"] == "A"


def test_case_sensitive_unknown_stage_ignored():
    assert student.analyze_recruiting_funnel([{"role": "A", "stage": "Hired"}]) == []


def test_multiple_hired_all_rates_one():
    row = student.analyze_recruiting_funnel([{"role": "A", "stage": "hired"}, {"role": "A", "stage": "hired"}])[0]
    assert row["screen_rate"] == 1.0
    assert row["hire_rate"] == 1.0


def test_role_with_zero_offer_has_offer_bottleneck():
    row = student.analyze_recruiting_funnel([{"role": "A", "stage": "interview"}, {"role": "A", "stage": "interview"}])[0]
    assert row["bottleneck"] == "offer"
