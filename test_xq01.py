"""XQ01 evaluator (v2) — 学生学业表现基础统计 (校情) — 4-attack + 5-redline compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_xq01 import (
    compute_pass_rate,
    item_difficulty,
    enrollment_concentration,
    gpa_distribution_buckets,
)

TOL = 1e-6


# ============================================================
# F1: compute_pass_rate (8 测试)
# ============================================================

def test_pr_basic_8_pass_2_fail():
    """10 学生, 8 通过 (>=60) → pass_rate=0.8"""
    grades = [
        {"student_id": "S001", "score": 75}, {"student_id": "S002", "score": 88},
        {"student_id": "S003", "score": 60}, {"student_id": "S004", "score": 45},
        {"student_id": "S005", "score": 92}, {"student_id": "S006", "score": 70},
        {"student_id": "S007", "score": 58}, {"student_id": "S008", "score": 80},
        {"student_id": "S009", "score": 65}, {"student_id": "S010", "score": 71},
    ]
    r = compute_pass_rate(grades, 60)
    assert r == {"pass_count": 8, "fail_count": 2, "pass_rate": 0.8}


def test_pr_all_pass():
    grades = [{"student_id": f"S{i}", "score": 80} for i in range(5)]
    r = compute_pass_rate(grades, 60)
    assert r == {"pass_count": 5, "fail_count": 0, "pass_rate": 1.0}


def test_pr_all_fail():
    grades = [{"student_id": f"S{i}", "score": 30} for i in range(5)]
    r = compute_pass_rate(grades, 60)
    assert r == {"pass_count": 0, "fail_count": 5, "pass_rate": 0.0}


def test_pr_at_threshold_pass():
    """score == threshold 算通过 (>=)"""
    grades = [{"student_id": "S001", "score": 60}]
    r = compute_pass_rate(grades, 60)
    assert r == {"pass_count": 1, "fail_count": 0, "pass_rate": 1.0}


def test_pr_custom_threshold_70():
    """同样 grades, threshold 提到 70: 6 通过 (75/88/92/70/80/71)"""
    grades = [
        {"student_id": "S001", "score": 75}, {"student_id": "S002", "score": 88},
        {"student_id": "S003", "score": 60}, {"student_id": "S004", "score": 45},
        {"student_id": "S005", "score": 92}, {"student_id": "S006", "score": 70},
        {"student_id": "S007", "score": 58}, {"student_id": "S008", "score": 80},
        {"student_id": "S009", "score": 65}, {"student_id": "S010", "score": 71},
    ]
    r = compute_pass_rate(grades, 70)
    assert r == {"pass_count": 6, "fail_count": 4, "pass_rate": 0.6}


def test_pr_single_student():
    """边界: 单学生"""
    r = compute_pass_rate([{"student_id": "S001", "score": 95}], 60)
    assert r == {"pass_count": 1, "fail_count": 0, "pass_rate": 1.0}


def test_pr_raises_on_empty():
    with pytest.raises(ValueError):
        compute_pass_rate([], 60)


def test_pr_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_pass_rate("not a list", 60)


# ============================================================
# F2: item_difficulty (8 测试)
# ============================================================

def test_id_basic_avg_70():
    """[60, 70, 80] avg=70, max=100 → P=0.7"""
    p = item_difficulty([60, 70, 80], 100)
    assert abs(p - 0.7) < TOL


def test_id_all_zeros():
    """全 0 → P=0.0"""
    p = item_difficulty([0, 0, 0, 0, 0], 100)
    assert abs(p - 0.0) < TOL


def test_id_all_full_marks():
    """全满 → P=1.0"""
    p = item_difficulty([100, 100, 100], 100)
    assert abs(p - 1.0) < TOL


def test_id_mixed_avg_78():
    """[50, 75, 80, 90, 95] avg=78 → P=0.78"""
    p = item_difficulty([50, 75, 80, 90, 95], 100)
    assert abs(p - 0.78) < TOL


def test_id_custom_max_score():
    """[40, 60, 80] avg=60, max=80 → P=0.75"""
    p = item_difficulty([40, 60, 80], 80)
    assert abs(p - 0.75) < TOL


def test_id_single_score():
    """单元素 [85] / 100 → 0.85"""
    p = item_difficulty([85], 100)
    assert abs(p - 0.85) < TOL


def test_id_raises_on_empty():
    with pytest.raises(ValueError):
        item_difficulty([], 100)


def test_id_raises_on_non_list():
    with pytest.raises(TypeError):
        item_difficulty("abc", 100)


# ============================================================
# F3: enrollment_concentration (8 测试)
# ============================================================

def test_ec_basic_4_courses():
    """[50, 20, 20, 10] HHI = 0.25+0.04+0.04+0.01 = 0.34 (与 handbook 案例不同, 防 hardcode 反查)"""
    courses = [{"course_id": f"C{i}", "enroll_count": ec} for i, ec in enumerate([50, 20, 20, 10])]
    r = enrollment_concentration(courses)
    assert abs(r - 0.34) < TOL


def test_ec_fully_concentrated():
    """单课 [100] → HHI = 1.0"""
    r = enrollment_concentration([{"course_id": "C1", "enroll_count": 100}])
    assert abs(r - 1.0) < TOL


def test_ec_uniform_4_equal():
    """[25, 25, 25, 25] → HHI = 4 * 0.25^2 = 0.25"""
    courses = [{"course_id": f"C{i}", "enroll_count": 25} for i in range(4)]
    r = enrollment_concentration(courses)
    assert abs(r - 0.25) < TOL


def test_ec_dominant_course():
    """[80, 10, 10] → HHI = 0.64+0.01+0.01 = 0.66"""
    courses = [{"course_id": f"C{i}", "enroll_count": ec} for i, ec in enumerate([80, 10, 10])]
    r = enrollment_concentration(courses)
    assert abs(r - 0.66) < TOL


def test_ec_two_course_uneven():
    """[60, 40] → HHI = 0.36+0.16 = 0.52"""
    courses = [{"course_id": f"C{i}", "enroll_count": ec} for i, ec in enumerate([60, 40])]
    r = enrollment_concentration(courses)
    assert abs(r - 0.52) < TOL


def test_ec_very_dispersed():
    """10 个均 10 → HHI = 10 * 0.01 = 0.1"""
    courses = [{"course_id": f"C{i}", "enroll_count": 10} for i in range(10)]
    r = enrollment_concentration(courses)
    assert abs(r - 0.1) < TOL


def test_ec_raises_on_empty():
    with pytest.raises(ValueError):
        enrollment_concentration([])


def test_ec_raises_on_zero_total():
    """全 0 enroll → ValueError"""
    with pytest.raises(ValueError):
        enrollment_concentration([
            {"course_id": "C1", "enroll_count": 0},
            {"course_id": "C2", "enroll_count": 0},
        ])


# ============================================================
# F4: gpa_distribution_buckets (8 测试)
# ============================================================

def test_gpa_basic_5_buckets():
    """10 GPA, buckets [0,1,2,3,4]: 0.5/1.0/1.5/2.0/2.5/2.8/3.0/3.2/3.5/4.0
    → [0,1):1, [1,2):2, [2,3):3, [3,4]:4"""
    gpas = [0.5, 1.5, 2.5, 3.0, 3.5, 4.0, 2.0, 1.0, 3.2, 2.8]
    r = gpa_distribution_buckets(gpas, [0, 1.0, 2.0, 3.0, 4.0])
    assert r == {"0.00-1.00": 1, "1.00-2.00": 2, "2.00-3.00": 3, "3.00-4.00": 4}


def test_gpa_all_in_one_bucket():
    """全在 [3,4] 段"""
    r = gpa_distribution_buckets([3.2, 3.5, 3.8, 3.0, 4.0], [0, 1.0, 2.0, 3.0, 4.0])
    assert r == {"0.00-1.00": 0, "1.00-2.00": 0, "2.00-3.00": 0, "3.00-4.00": 5}


def test_gpa_uniform_4_buckets():
    """每段 1 个"""
    r = gpa_distribution_buckets([0.5, 1.5, 2.5, 3.5], [0, 1.0, 2.0, 3.0, 4.0])
    assert r == {"0.00-1.00": 1, "1.00-2.00": 1, "2.00-3.00": 1, "3.00-4.00": 1}


def test_gpa_left_inclusive_right_exclusive():
    """gpa==1.0 落在 [1,2) 而不是 [0,1)"""
    r = gpa_distribution_buckets([1.0, 2.0, 3.0], [0, 1.0, 2.0, 3.0, 4.0])
    assert r == {"0.00-1.00": 0, "1.00-2.00": 1, "2.00-3.00": 1, "3.00-4.00": 1}


def test_gpa_last_bucket_inclusive():
    """gpa==4.0 (max) 落在最后桶 [3,4]"""
    r = gpa_distribution_buckets([4.0], [0, 1.0, 2.0, 3.0, 4.0])
    assert r == {"0.00-1.00": 0, "1.00-2.00": 0, "2.00-3.00": 0, "3.00-4.00": 1}


def test_gpa_custom_2_buckets():
    """[0, 2.5, 4.0] 仅 2 桶"""
    r = gpa_distribution_buckets([1.0, 2.0, 3.0, 4.0], [0, 2.5, 4.0])
    # 1.0, 2.0 ∈ [0, 2.5) → 2; 3.0, 4.0 ∈ [2.5, 4.0] → 2
    assert r == {"0.00-2.50": 2, "2.50-4.00": 2}


def test_gpa_raises_on_empty():
    with pytest.raises(ValueError):
        gpa_distribution_buckets([], [0, 1.0, 2.0, 3.0, 4.0])


def test_gpa_raises_on_buckets_not_increasing():
    with pytest.raises(ValueError):
        gpa_distribution_buckets([1.0, 2.0], [4.0, 2.0, 1.0])
