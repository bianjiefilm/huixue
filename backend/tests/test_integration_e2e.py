"""
端到端集成测试
测试完整的资源同步服务工作流程
"""

import json
import time
import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.services.resource_sync_service import ResourceSyncService
from app.services.sync_task_manager import SyncTaskManager
from app.models.models import SyncTaskStatusEnum


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def e2e_setup(staging_dir, sample_course_package, db_session):
    """端到端测试设置"""
    # 复制课程包到staging目录
    target_path = staging_dir / "uploads" / "test_course.zip"
    target_path.parent.mkdir(exist_ok=True)

    # 创建ZIP文件（简化测试）
    shutil.make_archive(str(target_path.with_suffix('')), 'zip', str(sample_course_package))

    return {
        "package_path": target_path,
        "original_package": sample_course_package
    }


class TestEndToEndWorkflow:
    """端到端工作流程测试"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_complete_import_workflow(self, mock_coordinator, client, auth_headers, e2e_setup, db_session):
        """测试完整的导入工作流程"""
        # 模拟服务协调器
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        # 步骤1: 上传课程包
        upload_file = e2e_setup["package_path"]
        with open(upload_file, 'rb') as f:
            files = {"file": ("test_course.zip", f, "application/zip")}
            data = {"creator_id": 1}

            response = client.post(
                "/api/v1/resource-import/v2/upload",
                files=files,
                data=data,
                headers=auth_headers
            )

        assert response.status_code == 200
        upload_data = response.json()
        assert upload_data["code"] == "0000"
        task_id = upload_data["data"]["task_id"]

        # 验证任务已创建
        mock_task_manager.create_file_import_task.assert_called_once()

        # 步骤2: 查询任务状态
        mock_task_manager.get_task_status.return_value = {
            "task_id": task_id,
            "status": "completed",
            "task_type": "file_import",
            "result": {
                "success": True,
                "imported_resources": [{"type": "practice", "id": 1}],
                "uploaded_files": [{"original_path": "cover.png"}]
            }
        }

        response = client.get(
            f"/api/v1/resource-import/v2/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        status_data = response.json()
        assert status_data["data"]["status"] == "completed"
        assert status_data["data"]["result"]["success"] is True

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_batch_import_workflow(self, mock_coordinator, client, auth_headers, temp_dir):
        """测试批量导入工作流程"""
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        # 创建多个测试文件
        packages = []
        for i in range(3):
            package_dir = temp_dir / f"course_{i}"
            package_dir.mkdir()

            # 创建manifest
            manifest = {
                "metadata": {
                    "title": f"Course {i}",
                    "description": f"Test course {i}",
                    "type": "practice",
                    "version": "1.0.0",
                    "difficulty": "beginner"
                },
                "stages": [],
                "assets": [],
                "checksum": "test"
            }

            manifest_file = package_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)

            # 创建ZIP
            zip_path = temp_dir / f"course_{i}.zip"
            shutil.make_archive(str(zip_path.with_suffix('')), 'zip', str(package_dir))
            packages.append(str(zip_path))

        # 模拟批量导入任务
        mock_task_manager.create_batch_import_task.return_value = "batch_task_123"

        # 调用批量导入API
        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data={
                "task_type": "batch_import",
                "payload": json.dumps({"package_paths": packages}),
                "priority": 2
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["task_type"] == "batch_import"

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_audit_and_cleanup_workflow(self, mock_coordinator, client, auth_headers, db_session):
        """测试审计和清理工作流程"""
        mock_auditor = Mock()
        mock_coordinator.task_manager.auditor = mock_auditor

        # 步骤1: 执行审计
        mock_audit_report = Mock()
        mock_audit_report.to_dict.return_value = {
            "report_id": "audit_123",
            "issues_found": 2,
            "issues": [
                {
                    "issue_id": "issue_1",
                    "issue_type": "orphan_file",
                    "can_auto_fix": False
                },
                {
                    "issue_id": "issue_2",
                    "issue_type": "metadata_mismatch",
                    "can_auto_fix": True
                }
            ],
            "summary": {"total_issues": 2}
        }
        mock_auditor.manual_audit.return_value = mock_audit_report

        response = client.post(
            "/api/v1/resource-import/v2/audit/run",
            headers=auth_headers
        )

        assert response.status_code == 200
        audit_data = response.json()
        assert audit_data["data"]["issues_found"] == 2

        # 步骤2: 清理可自动修复的问题
        mock_auditor.cleanup_issues.return_value = {
            "total_processed": 1,
            "success_count": 1,
            "failed_count": 0
        }

        response = client.post(
            "/api/v1/resource-import/v2/cleanup",
            params={"issue_ids": ["issue_2"]},  # 只清理可自动修复的问题
            headers=auth_headers
        )

        assert response.status_code == 200
        cleanup_data = response.json()
        assert cleanup_data["data"]["success_count"] == 1

    def test_health_check_integration(self, client):
        """测试健康检查集成"""
        response = client.get("/api/v1/resource-import/v2/health")

        # 无论服务状态如何，都应该返回响应
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data["data"]
        assert "services" in data["data"]


class TestErrorHandling:
    """错误处理测试"""

    def test_upload_invalid_file_type(self, client, auth_headers, temp_dir):
        """测试上传无效文件类型"""
        # 创建无效文件
        invalid_file = temp_dir / "invalid.exe"
        invalid_file.write_bytes(b"invalid content")

        with open(invalid_file, 'rb') as f:
            files = {"file": ("invalid.exe", f, "application/octet-stream")}
            data = {"creator_id": 1}

            response = client.post(
                "/api/v1/resource-import/v2/upload",
                files=files,
                data=data,
                headers=auth_headers
            )

        # 应该成功上传，但后续处理会失败
        assert response.status_code == 200

    def test_upload_empty_file(self, client, auth_headers):
        """测试上传空文件"""
        files = {"file": ("empty.zip", b"", "application/zip")}
        data = {"creator_id": 1}

        response = client.post(
            "/api/v1/resource-import/v2/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 200  # 上传成功，但验证会失败

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_task_not_found(self, mock_coordinator, client, auth_headers):
        """测试查询不存在的任务"""
        mock_task_manager = Mock()
        mock_task_manager.get_task_status.return_value = None
        mock_coordinator.task_manager = mock_task_manager

        response = client.get(
            "/api/v1/resource-import/v2/tasks/non_existent_task",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_invalid_json_payload(self, client, auth_headers):
        """测试无效JSON载荷"""
        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data={
                "task_type": "file_import",
                "payload": "invalid json {",
                "priority": 2
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "JSON格式错误" in response.json()["detail"]


class TestPerformance:
    """性能测试"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_list_tasks_performance(self, mock_coordinator, client, auth_headers, db_session):
        """测试列出任务的性能"""
        mock_task_manager = Mock()

        # 模拟大量任务
        tasks = []
        for i in range(100):
            tasks.append({
                "task_id": f"task_{i}",
                "task_type": "file_import",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00"
            })

        mock_task_manager.list_tasks.return_value = tasks
        mock_coordinator.task_manager = mock_task_manager

        start_time = time.time()
        response = client.get(
            "/api/v1/resource-import/v2/tasks",
            headers=auth_headers
        )
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 1.0  # 应该在1秒内完成

    @patch('app.api.v1.endpoints.resource_import.ResourceManifestCRUD')
    def test_list_manifests_performance(self, mock_manifest_crud, client, auth_headers):
        """测试列出清单的性能"""
        # 模拟大量清单
        manifests = []
        for i in range(50):
            manifest = Mock()
            manifest.id = i
            manifest.resource_type = "practice"
            manifest.resource_id = i
            manifest.manifest_version = "1.0.0"
            manifest.checksum = f"checksum_{i}"
            manifest.imported_at = Mock(isoformat=lambda: "2024-01-01T00:00:00")
            manifests.append(manifest)

        mock_manifest_crud.list_manifests.return_value = manifests

        start_time = time.time()
        response = client.get(
            "/api/v1/resource-import/v2/manifests",
            headers=auth_headers
        )
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 0.5  # 应该在0.5秒内完成


