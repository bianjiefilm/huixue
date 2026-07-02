"""
任务评测单元测试
测试 submit_task_evaluation、_execute_evaluation、_parse_test_script_output 函数
"""

import pytest
import json
import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.crud import crud
from app.models import models
from app.models.models import TaskTypeEnum

# 注意：code_executor 是在函数内部导入的，需要通过 patch 来 mock


class TestSubmitTaskEvaluation:
    """测试 submit_task_evaluation 函数"""

    def test_normal_evaluation_flow(self, db_session):
        """测试正常评测流程"""
        # 创建测试用户
        user = models.User(
            username="test_student",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 创建测试任务
        task = models.Task(
            id="test_task_1",
            title="测试任务",
            task_type=TaskTypeEnum.PRACTICE,
            env_type="code",
            practice_id=1,
            coin=10
        )
        db_session.add(task)
        db_session.commit()

        # 创建测试用例
        test_case = models.TaskTest(
            task_id="test_task_1",
            case_id="case_test_task_1_1",
            test_order=1,
            input_data='{"name": "Python"}',
            expected_output='{"output": "Python version 3.9"}',
            is_hidden=False
        )
        db_session.add(test_case)
        db_session.commit()

        # 准备提交数据
        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash123"
        }

        # Mock code_executor (在函数内部导入，需要patch模块)
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

            # 执行评测
            result = crud.submit_task_evaluation(
                db_session, "test_task_1", user.id, submission_data
            )

            # 验证结果
            assert result["status"] == "pass"
            assert result["score"] > 0
            assert result["passed_tests"] == 1
            assert result["total_tests"] == 1

            # 验证数据库记录
            db_result = db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == "test_task_1",
                models.TaskEvaluationResult.user_id == user.id
            ).first()
            assert db_result is not None
            assert db_result.status == "pass"

    def test_cooldown_validation(self, db_session):
        """测试冷却时间验证（5秒间隔）"""
        # 创建测试用户和任务
        user = models.User(
            username="test_student2",
            email="test2@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        
        task = models.Task(
            id="test_task_2",
            title="测试任务2",
            task_type=TaskTypeEnum.PRACTICE,
            env_type="code",
            practice_id=1,
            coin=10
        )
        db_session.add(task)
        db_session.commit()

        # 创建一次评测记录（刚刚创建）
        recent_eval = models.TaskEvaluationResult(
            task_id="test_task_2",
            user_id=user.id,
            status="fail",
            score=0,
            created_at=datetime.datetime.now()
        )
        db_session.add(recent_eval)
        db_session.commit()

        # 尝试立即再次评测
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash456"
        }

        with pytest.raises(ValueError, match="评测冷却中"):
            crud.submit_task_evaluation(
                db_session, "test_task_2", user.id, submission_data
            )

    def test_task_not_found(self, db_session):
        """测试任务不存在错误处理"""
        user = models.User(
            username="test_student3",
            email="test3@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash789"
        }

        with pytest.raises(ValueError, match="任务不存在"):
            crud.submit_task_evaluation(
                db_session, "non_existent_task", user.id, submission_data
            )

    def test_empty_code_handling(self, db_session):
        """测试空代码处理"""
        user = models.User(
            username="test_student4",
            email="test4@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        
        task = models.Task(
            id="test_task_3",
            title="测试任务3",
            task_type=TaskTypeEnum.PRACTICE,
            env_type="code",
            practice_id=1,
            coin=10
        )
        db_session.add(task)
        db_session.commit()

        # 提交空代码
        submission_data = {
            "answer": "",
            "codeRepoHash": "hash_empty"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            result = crud.submit_task_evaluation(
                db_session, "test_task_3", user.id, submission_data
            )

            # 应该返回失败状态
            assert result["status"] == "fail"
            assert result["score"] == 0
            assert "代码不能为空" in result.get("error_message", "")


class TestExecuteEvaluation:
    """测试 _execute_evaluation 函数"""

    def test_code_execution_success(self):
        """测试代码执行成功"""
        # 创建mock任务
        task = Mock()
        task.task_type = TaskTypeEnum.PRACTICE
        task.coin = 10
        task.evaluation_script_path = None

        # 创建mock测试用例
        tests = [
            Mock(
                input_data='{"name": "Python"}',
                expected_output='{"output": "Python version 3.9"}',
                is_hidden=False
            )
        ]

        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")'
        }

        # Mock code_executor (在函数内部导入，需要patch模块)
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

            result = crud._execute_evaluation(task, tests, submission_data)

            assert result["status"] == "pass"
            assert result["score"] > 0
            assert result["passed_tests"] == 1
            assert result["total_tests"] == 1
            assert len(result["test_results"]) == 1

    def test_code_execution_syntax_error(self):
        """测试代码语法错误"""
        task = Mock()
        task.task_type = TaskTypeEnum.PRACTICE
        task.coin = 10
        task.evaluation_script_path = None

        tests = [Mock(input_data='{}', expected_output='{}', is_hidden=False)]

        submission_data = {
            "answer": "print('unclosed quote"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'SyntaxError: unterminated string literal',
                'execution_time': 50
            }

            result = crud._execute_evaluation(task, tests, submission_data)

            assert result["status"] == "fail"
            assert result["score"] == 0
            assert result["passed_tests"] == 0
            assert "SyntaxError" in result.get("error_message", "")

    def test_code_execution_runtime_error(self):
        """测试代码运行时错误"""
        task = Mock()
        task.task_type = TaskTypeEnum.PRACTICE
        task.coin = 10
        task.evaluation_script_path = None

        tests = [Mock(input_data='{}', expected_output='{}', is_hidden=False)]

        submission_data = {
            "answer": "x = 1 / 0"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'ZeroDivisionError: division by zero',
                'execution_time': 50
            }

            result = crud._execute_evaluation(task, tests, submission_data)

            assert result["status"] == "fail"
            assert result["score"] == 0
            assert "ZeroDivisionError" in result.get("error_message", "")

    def test_test_cases_pass_fail(self):
        """测试测试用例通过/失败"""
        task = Mock()
        task.task_type = TaskTypeEnum.PRACTICE
        task.coin = 10
        task.evaluation_script_path = None

        tests = [
            Mock(input_data='{"a": 1}', expected_output='{"result": 2}', is_hidden=False),
            Mock(input_data='{"a": 2}', expected_output='{"result": 4}', is_hidden=False)
        ]

        # 只通过第一个测试用例
        submission_data = {
            "answer": "a = int(input())\nprint(a * 2)"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [
                    {'passed': True, 'input_data': {'a': 1}, 'expected_output': {'result': 2}, 'actual_output': '2', 'error_message': ''},
                    {'passed': False, 'input_data': {'a': 2}, 'expected_output': {'result': 4}, 'actual_output': '5', 'error_message': '输出不匹配'}
                ],
                'total_score': 50,
                'execution_time': 100
            }

            result = crud._execute_evaluation(task, tests, submission_data)

            assert result["status"] == "fail"
            assert result["passed_tests"] == 1
            assert result["total_tests"] == 2

    def test_timeout_handling(self):
        """测试超时处理"""
        task = Mock()
        task.task_type = TaskTypeEnum.PRACTICE
        task.coin = 10
        task.evaluation_script_path = None

        tests = [Mock(input_data='{}', expected_output='{}', is_hidden=False)]

        submission_data = {
            "answer": "while True: pass"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'Execution timeout',
                'execution_time': 30000  # 30秒超时
            }

            result = crud._execute_evaluation(task, tests, submission_data)

            assert result["status"] == "fail"
            assert "timeout" in result.get("error_message", "").lower()

    def test_multiple_env_types(self):
        """测试多种环境类型"""
        # 测试 code 环境
        task_code = Mock()
        task_code.task_type = TaskTypeEnum.PRACTICE
        task_code.coin = 10
        task_code.evaluation_script_path = None
        task_code.env_type = "code"

        tests = [Mock(input_data='{}', expected_output='{}', is_hidden=False)]

        submission_data = {
            "answer": "print('Hello')"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            result = crud._execute_evaluation(task_code, tests, submission_data)
            assert result["status"] == "pass"


class TestParseTestScriptOutput:
    """测试 _parse_test_script_output 函数"""

    def test_standard_output_format(self):
        """测试标准输出格式解析"""
        output = """
        得分: 80/100
        通过用例: 3
        总测试用例: 4
        ✅ 测试用例1 - PASS
        ✅ 测试用例2 - PASS
        ✅ 测试用例3 - PASS
        ❌ 测试用例4 - FAIL
        """

        result = crud._parse_test_script_output(output)

        assert result["status"] == "pass"  # 80分 >= 60
        assert result["total_score"] == 80
        assert result["max_score"] == 100
        assert len(result["test_results"]) == 4
        assert result["test_results"][0]["passed"] == True
        assert result["test_results"][3]["passed"] == False

    def test_non_standard_output_format(self):
        """测试非标准输出格式处理"""
        output = "得分: 50"

        result = crud._parse_test_script_output(output)

        assert result["status"] == "fail"  # 50分 < 60
        assert result["total_score"] == 50
        assert result["max_score"] == 100

    def test_empty_output_handling(self):
        """测试空输出处理"""
        output = ""

        result = crud._parse_test_script_output(output)

        assert result["status"] == "fail"
        assert result["total_score"] == 0
        assert len(result["test_results"]) == 0

    def test_error_message_extraction(self):
        """测试错误信息提取"""
        output = """
        得分: 0/100
        通过用例: 0
        总测试用例: 2
        ❌ 测试用例1 - FAIL: 语法错误
        ❌ 测试用例2 - FAIL: 运行时错误
        """

        result = crud._parse_test_script_output(output)

        assert result["status"] == "fail"
        assert result["total_score"] == 0
        assert len(result["test_results"]) == 2
        assert result["test_results"][0]["passed"] == False
        assert result["test_results"][1]["passed"] == False

    def test_fallback_score_calculation(self):
        """测试备用得分计算"""
        output = "一些没有标准格式的输出"

        result = crud._parse_test_script_output(output)

        assert result["status"] == "fail"
        assert result["total_score"] == 0
        assert result["max_score"] == 100

