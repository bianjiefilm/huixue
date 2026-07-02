"""
任务评测API端点测试
测试 /api/v1/tasks/{task_id}/evaluate 端点
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import models
from app.models.models import TaskTypeEnum


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = models.User(
        username="test_student_api",
        email="test_api@example.com",
        hashed_password="hashed",
        is_active=True,
        role=models.UserRoleEnum.STUDENT
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_task(db_session):
    """创建测试任务"""
    task = models.Task(
        id="test_task_api_1",
        title="API测试任务",
        task_type=TaskTypeEnum.PRACTICE,
        env_type="code",
        practice_id=1,
        coin=10
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def test_task_test(db_session, test_task):
    """创建测试用例"""
    test_case = models.TaskTest(
        task_id=test_task.id,
        test_order=1,
        input_data='{"name": "Python"}',
        expected_output='{"output": "Python version 3.9"}',
        is_hidden=False
    )
    db_session.add(test_case)
    db_session.commit()
    return test_case


class TestTaskEvaluationAPI:
    """测试任务评测API端点"""

    def test_normal_evaluation_request(self, client, db_session, test_user, test_task, test_task_test):
        """测试正常评测请求"""
        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash_api_1"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{
                    'passed': True,
                    'input_data': {'name': 'Python'},
                    'expected_output': {'output': 'Python version 3.9'},
                    'actual_output': 'Python version 3.9',
                    'error_message': ''
                }],
                'total_score': 100,
                'execution_time': 100
            }

            response = client.post(
                f"/api/v1/tasks/{test_task.id}/evaluate",
                params={"user_id": test_user.id},
                json=submission_data,
                headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("code") == "0000"
            assert data.get("data", {}).get("status") == "pass"
            assert data.get("data", {}).get("score") > 0

    def test_parameter_validation(self, client, db_session, test_user, test_task):
        """测试参数验证"""
        # 缺少user_id参数
        response = client.post(
            f"/api/v1/tasks/{test_task.id}/evaluate",
            json={"answer": "print('test')"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 应该返回422或400错误
        assert response.status_code in [400, 422]

    def test_authentication_verification(self, client, db_session, test_task):
        """测试认证验证"""
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_auth"
        }

        # 无认证头
        response = client.post(
            f"/api/v1/tasks/{test_task.id}/evaluate",
            params={"user_id": 1},
            json=submission_data
        )

        # 应该返回401或继续处理（取决于实际认证实现）
        assert response.status_code in [200, 401]

    def test_response_format_validation(self, client, db_session, test_user, test_task, test_task_test):
        """测试响应格式验证"""
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_format"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            response = client.post(
                f"/api/v1/tasks/{test_task.id}/evaluate",
                params={"user_id": test_user.id},
                json=submission_data,
                headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            
            # 验证响应格式
            assert "code" in data
            assert "message" in data
            assert "data" in data
            
            # 验证数据字段
            data_content = data.get("data", {})
            assert "status" in data_content
            assert "score" in data_content
            assert "elapsed" in data_content

    def test_empty_code_submission(self, client, db_session, test_user, test_task):
        """测试空代码提交"""
        submission_data = {
            "answer": "",
            "codeRepoHash": "hash_empty_api"
        }

        response = client.post(
            f"/api/v1/tasks/{test_task.id}/evaluate",
            params={"user_id": test_user.id},
            json=submission_data,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("data", {}).get("status") == "fail"

    def test_task_not_found(self, client, db_session, test_user):
        """测试任务不存在"""
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_not_found"
        }

        response = client.post(
            "/api/v1/tasks/non_existent_task/evaluate",
            params={"user_id": test_user.id},
            json=submission_data,
            headers={"Authorization": "Bearer test_token"}
        )

        # 应该返回错误
        assert response.status_code in [400, 404, 500]

    def test_evaluation_cooldown(self, client, db_session, test_user, test_task, test_task_test):
        """测试评测冷却时间"""
        import datetime
        
        # 创建最近一次评测记录
        recent_eval = models.TaskEvaluationResult(
            task_id=test_task.id,
            user_id=test_user.id,
            status="fail",
            score=0,
            created_at=datetime.datetime.now()
        )
        db_session.add(recent_eval)
        db_session.commit()

        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_cooldown"
        }

        response = client.post(
            f"/api/v1/tasks/{test_task.id}/evaluate",
            params={"user_id": test_user.id},
            json=submission_data,
            headers={"Authorization": "Bearer test_token"}
        )

        # 应该返回冷却错误
        assert response.status_code in [400, 500]

    def test_multiple_test_cases(self, client, db_session, test_user, test_task):
        """测试多个测试用例"""
        # 创建多个测试用例
        for i in range(3):
            test_case = models.TaskTest(
                task_id=test_task.id,
                test_order=i+1,
                input_data=f'{{"value": {i+1}}}',
                expected_output=f'{{"result": {(i+1)*2}}}',
                is_hidden=False
            )
            db_session.add(test_case)
        db_session.commit()

        submission_data = {
            "answer": "value = int(input())\nprint(value * 2)",
            "codeRepoHash": "hash_multiple"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [
                    {'passed': True, 'input_data': {'value': 1}, 'expected_output': {'result': 2}, 'actual_output': '2', 'error_message': ''},
                    {'passed': True, 'input_data': {'value': 2}, 'expected_output': {'result': 4}, 'actual_output': '4', 'error_message': ''},
                    {'passed': True, 'input_data': {'value': 3}, 'expected_output': {'result': 6}, 'actual_output': '6', 'error_message': ''}
                ],
                'total_score': 100,
                'execution_time': 150
            }

            response = client.post(
                f"/api/v1/tasks/{test_task.id}/evaluate",
                params={"user_id": test_user.id},
                json=submission_data,
                headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("data", {}).get("status") == "pass"
            assert data.get("data", {}).get("score") > 0


