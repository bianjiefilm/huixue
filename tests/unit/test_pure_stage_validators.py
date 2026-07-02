"""
Unit tests for backend/app/utils/stage_validators.py — stage validation pure functions.
"""
import pytest
from app.utils.stage_validators import (
    validate_stage_fields,
    check_duplicate_skills,
    validate_question_stage_fields,
    STAGE_TEMPLATES,
    get_template_by_id,
)


class TestValidateStageFields:

    def test_valid_minimal(self):
        data = {
            "task_info": {"title": "关卡1", "task_type": "READING"},
            "answer_info": {"answer_title": "参考答案"},
        }
        errors, warnings = validate_stage_fields(data)
        assert errors == []

    def test_title_too_long(self):
        data = {
            "task_info": {"title": "A" * 61},
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("60" in e for e in errors)

    def test_title_exactly_60(self):
        data = {
            "task_info": {"title": "A" * 60},
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert errors == []

    def test_too_many_skills(self):
        data = {
            "task_info": {"title": "X", "skills": ["a", "b", "c", "d", "e", "f"]},
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("5" in e for e in errors)

    def test_practice_type_missing_script(self):
        data = {
            "task_info": {"title": "X", "task_type": "PRACTICE"},
            "task_settings": {"evaluation_command": "python3"},
            "test_cases": [{"input": "1"}],
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("执行文件" in e for e in errors)

    def test_practice_type_missing_command(self):
        data = {
            "task_info": {"title": "X", "task_type": "PRACTICE"},
            "task_settings": {"evaluation_script_path": "test.py"},
            "test_cases": [{"input": "1"}],
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("执行命令" in e for e in errors)

    def test_practice_timeout_out_of_range(self):
        data = {
            "task_info": {"title": "X", "task_type": "PRACTICE"},
            "task_settings": {
                "evaluation_script_path": "t.py",
                "evaluation_command": "python3",
                "evaluation_timeout_seconds": 500,
            },
            "test_cases": [{"input": "1"}],
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("1-300" in e for e in errors)

    def test_practice_no_test_cases(self):
        data = {
            "task_info": {"title": "X", "task_type": "PRACTICE"},
            "task_settings": {
                "evaluation_script_path": "t.py",
                "evaluation_command": "python3",
            },
            "test_cases": [],
            "answer_info": {"answer_title": "ok"},
        }
        errors, _ = validate_stage_fields(data)
        assert any("1-10" in e for e in errors)

    def test_empty_answer_title(self):
        data = {
            "task_info": {"title": "X"},
            "answer_info": {"answer_title": "  "},
        }
        errors, _ = validate_stage_fields(data)
        assert any("答案标题" in e for e in errors)

    def test_missing_answer_info(self):
        data = {"task_info": {"title": "X"}}
        errors, _ = validate_stage_fields(data)
        assert any("答案标题" in e for e in errors)


class TestCheckDuplicateSkills:

    def test_no_duplicates(self):
        assert check_duplicate_skills(["a", "b"], [["c", "d"]]) == []

    def test_has_duplicates(self):
        result = check_duplicate_skills(["a", "b"], [["b", "c"]])
        assert result == ["b"]

    def test_multiple_existing_sets(self):
        result = check_duplicate_skills(["x", "y"], [["x"], ["y", "z"]])
        assert result == ["x", "y"]

    def test_empty_new_skills(self):
        assert check_duplicate_skills([], [["a"]]) == []

    def test_empty_existing(self):
        assert check_duplicate_skills(["a"], []) == []


class TestValidateQuestionStageFields:

    def test_valid_single_choice(self):
        data = {
            "question_data": {
                "question_content": "What is 1+1?",
                "question_type": "SINGLE_CHOICE",
                "choices": [
                    {"key": "A", "text": "2", "is_correct": True},
                    {"key": "B", "text": "3", "is_correct": False},
                ],
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert errors == []

    def test_single_choice_no_correct(self):
        data = {
            "question_data": {
                "question_content": "Q?",
                "question_type": "SINGLE_CHOICE",
                "choices": [
                    {"key": "A", "text": "x", "is_correct": False},
                    {"key": "B", "text": "y", "is_correct": False},
                ],
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("1个正确" in e for e in errors)

    def test_single_choice_two_correct(self):
        data = {
            "question_data": {
                "question_content": "Q?",
                "question_type": "SINGLE_CHOICE",
                "choices": [
                    {"key": "A", "text": "x", "is_correct": True},
                    {"key": "B", "text": "y", "is_correct": True},
                ],
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("1个正确" in e for e in errors)

    def test_multiple_choice_needs_two_correct(self):
        data = {
            "question_data": {
                "question_content": "Q?",
                "question_type": "MULTIPLE_CHOICE",
                "choices": [
                    {"key": "A", "text": "x", "is_correct": True},
                    {"key": "B", "text": "y", "is_correct": False},
                ],
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("2个正确" in e for e in errors)

    def test_too_few_choices(self):
        data = {
            "question_data": {
                "question_content": "Q?",
                "question_type": "SINGLE_CHOICE",
                "choices": [{"key": "A", "text": "x", "is_correct": True}],
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("2个选项" in e for e in errors)

    def test_empty_question_content(self):
        data = {
            "question_data": {
                "question_content": "",
                "question_type": "TRUE_FALSE",
                "correct_answer": "true",
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("题目内容" in e for e in errors)

    def test_true_false_missing_answer(self):
        data = {
            "question_data": {
                "question_content": "Is Python interpreted?",
                "question_type": "TRUE_FALSE",
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert any("正确答案" in e for e in errors)

    def test_true_false_valid(self):
        data = {
            "question_data": {
                "question_content": "Python is interpreted.",
                "question_type": "TRUE_FALSE",
                "correct_answer": "true",
            }
        }
        errors, _ = validate_question_stage_fields(data)
        assert errors == []


class TestStageTemplates:

    def test_templates_exist(self):
        assert len(STAGE_TEMPLATES) >= 3

    def test_each_has_required_keys(self):
        for t in STAGE_TEMPLATES:
            assert "id" in t
            assert "name" in t
            assert "task_type" in t
            assert "template_content" in t

    def test_get_existing(self):
        t = get_template_by_id("python_basic")
        assert t is not None
        assert t["task_type"] == "PRACTICE"

    def test_get_nonexistent(self):
        assert get_template_by_id("nonexistent") is None

    def test_single_choice_template(self):
        t = get_template_by_id("single_choice")
        assert t is not None
        choices = t["template_content"]["question_data"]["choices"]
        assert len(choices) == 4
