"""
resource_sync_v3/models.py 纯函数单元测试

覆盖: SyncPlan.get_summary_text, ResourceMetadata.calculate_checksum,
       ResourceMetadata.get_resource_paths
"""
import pytest
from app.services.resource_sync_v3.models import (
    SyncPlan, SyncAction, SyncActionType, ResourceType,
    ResourceMetadata, EnvironmentConfig, EnvironmentType,
    ContentManifest, ContentResource, Difficulty,
)


# ==================== SyncPlan.get_summary_text ====================

class TestSyncPlanGetSummaryText:

    def test_empty_plan(self):
        plan = SyncPlan()
        assert plan.get_summary_text() == ""

    def test_single_action_type(self):
        plan = SyncPlan()
        plan.add_action(SyncAction(
            action_type=SyncActionType.CREATE,
            resource_id="test-1",
            resource_type=ResourceType.TRAINING,
        ))
        text = plan.get_summary_text()
        assert "create" in text
        assert "1" in text

    def test_multiple_action_types(self):
        plan = SyncPlan()
        plan.add_action(SyncAction(
            action_type=SyncActionType.CREATE,
            resource_id="t1",
            resource_type=ResourceType.TRAINING,
        ))
        plan.add_action(SyncAction(
            action_type=SyncActionType.CREATE,
            resource_id="t2",
            resource_type=ResourceType.TRAINING,
        ))
        plan.add_action(SyncAction(
            action_type=SyncActionType.DELETE,
            resource_id="t3",
            resource_type=ResourceType.PRACTICE,
        ))
        text = plan.get_summary_text()
        assert "create: 2" in text
        assert "delete: 1" in text

    def test_summary_dict_updated(self):
        plan = SyncPlan()
        plan.add_action(SyncAction(
            action_type=SyncActionType.UPDATE,
            resource_id="u1",
            resource_type=ResourceType.TRAINING,
        ))
        assert plan.summary == {"update": 1}


# ==================== ResourceMetadata.calculate_checksum ====================

def _make_metadata(**overrides):
    """构造最小合法 ResourceMetadata"""
    defaults = dict(
        id="test-resource-1",
        version="1.0.0",
        title="测试资源",
        resource_type=ResourceType.TRAINING,
        training_type="drag_and_drop",
        intro="简介内容",
        industry="教育",
        difficulty=Difficulty.BEGINNER,
        course_hours=4,
        handbook_content_path="handbook.md",
        environment_config={"env_type": "TEMPO_BI", "docker_image_name": "tempo-bi:latest"},
    )
    defaults.update(overrides)
    return ResourceMetadata(**defaults)


class TestCalculateChecksum:

    def test_deterministic(self):
        m = _make_metadata()
        assert m.calculate_checksum() == m.calculate_checksum()

    def test_different_title_different_checksum(self):
        m1 = _make_metadata(title="A")
        m2 = _make_metadata(title="B")
        assert m1.calculate_checksum() != m2.calculate_checksum()

    def test_ignores_timestamps(self):
        """created_at/updated_at 被排除，不影响 checksum"""
        from datetime import datetime
        m1 = _make_metadata()
        m2 = _make_metadata(created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 6, 1))
        assert m1.calculate_checksum() == m2.calculate_checksum()

    def test_returns_md5_hex(self):
        checksum = _make_metadata().calculate_checksum()
        assert len(checksum) == 32
        assert all(c in "0123456789abcdef" for c in checksum)


# ==================== ResourceMetadata.get_resource_paths ====================

class TestGetResourcePaths:

    def test_basic_paths(self):
        m = _make_metadata(
            handbook_content_path="docs/handbook.md",
            cover_url_path="images/cover.png",
        )
        paths = m.get_resource_paths()
        assert "docs/handbook.md" in paths
        assert "images/cover.png" in paths

    def test_no_cover(self):
        m = _make_metadata(cover_url_path=None)
        paths = m.get_resource_paths()
        assert "handbook.md" in paths
        assert len([p for p in paths if p]) >= 1

    def test_with_content_resources(self):
        m = _make_metadata(
            content_resources=ContentManifest(
                datasets=[
                    ContentResource(name="data.csv", path="data/data.csv"),
                ],
                sql_scripts=[
                    ContentResource(name="init.sql", path="sql/init.sql"),
                ],
                bi_templates=[],
                ai_models=[],
            )
        )
        paths = m.get_resource_paths()
        assert "data/data.csv" in paths
        assert "sql/init.sql" in paths

    def test_empty_content_resources(self):
        m = _make_metadata()
        paths = m.get_resource_paths()
        # 至少包含 handbook
        assert len(paths) >= 1
