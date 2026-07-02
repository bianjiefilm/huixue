"""
Unit tests for backend/app/utils/usage_format.py — pure formatting functions.
"""
import pytest
from datetime import date, datetime
from app.utils.usage_format import (
    get_date_range,
    format_course_stat,
    format_practice_stat,
    format_training_stat,
    format_teacher_stat,
    format_student_stat,
    format_export_filename,
)


# Fix "today" for deterministic tests
FIXED_TODAY = date(2026, 4, 16)


class TestGetDateRange:

    def test_today(self):
        s, e = get_date_range("today", today=FIXED_TODAY)
        assert s == e == FIXED_TODAY

    def test_yesterday(self):
        s, e = get_date_range("yesterday", today=FIXED_TODAY)
        assert s == e == date(2026, 4, 15)

    def test_last_7_days(self):
        s, e = get_date_range("last_7_days", today=FIXED_TODAY)
        assert e == FIXED_TODAY
        assert (e - s).days == 6

    def test_last_30_days(self):
        s, e = get_date_range("last_30_days", today=FIXED_TODAY)
        assert (e - s).days == 29

    def test_custom(self):
        s, e = get_date_range("custom", "2026-01-01", "2026-01-31", today=FIXED_TODAY)
        assert s == date(2026, 1, 1)
        assert e == date(2026, 1, 31)

    def test_custom_missing_dates_falls_back(self):
        s, e = get_date_range("custom", None, None, today=FIXED_TODAY)
        # should fall back to last_7_days
        assert (e - s).days == 6

    def test_unknown_range_defaults(self):
        s, e = get_date_range("bogus", today=FIXED_TODAY)
        assert (e - s).days == 6

    def test_no_today_override_runs(self):
        # should not crash when today is None (uses real date)
        s, e = get_date_range("today")
        assert s == e


class TestFormatCourseStat:

    def test_basic(self):
        r = format_course_stat(1, "Python入门", 3)
        assert r["course_id"] == 1
        assert r["course_name"] == "Python入门"
        assert r["access_count"] == 16  # 10 + 3*2
        assert r["course_type"] == "PRACTICE"
        assert r["created_at"] == ""

    def test_with_created_at(self):
        dt = datetime(2026, 1, 1, 12, 0, 0)
        r = format_course_stat(2, "SQL", 1, created_at=dt)
        assert r["created_at"] == "2026-01-01T12:00:00"

    def test_idx_1(self):
        r = format_course_stat(10, "X", 1)
        assert r["access_count"] == 12
        assert r["classroom_creation_count"] == 1


class TestFormatPracticeStat:

    def test_basic(self):
        r = format_practice_stat(5, "实验1", 2)
        assert r["practice_id"] == 5
        assert r["access_count"] == 21  # 15 + 2*3
        assert r["learning_duration"] == 21 * 15

    def test_idx_1(self):
        r = format_practice_stat(1, "P", 1)
        assert r["access_count"] == 18


class TestFormatTrainingStat:

    def test_basic(self):
        r = format_training_stat(3, "实训A", 2)
        assert r["training_id"] == 3
        assert r["access_count"] == 28  # 20 + 2*4
        assert r["learning_duration"] == 28 * 30


class TestFormatTeacherStat:

    def test_fields(self):
        r = format_teacher_stat(4, "张老师", "T001", 3, 5)
        assert r["teacher_id"] == 4
        assert r["real_name"] == "张老师"
        assert r["classroom_count"] == 3
        assert r["practice_count"] == 5
        assert r["personal_practice_count"] == 5
        assert r["training_count"] == 0


class TestFormatStudentStat:

    def test_fields(self):
        r = format_student_stat(5, "李同学", "S001", 10, 2)
        assert r["student_id"] == 5
        assert r["login_count"] == 9  # 5 + 2*2
        assert r["practice_start_count"] == 10
        assert r["practice_learning_duration"] == 200  # 10*20


class TestFormatExportFilename:

    def test_known_type(self):
        fn = format_export_filename("course", "xlsx", timestamp="20260416_120000")
        assert fn == "课程统计_20260416_120000.xlsx"

    def test_unknown_type(self):
        fn = format_export_filename("unknown", "csv", timestamp="20260416_120000")
        assert fn == "统计_20260416_120000.csv"

    def test_auto_timestamp(self):
        fn = format_export_filename("teacher")
        assert fn.startswith("教师使用统计_")
        assert fn.endswith(".xlsx")
