"""
consistency_helpers.py 纯函数单元测试

覆盖: 健康评分计算
"""
import pytest
from app.utils.consistency_helpers import calculate_health_score


class TestCalculateHealthScore:

    def test_perfect_score(self):
        """无不一致、无错误 → 100"""
        results = {
            "cache_check": {
                "total_checked": 10,
                "inconsistencies": [],
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 100

    def test_no_items_checked(self):
        """无检查项 → 100"""
        results = {"cache_check": {"total_checked": 0}}
        assert calculate_health_score(results) == 100

    def test_empty_results(self):
        """空结果 → 100 (total_checked defaults to 0)"""
        assert calculate_health_score({}) == 100

    def test_half_inconsistent(self):
        """50% 不一致 → 50"""
        results = {
            "cache_check": {
                "total_checked": 10,
                "inconsistencies": [{}] * 5,
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 50

    def test_all_inconsistent(self):
        """100% 不一致 → 0"""
        results = {
            "cache_check": {
                "total_checked": 5,
                "inconsistencies": [{}] * 5,
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 0

    def test_error_penalty(self):
        """每个错误扣 10 分"""
        results = {
            "cache_check": {
                "total_checked": 10,
                "inconsistencies": [],
                "errors": [{}] * 2,
            }
        }
        assert calculate_health_score(results) == 80

    def test_combined(self):
        """不一致 + 错误同时存在"""
        results = {
            "cache_check": {
                "total_checked": 20,
                "inconsistencies": [{}] * 4,  # 20% → score 80
                "errors": [{}] * 1,            # penalty 10
            }
        }
        assert calculate_health_score(results) == 70

    def test_floor_at_zero(self):
        """评分不低于 0"""
        results = {
            "cache_check": {
                "total_checked": 1,
                "inconsistencies": [{}] * 1,
                "errors": [{}] * 20,
            }
        }
        assert calculate_health_score(results) == 0

    def test_single_item_consistent(self):
        results = {
            "cache_check": {
                "total_checked": 1,
                "inconsistencies": [],
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 100

    def test_single_item_inconsistent(self):
        results = {
            "cache_check": {
                "total_checked": 1,
                "inconsistencies": [{}],
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 0

    def test_missing_cache_check(self):
        """cache_check 字段缺失 → 100"""
        assert calculate_health_score({"other": {}}) == 100

    def test_returns_int(self):
        """始终返回 int"""
        results = {
            "cache_check": {
                "total_checked": 3,
                "inconsistencies": [{}],
                "errors": [],
            }
        }
        score = calculate_health_score(results)
        assert isinstance(score, int)

    def test_large_dataset(self):
        results = {
            "cache_check": {
                "total_checked": 1000,
                "inconsistencies": [{}] * 10,  # 1% → 99
                "errors": [],
            }
        }
        assert calculate_health_score(results) == 99
