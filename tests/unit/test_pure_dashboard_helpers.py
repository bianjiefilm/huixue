"""
dashboard_helpers.py 纯函数单元测试

覆盖: 截止日期紧急度、进度百分比、关注度评分、优先级判定、
      技能分类、推荐评分、相似度计算、实践状态判定
"""
import pytest
from app.utils.dashboard_helpers import (
    deadline_urgency,
    progress_percent,
    attention_score,
    priority_type,
    categorize_skill,
    recommendation_score,
    work_similarity_score,
    determine_practice_status,
    increment_version,
)


# ==================== 截止日期紧急度 ====================

class TestDeadlineUrgency:

    def test_none_returns_zero(self):
        assert deadline_urgency(None) == 0

    def test_overdue(self):
        assert deadline_urgency(0) == 100
        assert deadline_urgency(-5) == 100

    def test_one_day(self):
        assert deadline_urgency(1) == 80

    def test_three_days(self):
        assert deadline_urgency(3) == 80

    def test_four_days(self):
        assert deadline_urgency(4) == 50

    def test_seven_days(self):
        assert deadline_urgency(7) == 50

    def test_eight_days(self):
        assert deadline_urgency(8) == 22  # 30 - 8

    def test_thirty_days(self):
        assert deadline_urgency(30) == 0

    def test_large_value(self):
        assert deadline_urgency(100) == 0


# ==================== 进度百分比 ====================

class TestProgressPercent:

    def test_zero_total(self):
        assert progress_percent(5, 0) == 0

    def test_negative_total(self):
        assert progress_percent(5, -1) == 0

    def test_full_completion(self):
        assert progress_percent(10, 10) == 100

    def test_partial(self):
        assert progress_percent(3, 10) == 30

    def test_over_completion(self):
        """完成数超过总数时 cap 到 100"""
        assert progress_percent(15, 10) == 100

    def test_zero_completed(self):
        assert progress_percent(0, 10) == 0

    def test_rounding_down(self):
        """int() 截断"""
        assert progress_percent(1, 3) == 33  # 33.33... → 33


# ==================== 关注度评分 ====================

class TestAttentionScore:

    def test_all_zero(self):
        assert attention_score(0, 0, False) == 0.0

    def test_mandatory_adds_30(self):
        assert attention_score(0, 0, True) == 30.0

    def test_urgency_weight(self):
        assert attention_score(100, 0, False) == 50.0  # 100 * 0.5

    def test_gap_weight(self):
        assert attention_score(0, 100, False) == 30.0  # 100 * 0.3

    def test_combined(self):
        # 80*0.5 + 70*0.3 + 30 = 40 + 21 + 30 = 91
        assert attention_score(80, 70, True) == pytest.approx(91.0)


# ==================== 优先级类型 ====================

class TestPriorityType:

    def test_deadline_urgent(self):
        assert priority_type(0, 80, 10, True) == "deadline"
        assert priority_type(3, 80, 10, False) == "deadline"

    def test_skill_gap(self):
        assert priority_type(10, 20, 10, False) == "skill_gap"

    def test_skill_gap_zero_tasks(self):
        """total_tasks == 0 时不是 skill_gap"""
        assert priority_type(10, 0, 0, False) == "optional"

    def test_mandatory(self):
        assert priority_type(10, 50, 10, True) == "mandatory"

    def test_optional(self):
        assert priority_type(10, 50, 10, False) == "optional"

    def test_none_days_left(self):
        assert priority_type(None, 20, 5, False) == "skill_gap"

    def test_deadline_trumps_skill_gap(self):
        assert priority_type(2, 10, 10, True) == "deadline"


# ==================== 技能分类 ====================

class TestCategorizeSkill:

    def test_python(self):
        assert categorize_skill("Python") == "编程"

    def test_java(self):
        assert categorize_skill("Java") == "编程"

    def test_sql(self):
        assert categorize_skill("SQL") == "编程"

    def test_data_analysis_cn(self):
        assert categorize_skill("数据分析") == "数据分析"

    def test_pandas(self):
        assert categorize_skill("Pandas") == "数据分析"

    def test_tableau(self):
        assert categorize_skill("Tableau") == "数据分析"

    def test_bi(self):
        assert categorize_skill("BI") == "数据分析"

    def test_machine_learning_cn(self):
        assert categorize_skill("机器学习") == "人工智能"

    def test_deep_learning(self):
        assert categorize_skill("Deep Learning") == "人工智能"

    def test_pytorch(self):
        assert categorize_skill("PyTorch") == "人工智能"

    def test_statistics_cn(self):
        assert categorize_skill("统计学") == "数学统计"

    def test_probability(self):
        """注意: 'Probability' 包含 'bi' 子串，会误匹配到数据分析类别。
        这是原始 student_dashboard._categorize_skill 的已知行为。"""
        assert categorize_skill("Probability Theory") == "数据分析"

    def test_probability_cn(self):
        assert categorize_skill("概率论") == "数学统计"

    def test_math_cn(self):
        assert categorize_skill("数学建模") == "数学统计"

    def test_unknown(self):
        assert categorize_skill("项目管理") == "其他"

    def test_empty(self):
        assert categorize_skill("") == "其他"

    def test_case_insensitive(self):
        assert categorize_skill("PYTHON") == "编程"
        assert categorize_skill("machine learning") == "人工智能"


