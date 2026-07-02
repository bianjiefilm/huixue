"""
Pure helper functions for the Project Canvas feature.

Extracted from api/v1/endpoints/project_canvas.py.
No DB, no logging — plain data transforms.
"""
from typing import List, Dict, Optional, Union


# ==================== Status / color / size ====================

STATUS_COLOR_MAP = {
    "completed": "#22c55e",
    "in_progress": "#3b82f6",
    "warning": "#ef4444",
    "pending": "#f59e0b",
    "default": "#6b7280",
}


def get_status_color(status: str) -> str:
    """Map a node status string to its hex colour."""
    return STATUS_COLOR_MAP.get(status, "#6b7280")


def node_status_from_publish(publish_status: str) -> str:
    """
    Derive canvas node status from a training's publish_status value.

    Accepts the *string* value of TrainingPublishStatusEnum.
    """
    mapping = {
        "PUBLISHED": "completed",
        "PENDING_APPROVAL": "warning",
        "EDITING": "in_progress",
    }
    return mapping.get(publish_status, "default")


def node_size_from_hours(course_hours: Optional[Union[float, int]]) -> str:
    """Derive node size from course hours."""
    if course_hours is not None and course_hours >= 10:
        return "large"
    if course_hours is not None and course_hours >= 5:
        return "medium"
    return "small"


# ==================== Layout ====================

_POSITION_TEMPLATES: List[Dict[str, float]] = [
    {"x": 50, "y": 45},
    {"x": 42, "y": 18},
    {"x": 58, "y": 18},
    {"x": 28, "y": 38},
    {"x": 72, "y": 38},
    {"x": 22, "y": 58},
    {"x": 78, "y": 58},
    {"x": 35, "y": 75},
    {"x": 65, "y": 75},
    {"x": 15, "y": 45},
    {"x": 85, "y": 45},
    {"x": 50, "y": 85},
]


def distribute_nodes_deterministic(count: int) -> List[Dict[str, float]]:
    """
    Return *count* (x, y) positions for canvas nodes.

    Uses the fixed template positions; for overflow nodes a simple
    deterministic spread is used (no random).
    """
    positions = [_POSITION_TEMPLATES[i] for i in range(min(count, len(_POSITION_TEMPLATES)))]
    # Deterministic overflow positions in a grid pattern
    cols = 5
    for extra in range(max(0, count - len(_POSITION_TEMPLATES))):
        row, col = divmod(extra, cols)
        positions.append({
            "x": 20 + col * 15,
            "y": 20 + row * 15,
        })
    return positions


# ==================== Misc pure helpers ====================

def calculate_semester(year: int, month: int) -> str:
    """
    Compute semester string from year + month.

    Rule: before July → spring; July onward → autumn.
    """
    if month < 7:
        return f"{year}年春季"
    return f"{year}年秋季"


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_assessment_info(assessment_type: str) -> Dict:
    """
    Map an assessment type string to its display info.

    Pure — no ORM.
    """
    mapping = {
        "midterm_exam": {"type": "期中考试", "questions": 32, "score": 100, "duration": "120分钟"},
        "期中考试":      {"type": "期中考试", "questions": 32, "score": 100, "duration": "120分钟"},
        "final_exam":   {"type": "期末考试", "questions": 30, "score": 100, "duration": "150分钟"},
        "期末考试":      {"type": "期末考试", "questions": 30, "score": 100, "duration": "150分钟"},
        "question_bank": {"type": "题库", "questions": 150, "score": "—", "duration": "—"},
        "题库":          {"type": "题库", "questions": 150, "score": "—", "duration": "—"},
        "exam_config":  {"type": "考试配置", "questions": "—", "score": "—", "duration": "—"},
        "考试配置":      {"type": "考试配置", "questions": "—", "score": "—", "duration": "—"},
        "unit_test":    {"type": "单元测验", "questions": 20, "score": 100, "duration": "60分钟"},
        "单元测验":      {"type": "单元测验", "questions": 20, "score": 100, "duration": "60分钟"},
        "project":      {"type": "项目评估", "questions": "—", "score": 100, "duration": "—"},
        "项目评估":      {"type": "项目评估", "questions": "—", "score": 100, "duration": "—"},
    }
    return mapping.get(assessment_type, {"type": assessment_type or "实验考试", "questions": "—", "score": 100, "duration": "120分钟"})
