"""
资源同步服务的性能测试
测试在大规模数据下的性能表现
"""
import asyncio
import time
import tempfile
import json
import shutil
from pathlib import Path
import pytest
from concurrent.futures import ThreadPoolExecutor
import psutil
import os

from app.services.resource_sync.service import ResourceSyncService
from app.services.resource_sync.discovery import ResourceDiscoveryService
from app.services.resource_sync.diff_engine import IntelligentDiffEngine
from app.services.resource_sync.models import ResourceManifest, PracticeMetadata, TrainingMetadata


class TestPerformanceBase:
    """性能测试基类"""

    def setup_method(self):
        """测试前设置"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def teardown_method(self):
        """测试后清理"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        duration = end_time - self.start_time
        memory_used = end_memory - self.start_memory

        print(".2f")
        print(".2f")


class TestDiscoveryPerformance(TestPerformanceBase):
    """测试资源发现性能"""

    @pytest.fixture
    def large_ziyuan_dir(self):
        """创建包含大量资源的测试目录"""
        temp_dir = Path(tempfile.mkdtemp())
        ziyuan_dir = temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        # 创建100个实践资源
        practice_base = ziyuan_dir / "课程资源"
        practice_base.mkdir()

        for i in range(100):
            practice_dir = practice_base / f"practice-{i:03d}"
            practice_dir.mkdir()

            # 创建metadata.json
            metadata = {
                "schema_version": "1.0.0",
                "id": f"practice-{i:03d}",
                "title": f"实践课程 {i:03d}",
                "intro": f"这是第{i}个实践课程的简介",
                "industry": "计算机科学",
                "difficulty": "intermediate",
                "course_hours": 40,
                "estimated_completion_time": "10周",
                "prerequisites": ["基础知识"],
                "learning_objectives": ["掌握概念"],
                "tags": ["测试", "实践"],
                "handbook_content_path": "handbook.md",
                "cover_url_path": "cover.png",
                "max_students": 50,
                "is_active": True
            }

            with open(practice_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 创建必需的文件
            (practice_dir / "handbook.md").write_text(f"# 实践课程 {i} 手册")
            (practice_dir / "cover.png").write_text("fake png")

        # 创建50个实训资源
        training_base = ziyuan_dir / "实训资源"
        training_base.mkdir()

        for i in range(50):
            training_dir = training_base / f"training-{i:03d}"
            training_dir.mkdir()

            metadata = {
                "schema_version": "1.0.0",
                "id": f"training-{i:03d}",
                "title": f"实训项目 {i:03d}",
                "training_type": "drag_and_drop",
                "intro": f"这是第{i}个实训项目的简介",
                "industry": "金融科技",
                "difficulty": "advanced",
                "course_hours": 60,
                "estimated_completion_time": "15周",
                "prerequisites": ["专业基础"],
                "learning_objectives": ["掌握技能"],
                "tags": ["测试", "实训"],
                "handbook_content_path": "handbook.md",
                "cover_url_path": "cover.png",
                "assignment_nodes": [
                    {
                        "node_name": f"任务{i}",
                        "tool_type": "BI",
                        "description": f"任务{i}描述",
                        "estimated_time": "8小时"
                    }
                ],
                "require_design_files": True,
                "require_experiment_report": True,
                "max_students": 25,
                "is_active": True
            }

            with open(training_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            (training_dir / "handbook.md").write_text(f"# 实训项目 {i} 手册")
            (training_dir / "cover.png").write_text("fake png")

        yield ziyuan_dir
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_large_scale_discovery_performance(self, large_ziyuan_dir):
        """测试大规模资源发现性能"""
        discovery = ResourceDiscoveryService(str(large_ziyuan_dir))

        start_time = time.time()
        resources = await discovery.discover_resources()
        end_time = time.time()

        duration = end_time - start_time

        # 验证结果
        assert len(resources) == 150  # 100实践 + 50实训
        assert duration < 10.0  # 应该在10秒内完成

        # 验证资源内容
        practice_count = sum(1 for r in resources.values()
                           if r.metadata.resource_type.value == 'practice')
        training_count = sum(1 for r in resources.values()
                           if r.metadata.resource_type.value == 'training')

        assert practice_count == 100
        assert training_count == 50

    @pytest.mark.asyncio
    async def test_concurrent_discovery_performance(self, large_ziyuan_dir):
        """测试并发发现性能"""
        # 测试多个并发发现任务
        tasks = []
        for _ in range(3):
            discovery = ResourceDiscoveryService(str(large_ziyuan_dir))
            tasks.append(discovery.discover_resources())

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        duration = end_time - start_time

        # 验证结果
        for result in results:
            assert len(result) == 150

        # 并发应该比串行更快
        assert duration < 20.0


class TestDiffEnginePerformance(TestPerformanceBase):
    """测试差异引擎性能"""

    def create_mock_resources(self, count: int):
        """创建模拟资源"""
        from unittest.mock import Mock

        resources = {}
        for i in range(count):
            resources[f"resource-{i}"] = Mock(
                metadata=Mock(
                    id=f"resource-{i}",
                    title=f"资源{i}",
                    resource_type=Mock(value='practice'),
                    last_modified=Mock()
                )
            )
        return resources

    def test_large_diff_calculation_performance(self):
        """测试大规模差异计算性能"""
        # 创建1000个文件系统资源
        fs_resources = self.create_mock_resources(1000)

        # 数据库中没有任何资源
        db_resources = {}

        diff_engine = IntelligentDiffEngine()

        start_time = time.time()
        plan = diff_engine.compute_diff(fs_resources, db_resources)
        end_time = time.time()

        duration = end_time - start_time

        # 验证结果
        assert len(plan.actions) == 1000
        assert all(a.action_type == 'create' for a in plan.actions)
        assert duration < 2.0  # 应该在2秒内完成

    def test_partial_update_performance(self):
        """测试部分更新性能"""
        # 创建1000个资源，其中一半有变更
        fs_resources = self.create_mock_resources(1000)
        db_resources = self.create_mock_resources(500)  # 只有一半

        diff_engine = IntelligentDiffEngine()

        start_time = time.time()
        plan = diff_engine.compute_diff(fs_resources, db_resources)
        end_time = time.time()

        duration = end_time - start_time

        # 验证结果：500个创建操作
        assert len(plan.actions) == 500
        assert duration < 1.0  # 应该很快完成


class TestSyncServicePerformance(TestPerformanceBase):
    """测试同步服务整体性能"""

    @pytest.mark.asyncio
    async def test_full_sync_workflow_performance(self, large_ziyuan_dir):
        """测试完整同步工作流程性能"""
        service = ResourceSyncService(ziyuan_base_path=str(large_ziyuan_dir))

        start_time = time.time()

        # 执行完整流程
        validation = await service.validate_resources()
        sync_result = await service.sync_all_resources(dry_run=True)
        health_status = service.get_health_status()

        end_time = time.time()
        duration = end_time - start_time

        # 验证结果
        assert validation['total_resources'] == 150
        assert sync_result.total_actions == 150
        assert health_status is not None

        # 性能要求：150个资源在30秒内完成
        assert duration < 30.0

    @pytest.mark.asyncio
    async def test_memory_usage_during_sync(self, large_ziyuan_dir):
        """测试同步过程中的内存使用"""
        import gc

        # 强制垃圾回收
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        service = ResourceSyncService(ziyuan_base_path=str(large_ziyuan_dir))

        # 执行同步
        await service.validate_resources()
        await service.sync_all_resources(dry_run=True)

        # 检查内存使用
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        # 内存使用应该在合理范围内（例如不超过100MB）
        assert memory_used < 100.0


class TestConcurrentLoadPerformance(TestPerformanceBase):
    """测试并发负载性能"""

    @pytest.mark.asyncio
    async def test_multiple_services_concurrent_operation(self):
        """测试多个服务并发操作"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        ziyuan_dir = temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        try:
            # 创建一些测试资源
            for i in range(10):
                res_dir = ziyuan_dir / "课程资源" / f"practice-{i}"
                res_dir.mkdir(parents=True)

                metadata = {
                    "schema_version": "1.0.0",
                    "id": f"practice-{i}",
                    "title": f"实践课程 {i}",
                    "intro": f"简介{i}",
                    "industry": "计算机",
                    "difficulty": "intermediate",
                    "course_hours": 40,
                    "handbook_content_path": "handbook.md",
                    "cover_url_path": "cover.png"
                }

                with open(res_dir / "metadata.json", 'w') as f:
                    json.dump(metadata, f)

                (res_dir / "handbook.md").write_text(f"手册{i}")
                (res_dir / "cover.png").write_text("png")

            # 创建多个服务实例并发运行
            services = [ResourceSyncService(ziyuan_base_path=str(ziyuan_dir)) for _ in range(3)]

            async def run_service_validation(service):
                return await service.validate_resources()

            start_time = time.time()
            results = await asyncio.gather(*[run_service_validation(s) for s in services])
            end_time = time.time()

            duration = end_time - start_time

            # 验证结果
            for result in results:
                assert result['total_resources'] == 10

            # 并发应该在合理时间内完成
            assert duration < 5.0

        finally:
            shutil.rmtree(temp_dir)


class TestResourceSyncLoadTest:
    """负载测试"""

    @pytest.mark.asyncio
    async def test_sustained_load_simulation(self):
        """测试持续负载模拟"""
        # 创建一个包含大量资源的模拟场景
        temp_dir = Path(tempfile.mkdtemp())
        ziyuan_dir = temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        try:
            # 创建200个资源
            for i in range(200):
                res_dir = ziyuan_dir / "课程资源" / f"practice-{i:03d}"
                res_dir.mkdir(parents=True)

                metadata = {
                    "schema_version": "1.0.0",
                    "id": f"practice-{i:03d}",
                    "title": f"实践课程 {i:03d}",
                    "intro": f"这是第{i}个实践课程的简介，包含详细的描述信息",
                    "industry": "计算机科学",
                    "difficulty": "intermediate",
                    "course_hours": 40,
                    "estimated_completion_time": "10周",
                    "prerequisites": ["基础知识", "编程基础"],
                    "learning_objectives": ["掌握基本概念", "学会应用技能"],
                    "tags": ["测试", "实践", "编程"],
                    "handbook_content_path": "handbook.md",
                    "cover_url_path": "cover.png",
                    "max_students": 50,
                    "is_active": True
                }

                with open(res_dir / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                # 创建更大的文件来测试I/O性能
                handbook_content = f"# 实践课程 {i} 手册\n\n" + "\n\n".join([
                    f"## 第{j}章\n\n这是第{j}章的内容。" * 10 for j in range(1, 11)
                ])
                (res_dir / "handbook.md").write_text(handbook_content, encoding='utf-8')
                (res_dir / "cover.png").write_text("fake png content" * 1000)

            service = ResourceSyncService(ziyuan_base_path=str(ziyuan_dir))

            # 测试持续负载
            iterations = 3
            total_time = 0

            for iteration in range(iterations):
                start_time = time.time()

                # 执行验证
                validation = await service.validate_resources()
                assert validation['total_resources'] == 200

                # 执行同步
                sync_result = await service.sync_all_resources(dry_run=True)
                assert sync_result.total_actions == 200

                end_time = time.time()
                iteration_time = end_time - start_time
                total_time += iteration_time

                print(f"迭代 {iteration + 1}: {iteration_time:.2f}秒")

            avg_time = total_time / iterations

            # 验证性能：平均每次迭代应该在10秒内完成
            assert avg_time < 10.0

            print(f"负载测试完成 - 平均每次迭代: {avg_time:.2f}秒")

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-s", "--tb=short"])
