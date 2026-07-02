"""
数据一致性管理器单元测试
测试 DataConsistencyManager 的审计和修复功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.data_consistency_manager import (
    DataConsistencyManager, ConsistencyIssue, ConsistencyReport
)
from app.models.models import Task, TrainingAsset, TrainingDataset


class TestConsistencyIssue:
    """测试一致性问题类"""

    def test_consistency_issue_creation(self):
        """测试一致性问题创建"""
        issue = ConsistencyIssue(
            issue_id="test_issue_123",
            issue_type="orphan_file",
            severity="medium",
            category="file_system",
            resource_id=None,
            resource_type=None,
            path="/test/orphan/file.txt",
            description="发现孤儿文件",
            details={"file_path": "/test/orphan/file.txt"},
            suggested_action="检查文件是否仍然需要",
            can_auto_fix=False,
            discovered_at="2024-01-01T00:00:00Z",
            tags=["file_system", "orphan"]
        )

        assert issue.issue_id == "test_issue_123"
        assert issue.issue_type == "orphan_file"
        assert issue.severity == "medium"
        assert issue.can_auto_fix is False
        assert len(issue.tags) == 2

    def test_consistency_issue_to_dict(self):
        """测试序列化为字典"""
        issue = ConsistencyIssue(
            issue_id="test_issue_123",
            issue_type="metadata_mismatch",
            severity="low",
            category="practice",
            resource_id=1,
            resource_type="practice",
            path=None,
            description="任务数量不匹配",
            details={"expected": 5, "actual": 3},
            suggested_action="更新任务数量",
            can_auto_fix=True,
            discovered_at="2024-01-01T00:00:00Z",
            tags=["practice", "metadata"]
        )

        data = issue.to_dict()

        assert data["issue_id"] == "test_issue_123"
        assert data["issue_type"] == "metadata_mismatch"
        assert data["severity"] == "low"
        assert data["can_auto_fix"] is True
        assert data["details"]["expected"] == 5


class TestConsistencyReport:
    """测试一致性报告类"""

    def test_consistency_report_creation(self):
        """测试一致性报告创建"""
        issues = [
            ConsistencyIssue(
                issue_id="issue_1",
                issue_type="orphan_file",
                severity="medium",
                category="file_system",
                resource_id=None,
                resource_type=None,
                path="/test/file.txt",
                description="孤儿文件",
                details={"file_size": 1024},
                suggested_action="删除文件",
                can_auto_fix=False,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            ),
            ConsistencyIssue(
                issue_id="issue_2",
                issue_type="phantom_record",
                severity="critical",
                category="training",
                resource_id=1,
                resource_type="training",
                path=None,
                description="幽灵记录",
                details={"training_id": 1},
                suggested_action="删除记录",
                can_auto_fix=True,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            )
        ]

        report = ConsistencyReport(
            report_id="consistency_123",
            timestamp="2024-01-01T00:00:00Z",
            scan_duration=45.5,
            total_issues=2,
            issues_by_severity={"medium": 1, "critical": 1},
            issues_by_category={"file_system": 1, "training": 1},
            issues_by_type={"orphan_file": 1, "phantom_record": 1},
            auto_fixable_issues=1,
            critical_issues=1,
            issues=issues,
            summary={"total_issues": 2, "critical_issues": 1},
            recommendations=["存在严重问题，建议立即处理"]
        )

        assert report.report_id == "consistency_123"
        assert report.total_issues == 2
        assert report.critical_issues == 1
        assert report.auto_fixable_issues == 1
        assert len(report.issues) == 2

    def test_consistency_report_to_dict(self):
        """测试报告序列化"""
        report = ConsistencyReport(
            report_id="test_report",
            timestamp="2024-01-01T00:00:00Z",
            scan_duration=30.0,
            total_issues=1,
            issues_by_severity={"low": 1},
            issues_by_category={"practice": 1},
            issues_by_type={"metadata_mismatch": 1},
            auto_fixable_issues=1,
            critical_issues=0,
            issues=[],
            summary={"total_issues": 1},
            recommendations=["可以自动修复"]
        )

        data = report.to_dict()

        assert data["report_id"] == "test_report"
        assert data["total_issues"] == 1
        assert data["critical_issues"] == 0
        assert data["auto_fixable_issues"] == 1
        assert len(data["recommendations"]) == 1


class TestDataConsistencyManager:
    """测试数据一致性管理器"""

    def test_init(self):
        """测试管理器初始化"""
        manager = DataConsistencyManager()
        assert manager.issues == []
        assert hasattr(manager, '_check_storage_file_exists')

    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_practices')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_trainings')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_courses')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_file_system')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_resource_manifests')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._audit_staging_files')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._generate_recommendations')
    def test_perform_full_audit(self, mock_recommendations, mock_staging, mock_manifests,
                               mock_file_system, mock_courses, mock_trainings, mock_practices,
                               db_session):
        """测试执行完整一致性审计"""
        # 设置mock返回值
        mock_practices.return_value = None
        mock_trainings.return_value = None
        mock_courses.return_value = None
        mock_file_system.return_value = None
        mock_manifests.return_value = None
        mock_staging.return_value = None
        mock_recommendations.return_value = ["测试建议"]

        manager = DataConsistencyManager()
        report = manager.perform_full_audit(db_session)

        assert isinstance(report, ConsistencyReport)
        assert report.total_issues >= 0  # 审计结果可能为0或更多
        assert report.scan_duration >= 0
        assert isinstance(report.issues, list)
        assert isinstance(report.summary, dict)

        # 验证方法被调用
        mock_practices.assert_called_once()
        mock_trainings.assert_called_once()
        mock_courses.assert_called_once()
        mock_file_system.assert_called_once()
        mock_manifests.assert_called_once()
        mock_staging.assert_called_once()

    def test_audit_practices_task_count_mismatch(self, db_session, sample_practice):
        """测试审计实践任务数量不匹配"""
        # 创建不匹配的任务数量
        sample_practice.task_count = 5  # 设置为5个任务

        # 只创建一个任务
        task = Task(
            practice_id=sample_practice.id,
            title="Test Task",
            task_type="PRACTICE",
            order_in_practice=1
        )
        db_session.add(task)
        db_session.commit()

        manager = DataConsistencyManager()
        manager._audit_practices(db_session)

        # 应该发现问题
        assert len(manager.issues) == 1
        issue = manager.issues[0]
        assert issue.issue_type == "metadata_mismatch"
        assert issue.category == "practice"
        assert issue.resource_id == sample_practice.id
        assert "任务数量不匹配" in issue.description
        assert issue.can_auto_fix is True

    def test_audit_practices_environment_id_invalid(self, db_session, sample_practice):
        """测试审计实践环境ID无效"""
        sample_practice.environment_id = "invalid_env_id"

        manager = DataConsistencyManager()
        manager._audit_practices(db_session)

        # 应该发现问题
        assert len(manager.issues) >= 1
        issue = manager.issues[-1]  # 最后一个问题
        assert issue.issue_type == "invalid_reference"
        assert issue.category == "practice"
        assert "无效的环境ID" in issue.description

    @patch('app.services.data_consistency_manager.DataConsistencyManager._check_storage_file_exists')
    def test_audit_trainings_missing_asset(self, mock_check_storage, db_session, sample_training):
        """测试审计实训缺失素材"""
        mock_check_storage.return_value = False  # 模拟文件不存在

        # 为training设置环境ID以避免incomplete_config问题
        sample_training.environment_id = 1

        # 创建素材记录
        asset = TrainingAsset(
            training_id=sample_training.id,
            name="test_asset.png",
            relative_path="assets/test_asset.png",
            file_type="image/png",
            file_size=1024,
            uploader_id=1
        )
        db_session.add(asset)
        db_session.commit()

        manager = DataConsistencyManager()
        manager._audit_trainings(db_session)

        # 应该发现phantom_record问题
        assert len(manager.issues) >= 1
        phantom_issues = [issue for issue in manager.issues if issue.issue_type == "phantom_record"]
        assert len(phantom_issues) >= 1
        issue = phantom_issues[0]
        assert issue.category == "training"
        assert "文件不存在" in issue.description
        assert issue.severity == "critical"
        assert issue.can_auto_fix is False

    @patch('app.services.data_consistency_manager.DataConsistencyManager._check_storage_file_exists')
    def test_audit_trainings_missing_dataset(self, mock_check_storage, db_session, sample_training):
        """测试审计实训缺失数据集"""
        mock_check_storage.return_value = False  # 模拟文件不存在

        # 为training设置环境ID以避免incomplete_config问题
        sample_training.environment_id = 1

        # 创建数据集记录
        dataset = TrainingDataset(
            training_id=sample_training.id,
            name="test_dataset.csv",
            file_url="datasets/test_dataset.csv",
            relative_path="datasets/test_dataset.csv",
            file_type="csv",
            file_size=2048,
            uploader_id=1
        )
        db_session.add(dataset)
        db_session.commit()

        manager = DataConsistencyManager()
        manager._audit_trainings(db_session)

        # 应该发现phantom_record问题
        assert len(manager.issues) >= 1
        phantom_issues = [issue for issue in manager.issues if issue.issue_type == "phantom_record"]
        assert len(phantom_issues) >= 1
        issue = phantom_issues[0]
        assert issue.category == "training"
        assert "文件不存在" in issue.description

    def test_audit_trainings_missing_environment(self, db_session, sample_training):
        """测试审计实训缺失环境配置"""
        # 编码式实训但没有环境ID
        sample_training.training_type = "CODING"
        sample_training.environment_id = None

        manager = DataConsistencyManager()
        manager._audit_trainings(db_session)

        # 应该发现问题
        assert len(manager.issues) >= 1
        issue = manager.issues[-1]
        assert issue.issue_type == "incomplete_config"
        assert "缺少环境ID配置" in issue.description

    @patch('app.services.data_consistency_manager.DataConsistencyManager._get_all_storage_files')
    @patch('app.services.data_consistency_manager.DataConsistencyManager._get_all_referenced_files')
    def test_audit_file_system_orphan_files(self, mock_referenced, mock_storage, db_session):
        """测试审计文件系统孤儿文件"""
        # 模拟存储中有文件但数据库没有引用
        mock_storage.return_value = {"file1.txt", "file2.txt", "important.doc"}
        mock_referenced.return_value = {"file1.txt"}  # 只引用了file1.txt

        manager = DataConsistencyManager()
        manager._audit_file_system(db_session)

        # 应该发现孤儿文件问题
        orphan_issues = [i for i in manager.issues if i.issue_type == "orphan_file"]
        assert len(orphan_issues) >= 2  # file2.txt 和 important.doc

        for issue in orphan_issues:
            assert issue.severity == "medium"
            assert issue.category == "file_system"
            assert issue.can_auto_fix is False

    @patch('app.services.data_consistency_manager.DataConsistencyManager._check_storage_file_exists')
    def test_check_storage_file_exists(self, mock_check):
        """测试存储文件存在性检查"""
        mock_check.return_value = True

        manager = DataConsistencyManager()
        result = manager._check_storage_file_exists("test/file.txt")

        assert result is True
        mock_check.assert_called_once()

    def test_is_valid_environment_id(self):
        """测试环境ID有效性检查"""
        manager = DataConsistencyManager()

        # 测试有效的环境ID
        assert manager._is_valid_environment_id("python-3.9") is True
        assert manager._is_valid_environment_id("123") is True  # 数字ID
        assert manager._is_valid_environment_id("java-11") is True

        # 测试无效的环境ID
        assert manager._is_valid_environment_id("any_env_id") is False
        assert manager._is_valid_environment_id("") is False

    def test_count_database_records(self, db_session, sample_practice, sample_training):
        """测试统计数据库记录"""
        manager = DataConsistencyManager()
        counts = manager._count_database_records(db_session)

        assert "practices" in counts
        assert "trainings" in counts
        assert "courses" in counts
        assert counts["practices"] >= 1
        assert counts["trainings"] >= 1

    def test_generate_recommendations(self):
        """测试生成建议"""
        manager = DataConsistencyManager()

        # 测试不同场景的建议
        issues = [
            ConsistencyIssue(
                issue_id="critical_1",
                issue_type="phantom_record",
                severity="critical",
                category="training",
                resource_id=1,
                resource_type="training",
                path=None,
                description="严重问题",
                details={"training_id": 1},
                suggested_action="立即处理",
                can_auto_fix=False,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            ),
            ConsistencyIssue(
                issue_id="auto_fix_1",
                issue_type="metadata_mismatch",
                severity="low",
                category="practice",
                resource_id=1,
                resource_type="practice",
                path=None,
                description="可自动修复",
                details={"practice_id": 1},
                suggested_action="自动修复",
                can_auto_fix=True,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            ),
            ConsistencyIssue(
                issue_id="orphan_1",
                issue_type="orphan_file",
                severity="medium",
                category="file_system",
                resource_id=None,
                resource_type=None,
                path="/orphan/file.txt",
                description="孤儿文件",
                details={"file_size": 2048},
                suggested_action="清理文件",
                can_auto_fix=False,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            )
        ]

        recommendations = manager._generate_recommendations(issues)

        assert len(recommendations) >= 2
        assert any("严重问题" in rec for rec in recommendations)
        assert any("可以自动修复" in rec for rec in recommendations)
        assert any("孤儿文件" in rec for rec in recommendations)

    def test_generate_recommendations_many_issues(self):
        """测试大量问题的建议"""
        manager = DataConsistencyManager()

        # 创建60个问题
        issues = []
        for i in range(60):
            issues.append(ConsistencyIssue(
                issue_id=f"issue_{i}",
                issue_type="metadata_mismatch",
                severity="low",
                category="practice",
                resource_id=i+1,
                resource_type="practice",
                path=None,
                description=f"问题{i}",
                details={"practice_id": i+1},
                suggested_action=f"修复{i}",
                can_auto_fix=True,
                discovered_at="2024-01-01T00:00:00Z",
                tags=[]
            ))

        recommendations = manager._generate_recommendations(issues)

        assert len(recommendations) >= 1
        assert any("问题数量较多" in rec for rec in recommendations)

    def test_is_system_file(self):
        """测试系统文件判断"""
        manager = DataConsistencyManager()

        # 系统文件
        assert manager._is_system_file("/tmp/temp.txt") is True
        assert manager._is_system_file("node_modules/package.json") is True
        assert manager._is_system_file(".git/config") is True
        assert manager._is_system_file("cache/file.bak") is True

        # 普通文件
        assert manager._is_system_file("data/user_file.txt") is False
        assert manager._is_system_file("assets/image.png") is False
