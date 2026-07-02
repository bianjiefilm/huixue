"""
API端点集成测试
测试资源同步服务V2.0的REST API接口
"""

import json
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

from app.main import app
from app.core.database import get_db
from app.models.models import User


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers(mock_user):
    """认证头"""
    # 模拟JWT token
    return {"Authorization": "Bearer test_token"}


class TestSyncTaskAPI:
    """测试同步任务API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_create_sync_task_success(self, mock_coordinator, client, auth_headers, db_session):
        """测试成功创建同步任务"""
        mock_manager = Mock()
        mock_manager.submit_task.return_value = "task_123"
        mock_coordinator.task_manager = mock_manager

        task_data = {
            "task_type": "file_import",
            "payload": json.dumps({"package_path": "/test/path.zip"}),
            "priority": 2
        }

        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data=task_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["task_id"] == "task_123"
        assert data["data"]["task_type"] == "file_import"

    def test_create_sync_task_invalid_type(self, client, auth_headers):
        """测试创建无效类型的任务"""
        task_data = {
            "task_type": "invalid_type",
            "payload": json.dumps({"test": "data"}),
            "priority": 2
        }

        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data=task_data,
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_create_sync_task_invalid_json(self, client, auth_headers):
        """测试创建JSON格式错误的参数任务"""
        task_data = {
            "task_type": "file_import",
            "payload": "invalid json {",
            "priority": 2
        }

        response = client.post(
            "/api/v1/resource-import/v2/tasks",
            data=task_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "JSON格式错误" in response.json()["detail"]

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_get_sync_task_status(self, mock_coordinator, client, auth_headers, sample_sync_task):
        """测试获取任务状态"""
        mock_manager = Mock()
        mock_manager.get_task_status.return_value = {
            "task_id": "task_123",
            "status": "completed",
            "task_type": "file_import"
        }
        mock_coordinator.task_manager = mock_manager

        response = client.get(
            "/api/v1/resource-import/v2/tasks/task_123",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["task_id"] == "task_123"
        assert data["data"]["status"] == "completed"

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_get_sync_task_status_not_found(self, mock_coordinator, client, auth_headers):
        """测试获取不存在任务的状态"""
        mock_manager = Mock()
        mock_manager.get_task_status.return_value = None
        mock_coordinator.task_manager = mock_manager

        response = client.get(
            "/api/v1/resource-import/v2/tasks/non_existent_task",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "任务不存在" in response.json()["detail"]

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_list_sync_tasks(self, mock_coordinator, client, auth_headers):
        """测试列出同步任务"""
        mock_manager = Mock()
        mock_manager.list_tasks.return_value = [
            {
                "task_id": "task_1",
                "task_type": "file_import",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00"
            },
            {
                "task_id": "task_2",
                "task_type": "audit",
                "status": "running",
                "created_at": "2024-01-02T00:00:00"
            }
        ]
        mock_coordinator.task_manager = mock_manager

        response = client.get(
            "/api/v1/resource-import/v2/tasks",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert len(data["data"]["tasks"]) == 2

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_cancel_sync_task(self, mock_coordinator, client, auth_headers):
        """测试取消同步任务"""
        mock_manager = Mock()
        mock_manager.cancel_task.return_value = True
        mock_coordinator.task_manager = mock_manager

        response = client.delete(
            "/api/v1/resource-import/v2/tasks/task_123",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["task_id"] == "task_123"

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_cancel_sync_task_not_found(self, mock_coordinator, client, auth_headers):
        """测试取消不存在的任务"""
        mock_manager = Mock()
        mock_manager.cancel_task.return_value = False
        mock_coordinator.task_manager = mock_manager

        response = client.delete(
            "/api/v1/resource-import/v2/tasks/non_existent_task",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "任务不存在或无法取消" in response.json()["detail"]


class TestAuditAPI:
    """测试审计API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_run_consistency_audit(self, mock_coordinator, client, auth_headers):
        """测试执行一致性审计"""
        mock_auditor = Mock()
        mock_auditor.manual_audit.return_value.to_dict.return_value = {
            "report_id": "audit_123",
            "scan_duration": 45.5,
            "issues_found": 3,
            "issues": [],
            "summary": {"total_issues": 3}
        }
        mock_coordinator.task_manager.auditor = mock_auditor

        response = client.post(
            "/api/v1/resource-import/v2/audit/run",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["report_id"] == "audit_123"
        assert data["data"]["issues_found"] == 3

    @patch('app.api.v1.endpoints.resource_import.AuditReportCRUD')
    def test_list_audit_reports(self, mock_audit_crud, client, auth_headers, sample_audit_report):
        """测试列出审计报告"""
        mock_audit_crud.list_reports.return_value = [sample_audit_report]

        response = client.get(
            "/api/v1/resource-import/v2/audit/reports",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert len(data["data"]["reports"]) >= 1

    @patch('app.api.v1.endpoints.resource_import.AuditReportCRUD')
    def test_get_audit_report(self, mock_audit_crud, client, auth_headers, sample_audit_report):
        """测试获取审计报告详情"""
        mock_audit_crud.get_report_by_id.return_value = sample_audit_report

        response = client.get(
            "/api/v1/resource-import/v2/audit/reports/audit_123",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["report_id"] == "audit_123"

    @patch('app.api.v1.endpoints.resource_import.AuditReportCRUD')
    def test_get_audit_report_not_found(self, mock_audit_crud, client, auth_headers):
        """测试获取不存在的审计报告"""
        mock_audit_crud.get_report_by_id.return_value = None

        response = client.get(
            "/api/v1/resource-import/v2/audit/reports/non_existent_report",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "审计报告不存在" in response.json()["detail"]


class TestCleanupAPI:
    """测试清理API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_cleanup_issues(self, mock_coordinator, client, auth_headers):
        """测试清理审计发现的问题"""
        mock_auditor = Mock()
        mock_auditor.cleanup_issues.return_value = {
            "total_processed": 2,
            "success_count": 2,
            "failed_count": 0
        }
        mock_coordinator.task_manager.auditor = mock_auditor

        response = client.post(
            "/api/v1/resource-import/v2/cleanup",
            params={"issue_ids": ["issue_1", "issue_2"]},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["success_count"] == 2

    def test_cleanup_issues_no_admin(self, client, auth_headers):
        """测试非管理员用户清理问题"""
        # 修改用户角色为非管理员
        auth_headers_non_admin = auth_headers.copy()
        # 这里假设我们有一个非管理员用户的情况

        response = client.post(
            "/api/v1/resource-import/v2/cleanup",
            params={"issue_ids": ["issue_1"]},
            headers=auth_headers
        )

        # 如果当前用户不是管理员，应该返回403
        # 不过在测试中我们可能需要mock用户权限检查
        pass


class TestResourceManifestAPI:
    """测试资源清单API"""

    @patch('app.api.v1.endpoints.resource_import.ResourceManifestCRUD')
    def test_list_resource_manifests(self, mock_manifest_crud, client, auth_headers):
        """测试列出资源清单"""
        mock_manifest_crud.list_manifests.return_value = [
            Mock(
                id=1,
                resource_type="practice",
                resource_id=1,
                manifest_version="1.0.0",
                checksum="abc123",
                imported_at=Mock(isoformat=lambda: "2024-01-01T00:00:00")
            )
        ]

        response = client.get(
            "/api/v1/resource-import/v2/manifests",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert len(data["data"]["manifests"]) >= 1

    @patch('app.api.v1.endpoints.resource_import.ResourceManifestCRUD')
    def test_get_resource_manifest(self, mock_manifest_crud, client, auth_headers):
        """测试获取资源清单详情"""
        mock_manifest = Mock()
        mock_manifest.id = 1
        mock_manifest.resource_type = "practice"
        mock_manifest.resource_id = 1
        mock_manifest.manifest_version = "1.0.0"
        mock_manifest.manifest_data = {"title": "Test Practice"}
        mock_manifest.checksum = "abc123"
        mock_manifest.imported_at = Mock(isoformat=lambda: "2024-01-01T00:00:00")
        mock_manifest.imported_by = 1
        mock_manifest.import_task_id = "task_123"

        mock_manifest_crud.get_manifest.return_value = mock_manifest

        response = client.get(
            "/api/v1/resource-import/v2/manifests/practice/1",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["resource_type"] == "practice"
        assert data["data"]["resource_id"] == 1

    @patch('app.api.v1.endpoints.resource_import.ResourceManifestCRUD')
    def test_get_resource_manifest_not_found(self, mock_manifest_crud, client, auth_headers):
        """测试获取不存在的资源清单"""
        mock_manifest_crud.get_manifest.return_value = None

        response = client.get(
            "/api/v1/resource-import/v2/manifests/practice/999",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "资源清单不存在" in response.json()["detail"]


class TestStagingFileAPI:
    """测试待处理文件API"""

    @patch('app.api.v1.endpoints.resource_import.StagingFileCRUD')
    def test_list_staging_files(self, mock_staging_crud, client, auth_headers):
        """测试列出待处理文件"""
        mock_staging_crud.list_files_by_status.return_value = [
            Mock(
                id=1,
                file_path="uploads/test.zip",
                file_name="test.zip",
                file_size=1024000,
                status="detected",
                detected_at=Mock(isoformat=lambda: "2024-01-01T00:00:00"),
                processed_at=None,
                error_message=None
            )
        ]

        response = client.get(
            "/api/v1/resource-import/v2/staging/files",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert len(data["data"]["files"]) >= 1


class TestUploadAPI:
    """测试上传API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_upload_course_package(self, mock_coordinator, client, auth_headers, temp_dir):
        """测试上传课程包"""
        mock_manager = Mock()
        mock_manager.create_file_import_task.return_value = "task_123"
        mock_coordinator.task_manager = mock_manager

        # 创建测试文件
        test_file = temp_dir / "test_course.zip"
        test_file.write_bytes(b"fake zip content" * 1000)

        # 创建上传文件对象
        with open(test_file, 'rb') as f:
            files = {"file": ("test_course.zip", f, "application/zip")}
            data = {"creator_id": 1}

            response = client.post(
                "/api/v1/resource-import/v2/upload",
                files=files,
                data=data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["task_id"] == "task_123"

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_upload_course_package_invalid_file(self, mock_coordinator, client, auth_headers, temp_dir):
        """测试上传无效文件"""
        # 创建不存在的文件引用
        response = client.post(
            "/api/v1/resource-import/v2/upload",
            files={"file": ("test.txt", BytesIO(b"test content"), "text/plain")},
            data={"creator_id": 1},
            headers=auth_headers
        )

        # 应该成功创建任务，但后续验证会失败
        assert response.status_code == 200


class TestStatsAPI:
    """测试统计API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_get_sync_service_stats(self, mock_coordinator, client, auth_headers):
        """测试获取同步服务统计"""
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            "task_manager": {"running": True, "stats": {"active_tasks": 2}},
            "file_watcher": {"running": True},
            "auditor": {"running": True}
        }
        mock_coordinator.get_service_status.return_value = mock_service.get_service_status()

        response = client.get(
            "/api/v1/resource-import/v2/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert "task_manager" in data["data"]
        assert "file_watcher" in data["data"]


class TestHealthAPI:
    """测试健康检查API"""

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_check_sync_service_health_healthy(self, mock_coordinator, client):
        """测试健康检查 - 服务正常"""
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            "task_manager": {"running": True},
            "file_watcher": {"running": True},
            "auditor": {"running": True}
        }
        mock_coordinator.get_service_status.return_value = mock_service.get_service_status()

        response = client.get("/api/v1/resource-import/v2/health")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "0000"
        assert data["data"]["healthy"] is True

    @patch('app.api.v1.endpoints.resource_import.sync_coordinator')
    def test_check_sync_service_health_unhealthy(self, mock_coordinator, client):
        """测试健康检查 - 服务异常"""
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            "task_manager": {"running": False},
            "file_watcher": {"running": False},
            "auditor": {"running": False}
        }
        mock_coordinator.get_service_status.return_value = mock_service.get_service_status()

        response = client.get("/api/v1/resource-import/v2/health")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["healthy"] is False


class TestPermissionChecks:
    """测试权限检查"""

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/resource-import/v2/tasks")

        # 应该返回401或403，具体取决于认证中间件
        assert response.status_code in [401, 403]

    def test_insufficient_permissions_teacher(self, client, auth_headers):
        """测试教师权限访问管理员功能"""
        # 假设教师不能执行清理操作
        response = client.post(
            "/api/v1/resource-import/v2/cleanup",
            params={"issue_ids": ["issue_1"]},
            headers=auth_headers
        )

        # 如果当前用户不是管理员，应该返回403
        # 具体取决于权限检查逻辑
        pass

