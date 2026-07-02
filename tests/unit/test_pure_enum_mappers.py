"""
Unit tests for backend/app/utils/enum_mappers.py — enum mapping pure functions.
"""
from app.utils.enum_mappers import map_difficulty, map_task_type, map_question_type


class TestMapDifficulty:
    def test_beginner(self):
        assert map_difficulty("初级") == "beginner"

    def test_intermediate(self):
        assert map_difficulty("中级") == "intermediate"

    def test_advanced(self):
        assert map_difficulty("高级") == "advanced"

    def test_expert_maps_to_advanced(self):
        assert map_difficulty("专家") == "advanced"

    def test_unknown_defaults_intermediate(self):
        assert map_difficulty("未知") == "intermediate"

    def test_empty_defaults_intermediate(self):
        assert map_difficulty("") == "intermediate"


class TestMapTaskType:
    def test_practice(self):
        assert map_task_type("实践题") == "PRACTICE"

    def test_coding(self):
        assert map_task_type("编程题") == "PRACTICE"

    def test_choice(self):
        assert map_task_type("选择题") == "CHOICE"

    def test_single_choice(self):
        assert map_task_type("单选题") == "CHOICE"

    def test_multiple_choice(self):
        assert map_task_type("多选题") == "CHOICE"

    def test_judge(self):
        assert map_task_type("判断题") == "JUDGE"

    def test_unknown_defaults_practice(self):
        assert map_task_type("其他") == "PRACTICE"


class TestMapQuestionType:
    def test_single(self):
        assert map_question_type("单选题") == "SINGLE_CHOICE"

    def test_multiple(self):
        assert map_question_type("多选题") == "MULTIPLE_CHOICE"

    def test_true_false(self):
        assert map_question_type("判断题") == "TRUE_FALSE"

    def test_choice_maps_single(self):
        assert map_question_type("选择题") == "SINGLE_CHOICE"

    def test_fill_blank(self):
        assert map_question_type("填空题") == "FILL_BLANK"

    def test_short_answer(self):
        assert map_question_type("简答题") == "SHORT_ANSWER"

    def test_unknown_defaults_single_choice(self):
        assert map_question_type("论述题") == "SINGLE_CHOICE"
