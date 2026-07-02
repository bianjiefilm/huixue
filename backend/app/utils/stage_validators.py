"""
Pure validation functions for stage/level (关卡) data.

Extracted from crud/stage_crud.py — no DB, no I/O.
"""
from typing import List, Dict, Any, Optional, Tuple


def validate_stage_fields(stage_data: dict) -> Tuple[List[str], List[str]]:
    """
    Validate stage data fields (pure — no DB lookups).

    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    task_info = stage_data.get("task_info", {})

    # Title length
    title = task_info.get("title", "")
    if len(title) > 60:
        errors.append("关卡名称不能超过60个字符")

    # Skills count
    skills = task_info.get("skills", [])
    if len(skills) > 5:
        errors.append("技能标签最多设置5个")

    # Practice-type settings
    task_type = task_info.get("task_type")
    if task_type == "PRACTICE":
        task_settings = stage_data.get("task_settings", {})

        timeout = task_settings.get("evaluation_timeout_seconds", 20)
        if not (1 <= timeout <= 300):
            errors.append("评测时长限制必须在1-300秒之间")

        if not task_settings.get("evaluation_script_path"):
            errors.append("评测执行文件不能为空")

        if not task_settings.get("evaluation_command"):
            errors.append("评测执行命令不能为空")

        test_cases = stage_data.get("test_cases", [])
        if not (1 <= len(test_cases) <= 10):
            errors.append("测试集数量必须在1-10个之间")

    # Answer info
    answer_info = stage_data.get("answer_info", {})
    if not answer_info.get("answer_title", "").strip():
        errors.append("答案标题不能为空")

    return errors, warnings


def check_duplicate_skills(
    new_skills: List[str],
    existing_skills_sets: List[List[str]],
) -> List[str]:
    """
    Check if any of *new_skills* already appear in *existing_skills_sets*.

    Returns list of duplicate skill names.
    """
    used = set()
    for skill_list in existing_skills_sets:
        used.update(skill_list)
    return sorted(set(new_skills) & used)


def validate_question_stage_fields(stage_data: dict) -> Tuple[List[str], List[str]]:
    """
    Validate question-type stage data (单选/多选/判断).

    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    question_data = stage_data.get("question_data", {})
    question_type = question_data.get("question_type", "")

    if not question_data.get("question_content", "").strip():
        errors.append("题目内容不能为空")

    if question_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE"):
        choices = question_data.get("choices", [])
        if len(choices) < 2:
            errors.append("选择题至少需要2个选项")
        if len(choices) > 10:
            errors.append("选择题��多10个选项")

        correct_count = sum(1 for c in choices if c.get("is_correct"))
        if question_type == "SINGLE_CHOICE" and correct_count != 1:
            errors.append("单选题必须有且仅有1个正确答案")
        if question_type == "MULTIPLE_CHOICE" and correct_count < 2:
            errors.append("多选题至少需要2个正确答案")

    elif question_type == "TRUE_FALSE":
        if "correct_answer" not in question_data:
            errors.append("判断题必须指定正确答案")

    return errors, warnings


# ==================== Stage templates (pure data) ====================

STAGE_TEMPLATES = [
    {
        "id": "python_basic",
        "name": "Python基础编程",
        "description": "适用于Python基础语法练习",
        "task_type": "PRACTICE",
        "difficulty": "初级",
        "template_content": {
            "handbook_markdown": "# Python基础编程练习\n\n请完成以下编程任务...",
            "evaluation_command": "python3",
            "evaluation_script_path": "test.py",
            "test_cases": [
                {
                    "input_data": "1 2",
                    "expected_output": "3",
                    "is_hidden": False,
                    "match_rule": "EXACT_MATCH",
                }
            ],
        },
    },
    {
        "id": "single_choice",
        "name": "单选题模板",
        "description": "标准单选题模板",
        "task_type": "SINGLE_CHOICE",
        "difficulty": "初级",
        "template_content": {
            "handbook_markdown": "# 单选题\n\n请选择正确答案：",
            "question_data": {
                "question_content": "以下哪个是Python的关键字？",
                "question_type": "SINGLE_CHOICE",
                "choices": [
                    {"key": "A", "text": "class", "is_correct": True},
                    {"key": "B", "text": "Class", "is_correct": False},
                    {"key": "C", "text": "CLASS", "is_correct": False},
                    {"key": "D", "text": "clazz", "is_correct": False},
                ],
            },
        },
    },
    {
        "id": "true_false",
        "name": "判断题模板",
        "description": "标准判断题模板",
        "task_type": "TRUE_FALSE",
        "difficulty": "初级",
        "template_content": {
            "handbook_markdown": "# 判断题\n\n请判断以下说法是否正确：",
            "question_data": {
                "question_content": "Python是一种解释型语言。",
                "question_type": "TRUE_FALSE",
                "correct_answer": "true",
            },
        },
    },
]


def get_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
    """Look up a stage template by ID."""
    return next((t for t in STAGE_TEMPLATES if t["id"] == template_id), None)
