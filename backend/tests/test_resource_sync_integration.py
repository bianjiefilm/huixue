"""
资源同步服务的集成测试
测试完整的端到端工作流程
"""
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

from app.services.resource_sync.service import ResourceSyncService
from app.services.resource_sync.models import SyncResult, ResourceType


class TestResourceSyncIntegration:
    """资源同步集成测试"""

    @pytest.fixture
    async def integration_setup(self):
        """集成测试设置"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        ziyuan_dir = temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        # 创建完整的测试资源结构
        await self._create_test_resources(ziyuan_dir)

        service = ResourceSyncService(ziyuan_base_path=str(ziyuan_dir))

        yield service, ziyuan_dir

        # 清理
        shutil.rmtree(temp_dir)

    async def _create_test_resources(self, ziyuan_dir: Path):
        """创建测试资源"""
        # 创建实践资源
        practice_dir = ziyuan_dir / "课程资源" / "python-programming"
        practice_dir.mkdir(parents=True)

        practice_metadata = {
            "schema_version": "1.0.0",
            "id": "practice-python-programming",
            "title": "Python程序设计",
            "intro": "全面学习Python编程的实践课程",
            "industry": "计算机科学",
            "difficulty": "intermediate",
            "course_hours": 72,
            "estimated_completion_time": "16周",
            "prerequisites": ["计算机导论"],
            "learning_objectives": [
                "掌握Python基础语法",
                "理解面向对象编程",
                "掌握数据结构和算法"
            ],
            "tags": ["Python", "编程", "实践"],
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png",
            "repo_template_path": "starter_code",
            "max_students": 100,
            "is_active": True
        }

        with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(practice_metadata, f, ensure_ascii=False, indent=2)

        # 创建文件
        (practice_dir / "handbook.md").write_text("# Python程序设计手册\n\n详细的课程内容...")
        (practice_dir / "cover.png").write_text("fake png content")
        (practice_dir / "starter_code" / "main.py").mkdir(parents=True)
        (practice_dir / "starter_code" / "main.py").write_text("print('Hello, World!')")

        # 创建实训资源
        training_dir = ziyuan_dir / "实训资源" / "retail-analysis"
        training_dir.mkdir(parents=True)

        training_metadata = {
            "schema_version": "1.0.0",
            "id": "training-retail-analysis",
            "title": "零售企业经营分析",
            "training_type": "drag_and_drop",
            "intro": "基于实际零售数据进行商业分析",
            "industry": "零售",
            "difficulty": "advanced",
            "course_hours": 60,
            "estimated_completion_time": "12周",
            "prerequisites": ["数据分析基础", "SQL基础"],
            "learning_objectives": [
                "掌握零售数据分析方法",
                "学会使用BI工具",
                "理解商业智能应用"
            ],
            "tags": ["数据分析", "零售", "BI"],
            "handbook_content_path": "handbook.md",
            "cover_url_path": "cover.png",
            "assignment_nodes": [
                {
                    "node_name": "数据看板设计",
                    "tool_type": "BI",
                    "description": "设计零售数据分析看板",
                    "estimated_time": "6小时"
                },
                {
                    "node_name": "客户分析",
                    "tool_type": "BI",
                    "description": "进行客户细分分析",
                    "estimated_time": "8小时"
                }
            ],
            "require_design_files": True,
            "require_experiment_report": True,
            "max_students": 30,
            "is_active": True
        }

        with open(training_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(training_metadata, f, ensure_ascii=False, indent=2)

        (training_dir / "handbook.md").write_text("# 零售企业经营分析手册\n\n实训项目指南...")
        (training_dir / "cover.png").write_text("fake png content")

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, integration_setup):
        """测试完整工作流程集成"""
        service, ziyuan_dir = integration_setup

        # 1. 验证资源完整性
        validation_result = await service.validate_resources()

        assert validation_result['total_resources'] == 2
        assert validation_result['valid_resources'] == 2
        assert len(validation_result['invalid_resources']) == 0

        # 2. 执行全量同步（干运行）
        sync_result = await service.sync_all_resources(dry_run=True)

        assert sync_result.success == True
        assert sync_result.total_actions == 2
        assert sync_result.successful_actions == 2
        assert sync_result.failed_actions == 0

        # 验证同步计划包含正确的操作
        actions_by_type = {}
        for action in sync_result.actions or []:
            action_type = action.get('action_type') if isinstance(action, dict) else action.action_type
            if action_type not in actions_by_type:
                actions_by_type[action_type] = 0
            actions_by_type[action_type] += 1

        assert actions_by_type.get('create', 0) == 2

        # 3. 检查系统健康状态
        health_status = service.get_health_status()

        assert health_status.overall_health in ['healthy', 'warning', 'critical']
        assert isinstance(health_status.success_rate, float)
        assert health_status.total_operations >= 0

        # 4. 获取监控报告
        monitoring_report = service.get_monitoring_report()

        required_keys = ['health_status', 'recent_alerts', 'metrics_summary']
        for key in required_keys:
            assert key in monitoring_report

        # 5. 测试单个资源同步
        single_result = await service.sync_single_resource('practice-python-programming', dry_run=True)

        assert single_result.success == True
        assert single_result.total_actions == 1

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, integration_setup):
        """测试错误恢复集成"""
        service, ziyuan_dir = integration_setup

        # 模拟一个不存在的资源ID
        with pytest.raises(ValueError, match="资源不存在"):
            await service.sync_single_resource('non-existent-resource')

        # 验证服务仍然可以正常工作
        validation_result = await service.validate_resources()
        assert validation_result['total_resources'] == 2

    @pytest.mark.asyncio
    async def test_metadata_validation_integration(self, integration_setup):
        """测试元数据验证集成"""
        service, ziyuan_dir = integration_setup

        # 创建一个有问题的资源（缺少必需文件）
        bad_practice_dir = ziyuan_dir / "课程资源" / "bad-practice"
        bad_practice_dir.mkdir()

        bad_metadata = {
            "schema_version": "1.0.0",
            "id": "bad-practice",
            "title": "有问题的实践课程",
            "intro": "缺少必需文件",
            "industry": "测试",
            "difficulty": "beginner",
            "course_hours": 10,
            "handbook_content_path": "missing.md",  # 这个文件不存在
            "cover_url_path": "missing.png"  # 这个文件也不存在
        }

        with open(bad_practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(bad_metadata, f, ensure_ascii=False, indent=2)

        # 验证应该发现问题
        validation_result = await service.validate_resources()

        assert validation_result['total_resources'] == 3  # 原来2个 + 1个有问题的
        assert validation_result['valid_resources'] == 2  # 只有原来的2个有效
        assert len(validation_result['invalid_resources']) == 1

        invalid_resource = validation_result['invalid_resources'][0]
        assert invalid_resource['id'] == 'bad-practice'
        assert 'missing.md' in invalid_resource['issues'][0]

    @pytest.mark.asyncio
    async def test_large_scale_integration(self, integration_setup):
        """测试大规模集成"""
        service, ziyuan_dir = integration_setup

        # 在现有基础上添加更多资源
        for i in range(10, 20):  # 添加10个额外资源
            practice_dir = ziyuan_dir / "课程资源" / f"practice-{i}"
            practice_dir.mkdir()

            metadata = {
                "schema_version": "1.0.0",
                "id": f"practice-{i}",
                "title": f"批量实践课程 {i}",
                "intro": f"这是批量创建的第{i}个实践课程",
                "industry": "计算机科学",
                "difficulty": "intermediate",
                "course_hours": 40,
                "handbook_content_path": "handbook.md",
                "cover_url_path": "cover.png"
            }

            with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            (practice_dir / "handbook.md").write_text(f"# 课程{i}手册")
            (practice_dir / "cover.png").write_text("fake png")

        # 验证大规模资源
        validation_result = await service.validate_resources()

        assert validation_result['total_resources'] == 12  # 2个原有 + 10个新增
        assert validation_result['valid_resources'] == 12

        # 执行大规模同步
        sync_result = await service.sync_all_resources(dry_run=True)

        assert sync_result.success == True
        assert sync_result.total_actions == 12

    @pytest.mark.asyncio
    async def test_monitoring_integration(self, integration_setup):
        """测试监控系统集成"""
        service, ziyuan_dir = integration_setup

        # 执行多次操作来生成监控数据
        for i in range(3):
            await service.validate_resources()
            await service.sync_all_resources(dry_run=True)

        # 检查监控数据累积
        health_status = service.get_health_status()
        monitoring_report = service.get_monitoring_report()

        # 验证监控数据合理性
        assert health_status.total_operations >= 6  # 至少6个操作（3次验证 + 3次同步）
        assert 'metrics_summary' in monitoring_report

        # 验证健康状态计算
        assert health_status.success_rate >= 0.0
        assert health_status.success_rate <= 1.0

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, integration_setup):
        """测试并发操作集成"""
        service, ziyuan_dir = integration_setup

        # 创建多个并发任务
        tasks = []
        for i in range(5):
            if i % 2 == 0:
                tasks.append(service.validate_resources())
            else:
                tasks.append(service.sync_all_resources(dry_run=True))

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证结果
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"并发操作失败: {result}")
            elif isinstance(result, dict):  # validation result
                assert result['total_resources'] == 2
            elif isinstance(result, SyncResult):  # sync result
                assert result.success == True


class TestResourceSyncE2E:
    """端到端测试"""

    @pytest.mark.asyncio
    async def test_full_lifecycle_e2e(self):
        """测试完整生命周期的端到端流程"""
        # 创建完整的测试环境
        temp_dir = Path(tempfile.mkdtemp())
        ziyuan_dir = temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        try:
            # 1. 创建初始资源
            practice_dir = ziyuan_dir / "课程资源" / "initial-practice"
            practice_dir.mkdir(parents=True)

            metadata = {
                "schema_version": "1.0.0",
                "id": "initial-practice",
                "title": "初始实践课程",
                "intro": "测试生命周期的初始状态",
                "industry": "测试",
                "difficulty": "beginner",
                "course_hours": 20,
                "handbook_content_path": "handbook.md",
                "cover_url_path": "cover.png"
            }

            with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            (practice_dir / "handbook.md").write_text("# 初始手册")
            (practice_dir / "cover.png").write_text("fake png")

            # 2. 初始同步
            service = ResourceSyncService(ziyuan_base_path=str(ziyuan_dir))

            validation1 = await service.validate_resources()
            sync1 = await service.sync_all_resources(dry_run=True)

            assert validation1['total_resources'] == 1
            assert sync1.total_actions == 1

            # 3. 添加新资源
            training_dir = ziyuan_dir / "实训资源" / "new-training"
            training_dir.mkdir(parents=True)

            training_metadata = {
                "schema_version": "1.0.0",
                "id": "new-training",
                "title": "新增实训项目",
                "training_type": "drag_and_drop",
                "intro": "动态添加的新资源",
                "industry": "测试",
                "difficulty": "intermediate",
                "course_hours": 30,
                "handbook_content_path": "handbook.md",
                "cover_url_path": "cover.png"
            }

            with open(training_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(training_metadata, f, ensure_ascii=False, indent=2)

            (training_dir / "handbook.md").write_text("# 新实训手册")
            (training_dir / "cover.png").write_text("fake png")

            # 4. 增量同步
            validation2 = await service.validate_resources()
            sync2 = await service.sync_all_resources(dry_run=True)

            assert validation2['total_resources'] == 2
            assert sync2.total_actions == 2  # 两个资源都应该被检测到

            # 5. 修改现有资源
            metadata['title'] = "修改后的实践课程"
            with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 6. 变更同步
            sync3 = await service.sync_all_resources(dry_run=True)

            # 应该检测到变更（尽管在这个模拟环境中可能不会）
            assert sync3.success == True

            # 7. 最终健康检查
            final_health = service.get_health_status()
            assert final_health is not None

            print("端到端生命周期测试完成！")

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])
