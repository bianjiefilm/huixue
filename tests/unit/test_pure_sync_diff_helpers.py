"""
sync_diff_helpers.py 纯函数单元测试

覆盖: infer_resource_type, is_version_newer, check_file_changes, validate_sync_plan_actions
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
        assert infer_resource_type({"training_type": "drag_and_drop"}) == "training"

    def test_practice_without_type(self):
        assert infer_resource_type({"title": "test"}) == "practice"

    def test_empty_training_type(self):
        assert infer_resource_type({"training_type": ""}) == "practice"

    def test_none_training_type(self):
        assert infer_resource_type({"training_type": None}) == "practice"

    def test_empty_dict(self):
        assert infer_resource_type({}) == "practice"


# ==================== is_version_newer ====================

class TestIsVersionNewer:

    def test_newer_major(self):
        assert is_version_newer("2.0.0", "1.0.0") is True

    def test_newer_minor(self):
        assert is_version_newer("1.2.0", "1.1.0") is True

    def test_newer_patch(self):
        assert is_version_newer("1.0.2", "1.0.1") is True

    def test_equal(self):
        assert is_version_newer("1.0.0", "1.0.0") is False

    def test_older(self):
        assert is_version_newer("1.0.0", "2.0.0") is False

    def test_different_lengths(self):
        assert is_version_newer("1.1", "1.0.0") is True

    def test_padding(self):
        assert is_version_newer("1.0", "1.0.0") is False

    def test_invalid_falls_back(self):
        assert is_version_newer("abc", "abc") is False
        assert is_version_newer("abc", "def") is True  # string != comparison


# ==================== check_file_changes ====================

class TestCheckFileChanges:

    def test_no_changes(self):
        fs = {"a.txt": {"exists": True, "size": 100}}
        db = {"a.txt": {"exists": True, "size": 100}}
        assert check_file_changes(fs, db) == []

    def test_new_file(self):
        fs = {"a.txt": {"exists": True}, "b.txt": {"exists": True}}
        db = {"a.txt": {"exists": True}}
        changes = check_file_changes(fs, db)
        assert any("新增" in c and "b.txt" in c for c in changes)

    def test_deleted_file(self):
        fs = {"a.txt": {"exists": True}}
        db = {"a.txt": {"exists": True}, "b.txt": {"exists": True}}
        changes = check_file_changes(fs, db)
        assert any("删除" in c and "b.txt" in c for c in changes)

    def test_size_change(self):
        fs = {"a.txt": {"exists": True, "size": 200}}
        db = {"a.txt": {"exists": True, "size": 100}}
        changes = check_file_changes(fs, db)
        assert any("大小变化" in c for c in changes)

    def test_mtime_change(self):
        t1 = datetime(2024, 1, 1)
        t2 = datetime(2024, 6, 1)
        fs = {"a.txt": {"exists": True, "size": 100, "modified": t2}}
        db = {"a.txt": {"exists": True, "size": 100, "modified": t1}}
        changes = check_file_changes(fs, db)
        assert any("修改时间" in c for c in changes)

    def test_empty_both(self):
        assert check_file_changes({}, {}) == []

    def test_fs_file_not_exists(self):
        fs = {"a.txt": {"exists": False}}
        db = {"a.txt": {"exists": True}}
        changes = check_file_changes(fs, db)
        assert any("文件不存在" in c for c in changes)


# ==================== validate_sync_plan_actions ====================

class TestValidateSyncPlanActions:

    def test_empty_actions(self):
        assert validate_sync_plan_actions([]) == []

    def test_valid_actions(self):
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

    def test_conflicting_actions(self):
        actions = [
            {"action_type": "create", "resource_id": "r1"},
            {"action_type": "delete", "resource_id": "r1"},
        ]
        errors = validate_sync_plan_actions(actions)
        assert any("冲突" in e for e in errors)

    def test_duplicate_same_type_no_conflict(self):
        """Same resource_id + same action_type counts as duplicate but still flagged"""
        actions = [
            {"action_type": "create", "resource_id": "r1"},
            {"action_type": "create", "resource_id": "r1"},
        ]
        errors = validate_sync_plan_actions(actions)
        assert any("冲突" in e for e in errors)