# ==================== 推荐评分 ====================

class TestRecommendationScore:

    def test_no_interaction(self):
        """无交互 → 仅流行度分"""
        score = recommendation_score(0, 0, None, 5, 5)
        assert score == pytest.approx(0.2)  # popularity = 1.0 * 0.2

    def test_course_preference(self):
        score = recommendation_score(3, 0, None, 0, 0)
        assert score == pytest.approx(1.5)  # 3 * 0.5

    def test_quality_with_likes(self):
        score = recommendation_score(0, 5, 80, 0, 0)
        # quality = 0.8 * 0.3 = 0.24
        assert score == pytest.approx(0.24)

    def test_quality_none_score(self):
        """overall_score 为 None 时用 0.5"""
        score = recommendation_score(0, 1, None, 0, 0)
        assert score == pytest.approx(0.15)  # 0.5 * 0.3

    def test_popularity_cap(self):
        """流行度 capped at 1.0"""
        score = recommendation_score(0, 0, None, 100, 100)
        assert score == pytest.approx(0.2)  # 1.0 * 0.2

    def test_combined(self):
        # pref: 2*0.5=1.0, quality: (90/100)*0.3=0.27, pop: min(15/10,1)*0.2=0.2
        score = recommendation_score(2, 3, 90, 10, 5)
        assert score == pytest.approx(1.47)


# ==================== 相似度计算 ====================

class TestWorkSimilarityScore:

    def test_identical(self):
        assert work_similarity_score(True, True, 0) == pytest.approx(1.0)

    def test_nothing_similar(self):
        assert work_similarity_score(False, False, 20) == pytest.approx(0.0)

    def test_same_course_only(self):
        assert work_similarity_score(True, False, 50) == pytest.approx(0.4)

    def test_same_difficulty_only(self):
        assert work_similarity_score(False, True, 50) == pytest.approx(0.3)

    def test_close_heat_only(self):
        assert work_similarity_score(False, False, 5) == pytest.approx(0.3)

    def test_heat_boundary(self):
        assert work_similarity_score(False, False, 9) == pytest.approx(0.3)
        assert work_similarity_score(False, False, 10) == pytest.approx(0.0)


# ==================== 实践状态判定 ====================

class TestDeterminePracticeStatus:

    def test_editing_never_published(self):
        assert determine_practice_status("EDITING", None, False) == "draft"

    def test_editing_was_published(self):
        assert determine_practice_status("EDITING", None, True) == "editing"

    def test_published_private(self):
        assert determine_practice_status("PUBLISHED", "PRIVATE", True) == "published_personal"

    def test_published_public(self):
        assert determine_practice_status("PUBLISHED", "PUBLIC", True) == "published_public"

    def test_published_no_visibility(self):
        assert determine_practice_status("PUBLISHED", None, True) == "published_public"

    def test_pending_review(self):
        assert determine_practice_status("PENDING_REVIEW", None, False) == "pending"

    def test_rejected(self):
        assert determine_practice_status("REJECTED", None, False) == "rejected"

    def test_unknown_status(self):
        assert determine_practice_status("UNKNOWN", None, False) == "draft"

    def test_empty_status(self):
        assert determine_practice_status("", None, False) == "draft"

    def test_none_status(self):
        assert determine_practice_status(None, None, False) == "draft"

    def test_case_insensitive(self):
        assert determine_practice_status("editing", "private", True) == "editing"
        assert determine_practice_status("published", "private", True) == "published_personal"


# ==================== 版本号递增 ====================

class TestIncrementVersion:

    def test_minor_bump(self):
        assert increment_version("1.0.0", "minor") == "1.1.0"

    def test_major_bump(self):
        assert increment_version("1.2.3", "major") == "2.0.0"

    def test_minor_resets_patch(self):
        assert increment_version("1.2.5", "minor") == "1.3.0"

    def test_major_resets_minor_and_patch(self):
        assert increment_version("3.7.9", "major") == "4.0.0"

    def test_two_part_version(self):
        """只有 major.minor 没有 patch"""
        assert increment_version("2.5", "minor") == "2.6.0"

    def test_zero_version(self):
        assert increment_version("0.0.0", "minor") == "0.1.0"
        assert increment_version("0.0.0", "major") == "1.0.0"

    def test_invalid_version_fallback(self):
        assert increment_version("not-a-version", "minor") == "1.0.0"

    def test_empty_string_fallback(self):
        assert increment_version("", "minor") == "1.0.0"

    def test_default_is_minor(self):
        """version_type 不是 'major' 时按 minor 处理"""
        assert increment_version("1.0.0", "patch") == "1.1.0"
        assert increment_version("1.0.0", "anything") == "1.1.0"
