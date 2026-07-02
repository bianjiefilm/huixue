"""
Unit tests for backend/app/utils/sync_diff_helpers.py — sync diff pure functions.
"""
import pytest
from datetime import datetime
from app.utils.sync_diff_helpers import (
    infer_resource_type,
    is_version_newer,
    check_file_changes,
    validate_sync_plan_actions,
)


# ==================== infer_resource_type ====================

class TestInferResourceType:

    def test_training_with_type(self):
        assert infer_resource_type({"training_type": "coding"}) == "training"

    def test_training_drag_drop(self):
        assert infer_resource_type({"training_type": "drag_and_drop"}) == "training"

    def test_practice_no_type(self):
        assert infer_resource_type({"title": "test"}) == "practice"

    def test_practice_empty_type(self):
        assert infer_resource_type({"training_type": ""}) == "practice"

    def test_practice_none_type(self):
        assert infer_resource_type({"training_type": None}) == "practice"

    def test_empty_record(self):
        assert infer_resource_type({}) == "practice"


# ==================== is_version_newer ====================

class TestIsVersionNewer:

    def test_newer_major(self):
        assert is_version_newer("2.0.0", "1.0.0") is True

    def test_newer_minor(self):
        assert is_version_newer("1.2.0", "1.1.0") is True

    def test_newer_patch(self):
        assert is_version_newer("1.0.2", "1.0.1") is True

    def test_same_version(self):
        assert is_version_newer("1.0.0", "1.0.0") is False

    def test_older_version(self):
        assert is_version_newer("1.0.0", "2.0.0") is False

    def test_different_length(self):
        assert is_version_newer("1.0.0.1", "1.0.0") is True

    def test_different_length_equal(self):
        assert is_version_newer("1.0", "1.0.0") is False

    def test_invalid_format_different(self):
        # Falls back to string comparison
        assert is_version_newer("abc", "def") is True  # "abc" != "def"

    def test_invalid_format_same(self):
        assert is_version_newer("abc", "abc") is False

    def test_zero_vs_initial(self):
        assert is_version_newer("1.0.0", "0.0.0") is True

    def test_db_default(self):
        # Common case: db has no version, defaults to 0.0.0
        assert is_version_newer("1.0.0", "0.0.0") is True


# ==================== check_file_changes ====================

class TestCheckFileChanges:

    def test_no_changes(self):
        fs = {"a.py": {"exists": True, "size": 100}}
        db = {"a.py": {"exists": True, "size": 100}}
        assert check_file_changes(fs, db) == []

    def test_new_file(self):
        fs = {"a.py": {"exists": True}, "b.py": {"exists": True}}
        db = {"a.py": {"exists": True}}
        changes = check_file_changes(fs, db)
        assert any("新增" in c and "b.py" in c for c in changes)

    def test_deleted_file(self):
        fs = {"a.py": {"exists": True}}
        db = {"a.py": {"exists": True}, "old.py": {"exists": True}}
        changes = check_file_changes(fs, db)
        assert any("删除" in c and "old.py" in c for c in changes)

    def test_size_change(self):
        fs = {"a.py": {"exists": True, "size": 200}}
        db = {"a.py": {"exists": True, "size": 100}}
        changes = check_file_changes(fs, db)
        assert any("大小变化" in c for c in changes)

    def test_mtime_newer(self):
        t1 = datetime(2024, 1, 1)
        t2 = datetime(2024, 6, 1)
        fs = {"a.py": {"exists": True, "size": 100, "modified": t2}}
        db = {"a.py": {"exists": True, "size": 100, "modified": t1}}
        changes = check_file_changes(fs, db)
        assert any("修改时间" in c for c in changes)

    def test_mtime_older_no_change(self):
        t1 = datetime(2024, 6, 1)
        t2 = datetime(2024, 1, 1)
        fs = {"a.py": {"exists": True, "size": 100, "modified": t2}}
        db = {"a.py": {"exists": True, "size": 100, "modified": t1}}
        assert check_file_changes(fs, db) == []

    def test_fs_file_not_exists(self):
        fs = {"a.py": {"exists": False}}
        db = {"a.py": {"exists": True, "size": 100}}
        changes = check_file_changes(fs, db)
        assert any("文件不存在" in c for c in changes)

    def test_db_file_not_exists(self):
        fs = {"a.py": {"exists": True, "size": 100}}
        db = {"a.py": {"exists": False}}
        changes = check_file_changes(fs, db)
        assert any("数据库中文件不存在" in c for c in changes)

    def test_both_empty(self):
        assert check_file_changes({}, {}) == []

    def test_multiple_changes(self):
        fs = {
            "new.py": {"exists": True, "size": 50},
            "changed.py": {"exists": True, "size": 200},
        }
        db = {
            "deleted.py": {"exists": True, "size": 30},
            "changed.py": {"exists": True, "size": 100},
        }
        changes = check_file_changes(fs, db)
        assert len(changes) == 3  # new + deleted + size change


# ==================== validate_sync_plan_actions ====================

class TestValidateSyncPlanActions:

    def test_valid_plan(self):
        actions = [
            {"action_type": "create", "resource_id": "r1"},
            {"action_type": "update", "resource_id": "r2"},
        ]
        assert validate_sync_plan_actions(actions) == []

    def test_too_many_actions(self):
        actions = [{"action_type": "create", "resource_id": f"r{i}"} for i in range(1001)]
        errors = validate_sync_plan_actions(actions)
        assert any("过多" in e for e in errors)

    def test_custom_max(self):
        actions = [{"action_type": "create", "resource_id": f"r{i}"} for i in range(5)]
        errors = validate_sync_plan_actions(actions, max_actions=3)
        assert any("过多" in e for e in errors)

    def test_duplicate_resource_id(self):
        actions = [
            {"action_type": "create", "resource_id": "r1"},
            {"action_type": "update", "resource_id": "r1"},
        ]
        errors = validate_sync_plan_actions(actions)
        assert any("冲突" in e and "r1" in e for e in errors)

    def test_same_action_type_no_conflict(self):
        # Two creates for same resource is still a conflict (2 actions)
        actions = [
            {"action_type": "create", "resource_id": "r1"},
            {"action_type": "create", "resource_id": "r1"},
        ]
        errors = validate_sync_plan_actions(actions)
        assert any("冲突" in e for e in errors)

    def test_empty_plan(self):
        assert validate_sync_plan_actions([]) == []

    def test_single_action(self):
        actions = [{"action_type": "delete", "resource_id": "r1"}]
        assert validate_sync_plan_actions(actions) == []
