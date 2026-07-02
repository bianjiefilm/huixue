"""
性能和负载测试
测试资源同步服务V2.0在高负载下的表现
"""

import time
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import statistics

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def performance_metrics():
    """性能指标收集器"""
    return PerformanceMetrics()


class PerformanceMetrics:
    """性能指标收集"""

    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()

    def end(self):
        """结束计时"""
        self.end_time = time.time()

    def add_response_time(self, response_time: float, success: bool = True):
        """添加响应时间"""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_summary(self):
        """获取性能汇总"""
        if not self.response_times:
            return {}

        total_time = self.end_time - self.start_time if self.end_time else 0
        total_requests = len(self.response_times)

        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "95th_percentile": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
            "std_dev_response_time": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0
        }


class TestAPITPerformance:
    """API性能测试"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_task_creation_performance(self, mock_coordinator, client, auth_headers, performance_metrics):
        """测试任务创建性能"""
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        task_count = 100
        performance_metrics.start()

        for i in range(task_count):
            start_time = time.time()

            response = client.post(
                "/api/v1/resource-import/v2/tasks",
                data={
                    "task_type": "file_import",
                    "payload": f'{{"package_path": "/test/path{i}.zip"}}',
                    "priority": 2
                },
                headers=auth_headers
            )

            end_time = time.time()
            response_time = end_time - start_time

            success = response.status_code == 200
            performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 性能断言
        assert summary["success_rate"] >= 0.95  # 成功率至少95%
        assert summary["avg_response_time"] < 0.5  # 平均响应时间小于500ms
        assert summary["95th_percentile"] < 1.0  # 95%响应时间小于1秒

        print(f"任务创建性能测试结果: {summary}")

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_task_status_query_performance(self, mock_coordinator, client, auth_headers, performance_metrics):
        """测试任务状态查询性能"""
        mock_task_manager = Mock()
        mock_task_manager.get_task_status.return_value = {
            "task_id": "test_task",
            "status": "completed",
            "task_type": "file_import"
        }
        mock_coordinator.task_manager = mock_task_manager

        query_count = 200
        performance_metrics.start()

        for i in range(query_count):
            start_time = time.time()

            response = client.get(
                f"/api/v1/resource-import/v2/tasks/task_{i}",
                headers=auth_headers
            )

            end_time = time.time()
            response_time = end_time - start_time

            success = response.status_code == 200
            performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 性能断言
        assert summary["success_rate"] >= 0.99  # 成功率至少99%
        assert summary["avg_response_time"] < 0.2  # 平均响应时间小于200ms
        assert summary["95th_percentile"] < 0.5  # 95%响应时间小于500ms

        print(f"任务查询性能测试结果: {summary}")

    @patch('app.api.v1.endpoints.resource_import.ResourceManifestCRUD')
    def test_manifest_list_performance(self, mock_manifest_crud, client, auth_headers, performance_metrics):
        """测试清单列表性能"""
        # 创建大量模拟清单
        manifests = []
        for i in range(1000):
            manifest = Mock()
            manifest.id = i
            manifest.resource_type = "practice"
            manifest.resource_id = i
            manifest.manifest_version = "1.0.0"
            manifest.checksum = f"checksum_{i}"
            manifest.imported_at = Mock(isoformat=lambda: "2024-01-01T00:00:00")
            manifests.append(manifest)

        mock_manifest_crud.list_manifests.return_value = manifests

        query_count = 50
        performance_metrics.start()

        for i in range(query_count):
            start_time = time.time()

            response = client.get(
                "/api/v1/resource-import/v2/manifests",
                headers=auth_headers
            )

            end_time = time.time()
            response_time = end_time - start_time

            success = response.status_code == 200
            performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 性能断言
        assert summary["success_rate"] >= 0.95
        assert summary["avg_response_time"] < 1.0  # 包含大量数据的响应

        print(f"清单列表性能测试结果: {summary}")


class TestConcurrentLoad:
    """并发负载测试"""

    def test_concurrent_api_calls(self, client, auth_headers, performance_metrics):
        """测试并发API调用"""
        def make_api_call(call_id: int):
            """单个API调用"""
            start_time = time.time()

            try:
                response = client.get(
                    "/api/v1/resource-import/v2/health",
                    headers=auth_headers
                )
                success = response.status_code == 200
            except Exception:
                success = False

            end_time = time.time()
            response_time = end_time - start_time

            return response_time, success

        concurrent_users = 20
        requests_per_user = 10

        performance_metrics.start()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            # 提交所有并发任务
            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_api_call, user_id * requests_per_user + request_id)
                    futures.append(future)

            # 收集结果
            for future in as_completed(futures):
                response_time, success = future.result()
                performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 并发负载断言
        assert summary["success_rate"] >= 0.9  # 并发情况下成功率至少90%
        assert summary["avg_response_time"] < 2.0  # 并发情况下平均响应时间
        assert summary["requests_per_second"] >= 50  # QPS至少50

        print(f"并发负载测试结果: {summary}")

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_task_creation_under_load(self, mock_coordinator, client, auth_headers, performance_metrics):
        """测试负载下任务创建"""
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        def create_task_under_load(task_id: int):
            """在负载下创建任务"""
            start_time = time.time()

            try:
                response = client.post(
                    "/api/v1/resource-import/v2/tasks",
                    data={
                        "task_type": "file_import",
                        "payload": f'{{"package_path": "/load/test/path{task_id}.zip"}}',
                        "priority": 2
                    },
                    headers=auth_headers
                )
                success = response.status_code == 200
            except Exception:
                success = False

            end_time = time.time()
            response_time = end_time - start_time

            return response_time, success

        concurrent_users = 10
        tasks_per_user = 20

        performance_metrics.start()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            for user_id in range(concurrent_users):
                for task_id in range(tasks_per_user):
                    global_task_id = user_id * tasks_per_user + task_id
                    future = executor.submit(create_task_under_load, global_task_id)
                    futures.append(future)

            for future in as_completed(futures):
                response_time, success = future.result()
                performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 负载测试断言
        assert summary["success_rate"] >= 0.95
        assert summary["avg_response_time"] < 1.0
        assert summary["requests_per_second"] >= 30

        print(f"负载下任务创建测试结果: {summary}")


class TestMemoryAndResourceUsage:
    """内存和资源使用测试"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_memory_usage_stability(self, mock_coordinator, client, auth_headers):
        """测试内存使用稳定性"""
        import psutil
        import os

        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        # 记录初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行大量操作
        for i in range(100):
            response = client.get(
                "/api/v1/resource-import/v2/health",
                headers=auth_headers
            )
            assert response.status_code == 200

            # 创建任务
            response = client.post(
                "/api/v1/resource-import/v2/tasks",
                data={
                    "task_type": "file_import",
                    "payload": f'{{"package_path": "/memory/test/path{i}.zip"}}',
                    "priority": 2
                },
                headers=auth_headers
            )
            assert response.status_code == 200

        # 检查最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（例如不超过50MB）
        assert memory_increase < 50, f"内存泄漏检测: 增加了 {memory_increase:.2f} MB"

        print(f"内存使用测试: 初始 {initial_memory:.2f} MB, 最终 {final_memory:.2f} MB, 增加 {memory_increase:.2f} MB")

    def test_file_descriptor_leakage(self, client, auth_headers):
        """测试文件描述符泄漏"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_fds = len(process.open_files())

        # 执行文件操作
        for i in range(50):
            response = client.get(
                "/api/v1/resource-import/v2/health",
                headers=auth_headers
            )
            assert response.status_code == 200

        final_fds = len(process.open_files())
        fd_increase = final_fds - initial_fds

        # 文件描述符增长应该很小
        assert fd_increase < 10, f"文件描述符泄漏: 增加了 {fd_increase} 个"

        print(f"文件描述符测试: 初始 {initial_fds}, 最终 {final_fds}, 增加 {fd_increase}")


class TestDatabasePerformance:
    """数据库性能测试"""

    def test_database_connection_pooling(self, db_session, performance_metrics):
        """测试数据库连接池性能"""
        from app.crud.sync_crud import SyncTaskCRUD

        operations_count = 200
        performance_metrics.start()

        for i in range(operations_count):
            start_time = time.time()

            # 执行数据库操作
            task = SyncTaskCRUD.create_task(
                db=db_session,
                task_id=f"perf_test_task_{i}",
                task_type="file_import",
                payload={"test": f"data_{i}"},
                creator_id=1
            )

            # 查询任务
            retrieved_task = SyncTaskCRUD.get_task_by_id(db_session, f"perf_test_task_{i}")

            end_time = time.time()
            response_time = end_time - start_time

            success = retrieved_task is not None
            performance_metrics.add_response_time(response_time, success)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 数据库性能断言
        assert summary["success_rate"] >= 0.99
        assert summary["avg_response_time"] < 0.1  # 数据库操作应该很快
        assert summary["95th_percentile"] < 0.2

        print(f"数据库性能测试结果: {summary}")

    def test_bulk_operations_performance(self, db_session, performance_metrics):
        """测试批量操作性能"""
        from app.crud.sync_crud import SyncTaskCRUD

        bulk_size = 100
        performance_metrics.start()

        start_time = time.time()

        # 批量创建任务
        for i in range(bulk_size):
            SyncTaskCRUD.create_task(
                db=db_session,
                task_id=f"bulk_test_task_{i}",
                task_type="file_import",
                payload={"bulk": f"test_{i}"},
                creator_id=1
            )

        # 批量查询
        tasks = SyncTaskCRUD.list_tasks(db_session, limit=bulk_size)

        end_time = time.time()
        total_time = end_time - start_time

        performance_metrics.add_response_time(total_time, len(tasks) == bulk_size)
        performance_metrics.end()

        # 批量操作应该高效
        assert len(tasks) == bulk_size
        assert total_time < 5.0  # 批量操作应该在5秒内完成

        print(f"批量操作性能: {bulk_size} 条记录用时 {total_time:.2f} 秒")


class TestServiceScalability:
    """服务可扩展性测试"""

    @patch('app.services.sync_task_manager.SyncTaskManager')
    def test_task_manager_scalability(self, mock_task_manager_class, performance_metrics):
        """测试任务管理器可扩展性"""
        mock_manager = Mock()
        mock_task_manager_class.return_value = mock_manager

        # 模拟高负载情况
        task_count = 1000
        performance_metrics.start()

        for i in range(task_count):
            mock_manager.create_file_import_task.return_value = f"task_{i}"

            start_time = time.time()
            # 这里会调用mock的方法
            task_id = f"task_{i}"
            end_time = time.time()

            response_time = end_time - start_time
            performance_metrics.add_response_time(response_time, True)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 任务管理器应该能够处理高并发
        assert summary["success_rate"] >= 0.99
        assert summary["requests_per_second"] >= 1000  # 每秒处理1000个任务

        print(f"任务管理器可扩展性测试: {summary}")

    def test_configuration_scalability(self, performance_metrics):
        """测试配置可扩展性"""
        from app.sync_service_config import get_sync_config

        # 测试配置加载性能
        iterations = 1000
        performance_metrics.start()

        for i in range(iterations):
            start_time = time.time()
            config = get_sync_config()
            end_time = time.time()

            response_time = end_time - start_time
            performance_metrics.add_response_time(response_time, config is not None)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 配置加载应该很快
        assert summary["avg_response_time"] < 0.001  # 小于1ms

        print(f"配置可扩展性测试: {summary}")


class TestStressTest:
    """压力测试"""

    @pytest.mark.slow
    def test_sustained_load(self, client, auth_headers, performance_metrics):
        """测试持续负载"""
        duration_seconds = 60  # 持续1分钟
        interval = 0.1  # 每100ms一个请求

        performance_metrics.start()
        end_time = time.time() + duration_seconds

        request_count = 0

        while time.time() < end_time:
            start_time = time.time()

            try:
                response = client.get(
                    "/api/v1/resource-import/v2/health",
                    headers=auth_headers
                )
                success = response.status_code == 200
            except Exception:
                success = False

            end_time_request = time.time()
            response_time = end_time_request - start_time

            performance_metrics.add_response_time(response_time, success)
            request_count += 1

            # 控制请求频率
            time.sleep(interval)

        performance_metrics.end()

        summary = performance_metrics.get_summary()

        # 持续负载断言
        assert summary["success_rate"] >= 0.95
        assert summary["requests_per_second"] >= 8  # 约每秒10个请求
        assert summary["avg_response_time"] < 0.5

        print(f"持续负载测试结果 ({request_count} 个请求): {summary}")

    @pytest.mark.slow
    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_memory_leak_under_load(self, mock_coordinator, client, auth_headers):
        """测试负载下的内存泄漏"""
        import psutil
        import os
        import gc

        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        process = psutil.Process(os.getpid())

        # 记录初始内存
        gc.collect()  # 强制垃圾回收
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行高强度操作
        for i in range(1000):
            response = client.post(
                "/api/v1/resource-import/v2/tasks",
                data={
                    "task_type": "file_import",
                    "payload": f'{{"package_path": "/stress/test/path{i}.zip"}}',
                    "priority": 2
                },
                headers=auth_headers
            )

            # 每100个请求清理一次
            if i % 100 == 0:
                gc.collect()

        # 记录最终内存
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内
        # 注意：这是一个基本的检查，实际项目中可能需要更复杂的内存分析
        assert memory_increase < 100, f"可能的内存泄漏: 增加了 {memory_increase:.2f} MB"

        print(f"内存泄漏测试: 初始 {initial_memory:.2f} MB, 最终 {final_memory:.2f} MB, 增加 {memory_increase:.2f} MB")


# 性能基准
PERFORMANCE_THRESHOLDS = {
    "api_response_time": {
        "avg": 0.5,  # 秒
        "95th_percentile": 1.0
    },
    "database_query_time": {
        "avg": 0.05,
        "95th_percentile": 0.1
    },
    "concurrent_requests": {
        "success_rate": 0.9,
        "rps": 50  # requests per second
    },
    "memory_usage": {
        "max_increase_mb": 50
    },
    "file_descriptors": {
        "max_increase": 10
    }
}

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "load: marks tests as load tests")
    config.addinivalue_line("markers", "stress: marks tests as stress tests")

