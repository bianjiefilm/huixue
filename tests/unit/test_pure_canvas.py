"""
Unit tests for backend/app/utils/canvas_helpers.py — canvas + misc pure helpers.
"""
import pytest
from app.utils.canvas_helpers import (
    get_status_color,
    node_status_from_publish,
    node_size_from_hours,
    distribute_nodes_deterministic,
    calculate_semester,
    format_file_size,
    format_assessment_info,
)


class TestGetStatusColor:

    def test_completed(self):
        assert get_status_color("completed") == "#22c55e"

    def test_in_progress(self):
        assert get_status_color("in_progress") == "#3b82f6"

    def test_unknown_falls_back(self):
        assert get_status_color("nonexistent") == "#6b7280"


class TestNodeStatusFromPublish:

    def test_published(self):
        assert node_status_from_publish("PUBLISHED") == "completed"

    def test_editing(self):
        assert node_status_from_publish("EDITING") == "in_progress"

    def test_pending_approval(self):
        assert node_status_from_publish("PENDING_APPROVAL") == "warning"

    def test_unknown(self):
        assert node_status_from_publish("WHATEVER") == "default"


class TestNodeSizeFromHours:

    def test_large(self):
        assert node_size_from_hours(10) == "large"
        assert node_size_from_hours(20) == "large"

    def test_medium(self):
        assert node_size_from_hours(5) == "medium"
        assert node_size_from_hours(9) == "medium"

    def test_small(self):
        assert node_size_from_hours(4) == "small"
        assert node_size_from_hours(0) == "small"

    def test_none(self):
        assert node_size_from_hours(None) == "small"


class TestDistributeNodes:

    def test_zero(self):
        assert distribute_nodes_deterministic(0) == []

    def test_one(self):
        pos = distribute_nodes_deterministic(1)
        assert len(pos) == 1
        assert pos[0] == {"x": 50, "y": 45}

    def test_twelve_uses_all_templates(self):
        pos = distribute_nodes_deterministic(12)
        assert len(pos) == 12

    def test_overflow_deterministic(self):
        pos = distribute_nodes_deterministic(15)
        assert len(pos) == 15
        # overflow positions should be deterministic
        pos2 = distribute_nodes_deterministic(15)
        assert pos == pos2


class TestCalculateSemester:

    def test_spring(self):
        assert calculate_semester(2026, 3) == "2026年春季"

    def test_june_is_spring(self):
        assert calculate_semester(2026, 6) == "2026年春季"

    def test_july_is_autumn(self):
        assert calculate_semester(2026, 7) == "2026年秋季"

    def test_december_is_autumn(self):
        assert calculate_semester(2025, 12) == "2025年秋季"

    def test_january_is_spring(self):
        assert calculate_semester(2026, 1) == "2026年春季"


class TestFormatFileSize:

    def test_bytes(self):
        assert format_file_size(500) == "500 B"

    def test_kb(self):
        assert format_file_size(2048) == "2.0 KB"

    def test_mb(self):
        assert format_file_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gb(self):
        assert format_file_size(2 * 1024 * 1024 * 1024) == "2.0 GB"

    def test_zero(self):
        assert format_file_size(0) == "0 B"


class TestFormatAssessmentInfo:

    def test_midterm_en(self):
        r = format_assessment_info("midterm_exam")
        assert r["type"] == "期中考试"

    def test_midterm_cn(self):
        r = format_assessment_info("期中考试")
        assert r["type"] == "期中考试"

    def test_unit_test(self):
        r = format_assessment_info("unit_test")
        assert r["questions"] == 20

    def test_unknown_type(self):
        r = format_assessment_info("custom_quiz")
        assert r["type"] == "custom_quiz"
        assert r["score"] == 100

    def test_empty_string(self):
        r = format_assessment_info("")
        assert r["type"] == "实验考试"

    def test_question_bank(self):
        r = format_assessment_info("question_bank")
        assert r["questions"] == 150
