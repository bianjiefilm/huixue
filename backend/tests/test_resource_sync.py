"""
资源同步服务的完整测试套件
测试各个组件的功能和集成效果
"""
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

from app.services.resource_sync.models import (
    PracticeMetadata, TrainingMetadata, ResourceManifest,
    SyncPlan, SyncAction, SyncResult, ResourceType
)
from app.services.resource_sync.discovery import ResourceDiscoveryService, MetadataParser
from app.services.resource_sync.diff_engine import IntelligentDiffEngine, ConflictResolver
from app.services.resource_sync.executor import TransactionalExecutor
from app.services.resource_sync.monitoring import MetricsCollector, AuditLogger
from app.services.resource_sync.service import ResourceSyncService


@pytest.fixture
def temp_ziyuan_dir():
    """创建临时ziyuan目录用于测试"""
    temp_dir = Path(tempfile.mkdtemp())

    # 创建测试资源结构
    ziyuan_dir = temp_dir / "ziyuan"
    ziyuan_dir.mkdir()

    # 创建课程资源
    practice_dir = ziyuan_dir / "课程资源" / "test-practice"
    practice_dir.mkdir(parents=True)

    practice_metadata = {
        "schema_version": "1.0.0",
        "id": "test-practice-course",
        "title": "测试实践课程",
        "intro": "这是一个测试实践课程",
        "industry": "计算机科学",
        "difficulty": "intermediate",
        "course_hours": 40,
        "estimated_completion_time": "10周",
        "prerequisites": ["基础知识"],
        "learning_objectives": ["掌握基本概念"],
        "tags": ["测试", "实践"],
        "handbook_content_path": "handbook.md",
        "cover_url_path": "cover.png",
        "max_students": 50,
        "is_active": True
    }

    # 写入metadata.json
    with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(practice_metadata, f, ensure_ascii=False, indent=2)

    # 创建手册文件
    with open(practice_dir / "handbook.md", 'w', encoding='utf-8') as f:
        f.write("# 测试实践课程手册\n\n这是手册内容。")

    # 创建封面文件
    with open(practice_dir / "cover.png", 'w', encoding='utf-8') as f:
        f.write("fake png content")

    # 创建实训资源
    training_dir = ziyuan_dir / "实训资源" / "test-training"
    training_dir.mkdir(parents=True)

    training_metadata = {
        "schema_version": "1.0.0",
        "id": "test-training-project",
        "title": "测试实训项目",
        "training_type": "drag_and_drop",
        "intro": "这是一个测试实训项目",
        "industry": "金融科技",
        "difficulty": "advanced",
        "course_hours": 60,
        "estimated_completion_time": "15周",
        "prerequisites": ["专业基础"],
        "learning_objectives": ["掌握高级技能"],
        "tags": ["测试", "实训"],
        "handbook_content_path": "handbook.md",
        "cover_url_path": "cover.png",
        "assignment_nodes": [
            {
                "node_name": "数据分析任务",
                "tool_type": "BI",
                "description": "完成数据分析任务",
                "estimated_time": "8小时"
            }
        ],
        "require_design_files": True,
        "require_experiment_report": True,
        "max_students": 25,
        "is_active": True
    }

    # 写入metadata.json
    with open(training_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(training_metadata, f, ensure_ascii=False, indent=2)

    # 创建手册文件
    with open(training_dir / "handbook.md", 'w', encoding='utf-8') as f:
        f.write("# 测试实训项目手册\n\n这是实训手册内容。")

    yield ziyuan_dir

    # 清理临时目录
    shutil.rmtree(temp_dir)


class TestMetadataModels:
    """测试元数据模型"""

    def test_practice_metadata_creation(self):
        """测试实践元数据创建"""
        data = {
            "schema_version": "1.0.0",
            "id": "test-practice",
            "title": "测试实践课程",
            "intro": "测试简介",
            "industry": "计算机科学",
            "difficulty": "intermediate",
            "course_hours": 40,
            "estimated_completion_time": "10周",
            "prerequisites": ["基础知识"],
            "learning_objectives": ["掌握概念"],
            "tags": ["测试"],
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png",
            "max_students": 50,
            "is_active": True
        }

        metadata = PracticeMetadata(**data)

        assert metadata.id == "test-practice"
        assert metadata.title == "测试实践课程"
        assert metadata.resource_type == ResourceType.PRACTICE
        assert metadata.difficulty == "intermediate"
        assert metadata.course_hours == 40

    def test_training_metadata_creation(self):
        """测试实训元数据创建"""
        data = {
            "schema_version": "1.0.0",
            "id": "test-training",
            "title": "测试实训项目",
            "training_type": "drag_and_drop",
            "intro": "测试简介",
            "industry": "金融科技",
            "difficulty": "advanced",
            "course_hours": 60,
            "estimated_completion_time": "15周",
            "prerequisites": ["专业基础"],
            "learning_objectives": ["掌握技能"],
            "tags": ["测试"],
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png",
            "assignment_nodes": [
                {
                    "node_name": "任务1",
                    "tool_type": "BI",
                    "description": "任务描述",
                    "estimated_time": "8小时"
                }
            ],
            "require_design_files": True,
            "require_experiment_report": True,
            "max_students": 25,
            "is_active": True
        }

        metadata = TrainingMetadata(**data)

        assert metadata.id == "test-training"
        assert metadata.title == "测试实训项目"
        assert metadata.resource_type == ResourceType.TRAINING
        assert metadata.training_type == "drag_and_drop"
        assert len(metadata.assignment_nodes) == 1

    def test_metadata_validation(self, temp_ziyuan_dir):
        """测试元数据验证"""
        practice_dir = temp_ziyuan_dir / "课程资源" / "test-practice"

        # 测试有效元数据
        metadata = PracticeMetadata.parse_file(practice_dir / "metadata.json")
        missing_files = metadata.validate_file_dependencies(str(practice_dir))
        assert len(missing_files) == 0  # 所有必需文件都存在

        # 测试缺少文件的情况
        metadata.handbook_content_path = "missing.md"
        missing_files = metadata.validate_file_dependencies(str(practice_dir))
        assert "missing.md" in missing_files

    def test_checksum_calculation(self):
        """测试校验和计算"""
        metadata = PracticeMetadata(
            id="test",
            title="测试",
            intro="简介",
            industry="行业",
            difficulty="intermediate",
            course_hours=40,
            handbook_content_path="handbook.md",
            cover_url_path="cover.png"
        )

        checksum1 = metadata.calculate_checksum()
        assert checksum1 is not None
        assert len(checksum1) > 0

        # 修改内容后校验和应该改变
        metadata.title = "修改后的标题"
        checksum2 = metadata.calculate_checksum()
        assert checksum1 != checksum2


class TestResourceDiscovery:
    """测试资源发现功能"""

    @pytest.mark.asyncio
    async def test_discovery_service(self, temp_ziyuan_dir):
        """测试资源发现服务"""
        discovery = ResourceDiscoveryService(str(temp_ziyuan_dir))

        resources = await discovery.discover_resources()

        assert len(resources) == 2

        # 检查实践资源
        practice_id = "test-practice-course"
        assert practice_id in resources
        practice_manifest = resources[practice_id]

        assert practice_manifest.metadata.id == practice_id
        assert practice_manifest.metadata.title == "测试实践课程"
        assert practice_manifest.metadata.resource_type == ResourceType.PRACTICE

        # 检查实训资源
        training_id = "test-training-project"
        assert training_id in resources
        training_manifest = resources[training_id]

        assert training_manifest.metadata.id == training_id
        assert training_manifest.metadata.title == "测试实训项目"
        assert training_manifest.metadata.resource_type == ResourceType.TRAINING

    def test_metadata_parser(self):
        """测试元数据解析器"""
        parser = MetadataParser()

        # 测试实践元数据解析
        practice_data = {
            "id": "practice-1",
            "title": "实践课程",
            "intro": "简介",
            "industry": "计算机",
            "difficulty": "intermediate",
            "course_hours": 40,
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png"
        }

        practice_metadata = parser.parse_practice_metadata(practice_data)
        assert practice_metadata.id == "practice-1"
        assert practice_metadata.resource_type == ResourceType.PRACTICE

        # 测试实训元数据解析
        training_data = {
            "id": "training-1",
            "title": "实训项目",
            "training_type": "drag_and_drop",
            "intro": "简介",
            "industry": "金融",
            "difficulty": "advanced",
            "course_hours": 60,
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png"
        }

        training_metadata = parser.parse_training_metadata(training_data)
        assert training_metadata.id == "training-1"
        assert training_metadata.resource_type == ResourceType.TRAINING
        assert training_metadata.training_type == "drag_and_drop"


class TestDiffEngine:
    """测试差异引擎"""

    def test_diff_calculation(self, temp_ziyuan_dir):
        """测试差异计算"""
        # 创建模拟的数据库状态
        db_state = {}

        # 创建文件系统状态
        fs_state = {
            "test-practice-course": Mock(
                metadata=Mock(
                    id="test-practice-course",
                    title="测试实践课程",
                    resource_type=ResourceType.PRACTICE,
                    last_modified=Mock()
                )
            ),
            "test-training-project": Mock(
                metadata=Mock(
                    id="test-training-project",
                    title="测试实训项目",
                    resource_type=ResourceType.TRAINING,
                    last_modified=Mock()
                )
            )
        }

        diff_engine = IntelligentDiffEngine()
        plan = diff_engine.compute_diff(fs_state, db_state)

        assert len(plan.actions) == 2

        # 检查创建操作
        create_actions = [a for a in plan.actions if a.action_type == 'create']
        assert len(create_actions) == 2

        action_ids = {a.resource_id for a in create_actions}
        assert action_ids == {"test-practice-course", "test-training-project"}

    def test_conflict_resolution(self):
        """测试冲突解决"""
        plan = SyncPlan()
        plan.add_action(SyncAction(
            action_type='update',
            resource_id='test-resource',
            resource_type=ResourceType.PRACTICE
        ))

        resolver = ConflictResolver()

        # 测试最新胜出策略
        resolved_plan = resolver.resolve_conflicts(plan, 'latest_wins')
        assert len(resolved_plan.actions) == 1

        # 测试保守策略
        conservative_plan = resolver.resolve_conflicts(plan, 'conservative')
        create_actions = [a for a in conservative_plan.actions if a.action_type == 'create']
        assert len(create_actions) == 0  # 保守策略不处理更新


class TestTransactionalExecutor:
    """测试事务性执行器"""

    @pytest.mark.asyncio
    async def test_executor_simulation(self):
        """测试执行器模拟功能"""
        executor = TransactionalExecutor()

        # 创建测试计划
        plan = SyncPlan()
        plan.add_action(SyncAction(
            action_type='create',
            resource_id='test-resource',
            resource_type=ResourceType.PRACTICE,
            reason='测试创建'
        ))

        result = await executor.execute_plan(plan)

        assert result.success == True
        assert result.total_actions == 1
        assert result.successful_actions == 1
        assert result.failed_actions == 0

    def test_error_handling(self):
        """测试错误处理"""
        # 这个测试可以扩展为测试各种错误情况
        pass


class TestMonitoring:
    """测试监控功能"""

    def test_metrics_collection(self):
        """测试指标收集"""
        metrics = MetricsCollector()

        # 记录一些操作
        metrics.record_operation('discover', 'resource', 1.5, True)
        metrics.record_operation('sync', 'resource', 2.0, True)
        metrics.record_operation('validate', 'resource', 0.5, False)

        # 检查指标
        discover_stats = metrics.get_operation_stats('discover', 'resource')
        assert discover_stats['count'] == 1
        assert discover_stats['success_count'] == 1
        assert discover_stats['avg_duration'] == 1.5

        health = metrics.get_health_status()
        assert health.success_rate == 2/3  # 2成功，1失败
        assert health.total_operations == 3

    def test_audit_logging(self, tmp_path):
        """测试审计日志"""
        log_path = tmp_path / "audit.log"
        audit_logger = AuditLogger(str(log_path))

        # 记录操作
        audit_logger.log_sync_operation('create', 'test-resource', 'system', {'details': 'test'})

        # 检查日志文件是否创建
        assert log_path.exists()

        # 检查日志内容
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'SYNC_OPERATION' in content
            assert 'test-resource' in content


class TestResourceSyncService:
    """测试资源同步服务集成"""

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, temp_ziyuan_dir):
        """测试完整的同步工作流程"""
        service = ResourceSyncService(ziyuan_base_path=str(temp_ziyuan_dir))

        # 1. 验证资源
        validation_result = await service.validate_resources()
        assert validation_result['total_resources'] == 2
        assert validation_result['valid_resources'] == 2

        # 2. 执行干运行同步
        sync_result = await service.sync_all_resources(dry_run=True)
        assert sync_result.success == True
        assert sync_result.total_actions == 2  # 应该创建2个资源

        # 3. 检查健康状态
        health_status = service.get_health_status()
        assert 'overall_health' in health_status.dict()

        # 4. 获取监控报告
        monitoring_report = service.get_monitoring_report()
        assert 'health_status' in monitoring_report
        assert 'recent_alerts' in monitoring_report
        assert 'metrics_summary' in monitoring_report

    @pytest.mark.asyncio
    async def test_single_resource_sync(self, temp_ziyuan_dir):
        """测试单个资源同步"""
        service = ResourceSyncService(ziyuan_base_path=str(temp_ziyuan_dir))

        # 同步单个实践资源
        result = await service.sync_single_resource('test-practice-course', dry_run=True)
        assert result.success == True

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_ziyuan_dir):
        """测试错误处理"""
        service = ResourceSyncService(ziyuan_base_path=str(temp_ziyuan_dir))

        # 测试同步不存在的资源
        with pytest.raises(ValueError, match="资源不存在"):
            await service.sync_single_resource('non-existent-resource')


