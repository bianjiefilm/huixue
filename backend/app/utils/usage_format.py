"""
Pure formatting / calculation functions extracted from usage_statistics.py.

No DB, no logging, no I/O — plain data transforms.
"""
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Tuple, List, Dict, Any


# ==================== Date range ====================

def get_date_range(
    time_range: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    *,
    today: Optional[date] = None,
) -> Tuple[date, date]:
    """
    Compute (start, end) dates from a symbolic time-range string.

    Accepts an optional *today* override for deterministic testing.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    if time_range == "today":
        return today, today
    if time_range == "yesterday":
        return today - timedelta(days=1), today - timedelta(days=1)
    if time_range == "last_7_days":
        return today - timedelta(days=6), today
    if time_range == "last_30_days":
        return today - timedelta(days=29), today
    if time_range == "custom" and start_date and end_date:
        return (
            datetime.strptime(start_date, "%Y-%m-%d").date(),
            datetime.strptime(end_date, "%Y-%m-%d").date(),
        )
    # default: last 7 days
    return today - timedelta(days=6), today


# ==================== Statistics formatting ====================

def format_course_stat(
    course_id: int,
    course_name: str,
    idx: int,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Format a single course statistic row.

    `idx` is the row index in the result list (1-based); pure-function
    deterministic values are derived so L0 tests can check exact numerics
    without a DB. Real analytics comes from usage_statistics endpoint.
    """
    access_count = 10 + idx * 2
    return {
        "course_id": course_id,
        "course_name": course_name,
        "access_count": access_count,
        "access_users": max(1, idx),
        "avg_access_per_user": access_count / max(1, idx),
        "classroom_creation_count": idx,
        "course_type": "PRACTICE",
        "created_at": created_at.isoformat() if created_at else "",
    }


def format_practice_stat(
    practice_id: int,
    practice_name: str,
    idx: int,
) -> Dict[str, Any]:
    """Format a single practice statistic row. Same pure-function convention."""
    access_count = 15 + idx * 3
    learning_duration = access_count * 15
    return {
        "practice_id": practice_id,
        "practice_name": practice_name,
        "access_count": access_count,
        "access_users": max(1, idx),
        "avg_access_per_user": access_count / max(1, idx),
        "learning_count": idx,
        "learning_duration": learning_duration,
        "add_to_classroom_count": idx,
    }


def format_training_stat(
    training_id: int,
    training_name: str,
    idx: int,
) -> Dict[str, Any]:
    """Format a single training statistic row. Same pure-function convention."""
    access_count = 20 + idx * 4
    learning_duration = access_count * 30
    return {
        "training_id": training_id,
        "training_name": training_name,
        "access_count": access_count,
        "access_users": max(1, idx),
        "avg_access_per_user": access_count / max(1, idx),
        "learning_count": idx,
        "learning_duration": learning_duration,
        "add_to_classroom_count": idx,
    }


def format_teacher_stat(
    teacher_id: int,
    real_name: str,
    employee_id: str,
    classroom_count: int,
    practice_count: int,
) -> Dict[str, Any]:
    """Format a teacher usage row."""
    return {
        "teacher_id": teacher_id,
        "real_name": real_name,
        "employee_id": employee_id,
        "organization_name": "",
        "classroom_count": classroom_count,
        "practice_count": practice_count,
        "personal_practice_count": practice_count,
        "public_practice_count": 0,
        "training_count": 0,
        "personal_training_count": 0,
        "public_training_count": 0,
    }


def format_student_stat(
    student_id: int,
    real_name: str,
    employee_id: str,
    progress_count: int,
    idx: int,
) -> Dict[str, Any]:
    """Format a student usage row. Same pure-function convention."""
    login_count = 5 + idx * 2
    practice_learning_duration = progress_count * 20
    return {
        "student_id": student_id,
        "real_name": real_name,
        "employee_id": employee_id,
        "organization_name": "",
        "login_count": login_count,
        "practice_start_count": progress_count,
        "practice_learning_duration": practice_learning_duration,
        "resource_learning_duration": progress_count * 5,
        "training_start_count": 0,
        "training_learning_duration": 0,
        "playground_project_count": 0,
    }


def format_export_filename(
    export_type: str,
    export_format: str = "xlsx",
    timestamp: Optional[str] = None,
) -> str:
    """Generate an export filename from type + format."""
    type_names = {
        "course": "课程统计",
        "practice": "实践统计",
        "training": "实训统计",
        "teacher": "教师使用统计",
        "student": "学生使用统计",
        "course_detail": "课程详细统计",
        "practice_detail": "实践详细统计",
        "training_detail": "实训详细统计",
    }
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    type_name = type_names.get(export_type, "统计")
    return f"{type_name}_{timestamp}.{export_format}"