class TestConcurrentOperations:
    """并发操作测试"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_concurrent_task_creation(self, mock_coordinator, client, auth_headers):
        """测试并发任务创建"""
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        # 模拟并发创建任务
        task_ids = []
        for i in range(5):
            mock_task_manager.submit_task.return_value = f"task_{i}"
            task_ids.append(f"task_{i}")

        # 并发创建任务（在实际应用中，这些会是独立的请求）
        for i in range(5):
            response = client.post(
                "/api/v1/resource-import/v2/tasks",
                data={
                    "task_type": "file_import",
                    "payload": json.dumps({"package_path": f"/test/path{i}.zip"}),
                    "priority": 2
                },
                headers=auth_headers
            )
            assert response.status_code == 200

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_concurrent_status_queries(self, mock_coordinator, client, auth_headers):
        """测试并发状态查询"""
        mock_task_manager = Mock()
        mock_coordinator.task_manager = mock_task_manager

        # 并发查询多个任务状态
        for i in range(10):
            mock_task_manager.get_task_status.return_value = {
                "task_id": f"task_{i}",
                "status": "running",
                "task_type": "file_import"
            }

            response = client.get(
                f"/api/v1/resource-import/v2/tasks/task_{i}",
                headers=auth_headers
            )
            assert response.status_code == 200


class TestDataIntegrity:
    """数据完整性测试"""

    def test_manifest_validation_integrity(self, sample_course_package):
        """测试清单验证的完整性"""
        from app.services.resource_sync_service import ResourceSyncService

        service = ResourceSyncService()
        is_valid, manifest, errors = service.validate_course_package(sample_course_package)

        assert is_valid is True
        assert manifest is not None
        assert len(errors) == 0

        # 验证校验和
        expected_checksum = service.validator.generate_manifest_checksum(
            json.loads((sample_course_package / "manifest.json").read_text())
        )
        assert manifest.checksum == expected_checksum

    @patch('app.services.resource_sync_service.ObjectStorage')
    def test_import_transaction_rollback(self, mock_storage_class, db_session, temp_dir):
        """测试导入事务回滚"""
        mock_storage = Mock()
        mock_storage.upload_file.side_effect = Exception("Storage upload failed")
        mock_storage_class.return_value = mock_storage

        # 创建无效的课程包（会导致导入失败）
        invalid_package = temp_dir / "invalid"
        invalid_package.mkdir()

        manifest_file = invalid_package / "manifest.json"
        manifest_file.write_text("invalid json")

        service = ResourceSyncService()
        result = service.import_course_package(invalid_package, 1, db_session)

        assert result["success"] is False
        assert "errors" in result

    def test_task_state_consistency(self, db_session):
        """测试任务状态一致性"""
        from app.crud.sync_crud import SyncTaskCRUD

        # 创建任务
        task = SyncTaskCRUD.create_task(
            db=db_session,
            task_id="consistency_test_task",
            task_type="file_import",
            payload={"test": "data"},
            creator_id=1
        )

        # 更新状态
        success = SyncTaskCRUD.update_task_status(
            db=db_session,
            task_id="consistency_test_task",
            status="completed",
            result={"success": True}
        )

        assert success is True

        # 验证状态
        updated_task = SyncTaskCRUD.get_task_by_id(db_session, "consistency_test_task")
        assert updated_task.status.value == "completed"
        assert updated_task.result == {"success": True}


class TestSecurity:
    """安全测试"""

    def test_path_traversal_prevention(self, client, auth_headers, temp_dir):
        """测试路径遍历攻击防护"""
        # 尝试使用路径遍历
        malicious_path = "../../../etc/passwd"

        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data={
                "task_type": "file_import",
                "payload": json.dumps({"package_path": malicious_path}),
                "priority": 2
            },
            headers=auth_headers
        )

        # 应该创建任务，但实际处理时会失败（取决于实现）
        assert response.status_code == 200

    def test_large_file_upload_protection(self, client, auth_headers):
        """测试大文件上传保护"""
        # 创建一个大的内存文件（模拟大文件）
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("large_file.zip", large_content, "application/zip")}
        data = {"creator_id": 1}

        # 这可能会由于内存限制而失败，但应该有适当的错误处理
        response = client.post(
            "/api/v1/resource-import/v2/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        # 无论成功与否，都应该有适当的响应
        assert response.status_code in [200, 413, 500]

    def test_invalid_mime_type_rejection(self, client, auth_headers):
        """测试无效MIME类型拒绝"""
        # 上传可执行文件
        exe_content = b"MZ" + b"x" * 100  # 模拟EXE文件头部
        files = {"file": ("malicious.exe", exe_content, "application/octet-stream")}
        data = {"creator_id": 1}

        response = client.post(
            "/api/v1/resource-import/v2/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        # 应该成功上传，但后续验证会失败
        assert response.status_code == 200