class TestPerformance:
    """测试性能表现"""

    @pytest.mark.asyncio
    async def test_concurrent_discovery(self, temp_ziyuan_dir):
        """测试并发发现性能"""
        import time

        service = ResourceSyncService(ziyuan_base_path=str(temp_ziyuan_dir))

        start_time = time.time()
        await service.validate_resources()
        end_time = time.time()

        duration = end_time - start_time
        # 对于2个资源，应该在1秒内完成
        assert duration < 1.0

    def test_memory_usage(self):
        """测试内存使用情况"""
        # 这个测试可以扩展为监控内存使用
        pass


class TestIntegrationE2E:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, temp_ziyuan_dir):
        """测试端到端工作流程"""
        service = ResourceSyncService(ziyuan_base_path=str(temp_ziyuan_dir))

        # 完整的端到端流程
        try:
            # 1. 发现和验证
            validation = await service.validate_resources()
            assert validation['valid_resources'] > 0

            # 2. 生成同步计划
            sync_result = await service.sync_all_resources(dry_run=True)
            assert sync_result.total_actions > 0

            # 3. 验证监控数据
            health = service.get_health_status()
            assert health is not None

            # 4. 检查审计日志
            report = service.get_monitoring_report()
            assert 'health_status' in report

        except Exception as e:
            pytest.fail(f"端到端测试失败: {e}")

    @pytest.mark.asyncio
    async def test_large_scale_simulation(self):
        """测试大规模数据模拟"""
        # 创建大量模拟资源
        mock_resources = {}
        for i in range(100):
            mock_resources[f"resource-{i}"] = Mock(
                metadata=Mock(
                    id=f"resource-{i}",
                    title=f"资源{i}",
                    resource_type=ResourceType.PRACTICE,
                    last_modified=Mock()
                )
            )

        mock_db_state = {}

        diff_engine = IntelligentDiffEngine()
        plan = diff_engine.compute_diff(mock_resources, mock_db_state)

        assert len(plan.actions) == 100
        assert all(a.action_type == 'create' for a in plan.actions)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
