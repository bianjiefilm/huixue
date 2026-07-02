"""
Unit tests for backend/app/core/validators.py — pure validation functions.
"""
import pytest
from app.core.validators import (
    sanitize_html,
    validate_file_extension,
    validate_sql_identifier,
)


class TestSanitizeHtml:

    def test_removes_script(self):
        assert "<script" not in sanitize_html('<div><script>alert(1)</script></div>')

    def test_removes_style(self):
        assert "<style" not in sanitize_html('<style>body{color:red}</style><p>hi</p>')

    def test_removes_iframe(self):
        assert "<iframe" not in sanitize_html('<iframe src="x"></iframe>')

    def test_removes_event_handlers(self):
        result = sanitize_html('<img onerror="alert(1)" src="x">')
        assert "onerror" not in result

    def test_preserves_safe_html(self):
        safe = "<p>Hello <b>world</b></p>"
        assert sanitize_html(safe) == safe

    def test_empty_string(self):
        assert sanitize_html("") == ""

    def test_none_returns_none(self):
        assert sanitize_html(None) is None


class TestValidateFileExtension:

    ALLOWED = [".pdf", ".doc", ".docx", ".xlsx"]

    def test_valid_pdf(self):
        assert validate_file_extension("report.pdf", self.ALLOWED) is True

    def test_valid_docx(self):
        assert validate_file_extension("essay.docx", self.ALLOWED) is True

    def test_invalid_exe(self):
        assert validate_file_extension("virus.exe", self.ALLOWED) is False

    def test_case_insensitive(self):
        assert validate_file_extension("REPORT.PDF", self.ALLOWED) is True

    def test_no_extension(self):
        assert validate_file_extension("readme", self.ALLOWED) is False

    def test_empty_filename(self):
        assert validate_file_extension("", self.ALLOWED) is False

    def test_none_filename(self):
        assert validate_file_extension(None, self.ALLOWED) is False


class TestValidateSqlIdentifier:

    def test_valid(self):
        assert validate_sql_identifier("users") is True

    def test_underscore(self):
        assert validate_sql_identifier("student_course_progress") is True

    def test_starts_with_number(self):
        assert validate_sql_identifier("1table") is False

    def test_injection(self):
        assert validate_sql_identifier("users; DROP TABLE --") is False

    def test_empty(self):
        assert validate_sql_identifier("") is False

    def test_none(self):
        assert validate_sql_identifier(None) is False
