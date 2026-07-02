"""
canvas_helpers.py 纯函数单元测试

覆盖: get_status_color, node_status_from_publish, node_size_from_hours,
       distribute_nodes_deterministic, calculate_semester, format_file_size,
       format_assessment_info
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

    def test_warning(self):
        assert get_status_color("warning") == "#ef4444"

    def test_pending(self):
        assert get_status_color("pending") == "#f59e0b"

    def test_default(self):
        assert get_status_color("default") == "#6b7280"

    def test_unknown_returns_default(self):
        assert get_status_color("nonexistent") == "#6b7280"

    def test_empty(self):
        assert get_status_color("") == "#6b7280"


class TestNodeStatusFromPublish:

    def test_published(self):
        assert node_status_from_publish("PUBLISHED") == "completed"

    def test_pending_approval(self):
        assert node_status_from_publish("PENDING_APPROVAL") == "warning"

    def test_editing(self):
        assert node_status_from_publish("EDITING") == "in_progress"

    def test_unknown(self):
        assert node_status_from_publish("DRAFT") == "default"

    def test_empty(self):
        assert node_status_from_publish("") == "default"


class TestNodeSizeFromHours:

    def test_large(self):
        assert node_size_from_hours(10) == "large"
        assert node_size_from_hours(20) == "large"

    def test_medium(self):
        assert node_size_from_hours(5) == "medium"
        assert node_size_from_hours(9) == "medium"

    def test_small(self):
        assert node_size_from_hours(4) == "small"
        assert node_size_from_hours(1) == "small"

    def test_zero(self):
        assert node_size_from_hours(0) == "small"

    def test_none(self):
        assert node_size_from_hours(None) == "small"

    def test_float(self):
        assert node_size_from_hours(10.5) == "large"
        assert node_size_from_hours(4.9) == "small"


class TestDistributeNodesDeterministic:

    def test_zero_nodes(self):
        assert distribute_nodes_deterministic(0) == []

    def test_one_node(self):
        result = distribute_nodes_deterministic(1)
        assert len(result) == 1
        assert result[0] == {"x": 50, "y": 45}

    def test_twelve_nodes_all_template(self):
        result = distribute_nodes_deterministic(12)
        assert len(result) == 12

    def test_overflow_nodes(self):
        result = distribute_nodes_deterministic(15)
        assert len(result) == 15
        # First 12 from template, 3 overflow
        overflow = result[12:]
        assert len(overflow) == 3

    def test_all_positions_have_xy(self):
        for n in [1, 5, 12, 20]:
            positions = distribute_nodes_deterministic(n)
            for pos in positions:
                assert "x" in pos and "y" in pos


class TestCalculateSemester:

    def test_spring(self):
        assert calculate_semester(2024, 3) == "2024年春季"
        assert calculate_semester(2024, 1) == "2024年春季"
        assert calculate_semester(2024, 6) == "2024年春季"

    def test_autumn(self):
        assert calculate_semester(2024, 7) == "2024年秋季"
        assert calculate_semester(2024, 9) == "2024年秋季"
        assert calculate_semester(2024, 12) == "2024年秋季"

    def test_boundary(self):
        assert calculate_semester(2025, 6) == "2025年春季"
        assert calculate_semester(2025, 7) == "2025年秋季"


class TestFormatFileSize:

    def test_bytes(self):
        assert format_file_size(500) == "500 B"
        assert format_file_size(0) == "0 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_boundary_kb(self):
        assert format_file_size(1023) == "1023 B"
        assert "KB" in format_file_size(1024)


class TestFormatAssessmentInfo:

    def test_midterm_exam(self):
        r = format_assessment_info("midterm_exam")
        assert r["type"] == "期中考试"
        assert r["questions"] == 32

    def test_midterm_cn(self):
        r = format_assessment_info("期中考试")
        assert r["type"] == "期中考试"

    def test_final_exam(self):
        r = format_assessment_info("final_exam")
        assert r["type"] == "期末考试"

    def test_unit_test(self):
        r = format_assessment_info("unit_test")
        assert r["type"] == "单元测验"
        assert r["duration"] == "60分钟"

    def test_unknown_type(self):
        r = format_assessment_info("custom_type")
        assert r["type"] == "custom_type"
        assert r["score"] == 100

    def test_none_type(self):
        r = format_assessment_info(None)
        assert r["type"] == "实验考试"
