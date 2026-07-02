"""
training_database_mapper.py 纯函数单元测试

覆盖: map_training_type, map_difficulty_level
"""
import pytest
from app.utils.training_database_mapper import map_training_type, map_difficulty_level
from app.models.models import TrainingTypeEnum, DifficultyLevelEnum


class TestMapTrainingType:

    def test_drag_drop(self):
        assert map_training_type("拖拽式") == TrainingTypeEnum.DRAG_DROP

    def test_coding(self):
        assert map_training_type("编码式") == TrainingTypeEnum.CODING

    def test_unknown_defaults_drag_drop(self):
        assert map_training_type("未知类型") == TrainingTypeEnum.DRAG_DROP

    def test_empty_string(self):
        assert map_training_type("") == TrainingTypeEnum.DRAG_DROP

    def test_none_like(self):
        """None 不是合法输入，但 dict.get 返回默认值"""
        assert map_training_type("None") == TrainingTypeEnum.DRAG_DROP

    def test_english_fallback(self):
        assert map_training_type("drag_and_drop") == TrainingTypeEnum.DRAG_DROP

    def test_exact_match_only(self):
        """不做模糊匹配"""
        assert map_training_type("拖拽") == TrainingTypeEnum.DRAG_DROP  # default
        assert map_training_type("编码") == TrainingTypeEnum.DRAG_DROP  # default


class TestMapDifficultyLevel:

    def test_beginner(self):
        assert map_difficulty_level("初级") == DifficultyLevelEnum.beginner

    def test_intermediate(self):
        assert map_difficulty_level("中级") == DifficultyLevelEnum.intermediate

    def test_advanced(self):
        assert map_difficulty_level("高级") == DifficultyLevelEnum.advanced

    def test_unknown_defaults_intermediate(self):
        assert map_difficulty_level("专家级") == DifficultyLevelEnum.intermediate

    def test_empty_string(self):
        assert map_difficulty_level("") == DifficultyLevelEnum.intermediate

    def test_english_fallback(self):
        assert map_difficulty_level("beginner") == DifficultyLevelEnum.intermediate  # not in map

    def test_all_three_distinct(self):
        """三个级别互不相同"""
        results = {
            map_difficulty_level("初级"),
            map_difficulty_level("中级"),
            map_difficulty_level("高级"),
        }
        assert len(results) == 3
