"""
Pure enum/label mapping functions.

Extracted from utils/database_mapper.py — no DB, no I/O.
"""
from typing import Dict


# ==================== Difficulty ====================

_DIFFICULTY_MAP: Dict[str, str] = {
    "初级": "beginner",
    "中级": "intermediate",
    "高级": "advanced",
    "专家": "advanced",
}


def map_difficulty(ai_difficulty: str) -> str:
    """Map Chinese difficulty label to enum value. Default: intermediate."""
    return _DIFFICULTY_MAP.get(ai_difficulty, "intermediate")


# ==================== Task type ====================

_TASK_TYPE_MAP: Dict[str, str] = {
    "实践题": "PRACTICE",
    "选择题": "CHOICE",
    "判断题": "JUDGE",
    "编程题": "PRACTICE",
    "单选题": "CHOICE",
    "多选题": "CHOICE",
}


def map_task_type(ai_type: str) -> str:
    """Map Chinese task type name to enum value. Default: PRACTICE."""
    return _TASK_TYPE_MAP.get(ai_type, "PRACTICE")


# ==================== Question type ====================

_QUESTION_TYPE_MAP: Dict[str, str] = {
    "单选题": "SINGLE_CHOICE",
    "多选题": "MULTIPLE_CHOICE",
    "判断题": "TRUE_FALSE",
    "选择题": "SINGLE_CHOICE",
    "填空题": "FILL_BLANK",
    "简答题": "SHORT_ANSWER",
}


def map_question_type(ai_type: str) -> str:
    """Map Chinese question type name to enum value. Default: SINGLE_CHOICE."""
    return _QUESTION_TYPE_MAP.get(ai_type, "SINGLE_CHOICE")
