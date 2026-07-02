"""
Unit tests for backend/app/utils/diff_helpers.py — v1 diff engine pure functions.
"""
from datetime import datetime
from types import SimpleNamespace
from app.utils.diff_helpers import (
    find_new_keys,
    find_deleted_keys,
    determine_deletion_action,
    compare_metadata_fields,
    compare_file_keys,
    should_mark_version_change,
)


# ==================== find_new_keys / find_deleted_keys ====================
# These are thin wrappers on set subtraction; test only edge semantics.

class TestSetOperations:
    def test_new_keys_partial(self):
        assert find_new_keys({"a", "b", "c"}, {"b"}) == {"a", "c"}

    def test_new_keys_empty(self):
        assert find_new_keys(set(), {"x"}) == set()

    def test_deleted_keys_partial(self):
        assert find_deleted_keys({"b"}, {"a", "b", "c"}) == {"a", "c"}

    def test_deleted_keys_identical(self):
        assert find_deleted_keys({"x", "y"}, {"x", "y"}) == set()


# ==================== determine_deletion_action ====================

class TestDetermineDeleteAction:
    # Word-boundary matches
    def test_test_keyword(self):
        assert determine_deletion_action("Test Course") == "delete"

    def test_demo_keyword(self):
        assert determine_deletion_action("Demo Project") == "delete"

    def test_temp_chinese_keyword(self):
        assert determine_deletion_action("临时资源") == "delete"

    def test_case_insensitive(self):
        assert determine_deletion_action("TEST uppercase") == "delete"

    def test_keyword_in_middle(self):
        assert determine_deletion_action("my test course v2") == "delete"

    # Word-boundary: no false positives
    def test_contest_not_matched(self):
        assert determine_deletion_action("contest results") == "soft_delete"

    def test_testimony_not_matched(self):
        assert determine_deletion_action("testimony report") == "soft_delete"

    def test_demonstration_not_matched(self):
        assert determine_deletion_action("demonstration video") == "soft_delete"

    # Normal titles
    def test_normal_title(self):
        assert determine_deletion_action("Python 入门") == "soft_delete"

    def test_empty_title(self):
        assert determine_deletion_action("") == "soft_delete"

    def test_production_title(self):
        assert determine_deletion_action("数据分析实训课程") == "soft_delete"

    # Delimiter variants
    def test_test_with_underscore(self):
        assert determine_deletion_action("my_test_data") == "delete"

    def test_test_with_hyphen(self):
        assert determine_deletion_action("demo-project") == "delete"

    def test_test_at_start(self):
        assert determine_deletion_action("test") == "delete"

    def test_test_at_end(self):
        assert determine_deletion_action("unit test") == "delete"


# ==================== should_mark_version_change ====================

class TestShouldMarkVersionChange:
    def test_fs_newer(self):
        assert should_mark_version_change(
            datetime(2025, 1, 2), datetime(2025, 1, 1), "aaa", "aaa"
        ) is True

    def test_same_time_same_checksum(self):
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 1), "aaa", "aaa"
        ) is False

    def test_same_time_different_checksum(self):
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 1), "aaa", "bbb"
        ) is True

    def test_db_newer_same_checksum(self):
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 2), "aaa", "aaa"
        ) is False

    def test_db_newer_different_checksum(self):
        # DB is newer but checksums differ → still a change
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 2), "aaa", "bbb"
        ) is True

    def test_none_checksums_equal(self):
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 1), None, None
        ) is False

    def test_one_none_checksum(self):
        assert should_mark_version_change(
            datetime(2025, 1, 1), datetime(2025, 1, 1), None, "aaa"
        ) is True

    def test_fs_much_newer(self):
        assert should_mark_version_change(
            datetime(2025, 6, 1), datetime(2024, 1, 1), "x", "x"
        ) is True


# ==================== compare_metadata_fields ====================

class TestCompareMetadataFields:
    def _make_metadata(self, **kwargs):
        defaults = {
            'title': 'Course', 'intro': 'Intro text', 'industry': 'IT',
            'difficulty': 'beginner', 'course_hours': 10,
            'estimated_completion_time': '2周', 'max_students': 50,
            'is_active': True, 'prerequisites': [],
            'learning_objectives': [], 'tags': [],
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _make_db(self, **kwargs):
        defaults = {
            'title': 'Course', 'intro': 'Intro text', 'industry': 'IT',
            'difficulty': 'beginner', 'course_hours': 10,
            'estimated_completion_time': '2周', 'max_students': 50,
            'is_active': True, 'prerequisites': [],
            'learning_objectives': [], 'tags': [],
        }
        defaults.update(kwargs)
        return defaults

    def test_no_changes(self):
        assert compare_metadata_fields(self._make_metadata(), self._make_db()) == []

    def test_title_change(self):
        changes = compare_metadata_fields(
            self._make_metadata(title='New'), self._make_db(title='Old'))
        assert changes == [('title', 'Old', 'New')]

    def test_multiple_scalar_changes(self):
        changes = compare_metadata_fields(
            self._make_metadata(title='X', course_hours=20),
            self._make_db(title='Y', course_hours=10))
        fields = [c[0] for c in changes]
        assert 'title' in fields and 'course_hours' in fields

    def test_array_field_order_ignored(self):
        assert compare_metadata_fields(
            self._make_metadata(tags=['a', 'b']),
            self._make_db(tags=['b', 'a'])) == []

    def test_array_field_content_differs(self):
        changes = compare_metadata_fields(
            self._make_metadata(tags=['a', 'b', 'c']),
            self._make_db(tags=['a', 'b']))
        assert len(changes) == 1 and changes[0][0] == 'tags'

    def test_training_fields_detected(self):
        changes = compare_metadata_fields(
            self._make_metadata(training_type='coding', require_design_files=True),
            self._make_db(training_type='drag_and_drop', require_design_files=False))
        fields = [c[0] for c in changes]
        assert 'training_type' in fields and 'require_design_files' in fields

    def test_training_assignment_nodes_change(self):
        changes = compare_metadata_fields(
            self._make_metadata(training_type='coding', assignment_nodes=[{'id': 1}]),
            self._make_db(assignment_nodes=[{'id': 2}]))
        assert 'assignment_nodes' in [c[0] for c in changes]

    def test_non_training_skips_training_fields(self):
        changes = compare_metadata_fields(
            self._make_metadata(), self._make_db(training_type='coding'))
        assert 'training_type' not in [c[0] for c in changes]

    def test_bool_change(self):
        changes = compare_metadata_fields(
            self._make_metadata(is_active=False), self._make_db(is_active=True))
        assert ('is_active', True, False) in changes


# ==================== compare_file_keys ====================

class TestCompareFileKeys:
    def test_no_changes(self):
        added, removed = compare_file_keys({'a': {}, 'b': {}}, {'a': {}, 'b': {}})
        assert added == [] and removed == []

    def test_mixed(self):
        added, removed = compare_file_keys({'a': {}, 'c': {}}, {'a': {}, 'b': {}})
        assert added == ['c'] and removed == ['b']

    def test_both_empty(self):
        added, removed = compare_file_keys({}, {})
        assert added == [] and removed == []
