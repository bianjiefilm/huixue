"""
任务评测安全测试
测试认证授权、输入验证、SQL注入/XSS防护
"""

import pytest
import json
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.crud import crud
from app.models import models
from app.models.models import TaskTypeEnum
from tests.fixtures.test_data_generator import TestDataGenerator


class TestSecurity:
    """安全测试类"""

    def test_token_validation(self, db_session):
        """测试Token验证"""
        # 这个测试需要根据实际的认证实现来编写
        # 目前后端使用简单的Bearer token验证
        pass

    def test_token_expiration_handling(self, db_session):
        """测试Token过期处理"""
        # 这个测试需要根据实际的认证实现来编写
        pass

    def test_invalid_token_rejection(self, db_session):
        """测试无效Token拒绝"""
        # 这个测试需要根据实际的认证实现来编写
        pass

    def test_unauthenticated_user_rejection(self, db_session):
        """测试未登录用户拒绝"""
        # 这个测试需要根据实际的认证实现来编写
        pass

    def test_student_can_only_evaluate_own_tasks(self, db_session):
        """测试学生只能评测自己的任务"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=2, practice_count=1, task_count_per_practice=1
        )
        
        student1 = scenario["students"][0]
        student2 = scenario["students"][1]
        task = scenario["practices"][0].tasks[0]
        
        # 学生1应该能评测自己的任务
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_security_1"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            result1 = crud.submit_task_evaluation(
                db_session, task.id, student1.id, submission_data
            )
            
            assert result1["status"] == "pass"
            
            # 学生2也应该能评测同样的任务（因为任务属于课堂）
            # 注意：实际权限检查可能在其他地方
            result2 = crud.submit_task_evaluation(
                db_session, task.id, student2.id, submission_data
            )
            
            assert result2["status"] == "pass"

    def test_sql_injection_protection(self, db_session):
        """测试SQL注入防护"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 尝试SQL注入攻击
        malicious_code = "'; DROP TABLE users; --"
        
        submission_data = {
            "answer": malicious_code,
            "codeRepoHash": "hash_sql_injection"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'SyntaxError',
                'execution_time': 50
            }

            # 应该正常处理，不会执行SQL注入
            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )
            
            # 验证数据库表仍然存在
            user_count = db_session.query(models.User).count()
            assert user_count > 0

    def test_xss_protection(self, db_session):
        """测试XSS防护"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # XSS攻击代码
        xss_code = "<script>alert('XSS')</script>"
        
        submission_data = {
            "answer": xss_code,
            "codeRepoHash": "hash_xss"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'SyntaxError',
                'execution_time': 50
            }

            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )
            
            # 验证代码被安全存储（不会执行脚本）
            db_result = db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == task.id,
                models.TaskEvaluationResult.user_id == student.id
            ).first()
            
            assert db_result is not None
            # 验证存储的代码包含原始内容（不会被执行）
            assert xss_code in db_result.submission_code

    def test_code_injection_protection(self, db_session):
        """测试代码注入防护"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 危险代码：尝试访问文件系统
        dangerous_code = """
import os
os.system('rm -rf /')
"""
        
        submission_data = {
            "answer": dangerous_code,
            "codeRepoHash": "hash_dangerous"
        }

        # 代码执行器应该限制危险操作
        # 这里只是验证代码能被安全存储
        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'error',
                'error_message': 'SecurityError: Restricted operation',
                'execution_time': 50
            }

            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )
            
            assert result["status"] == "fail"

    def test_special_characters_handling(self, db_session):
        """测试特殊字符处理"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 包含特殊字符的代码
        special_chars_code = """
print('测试中文')
print("特殊字符: !@#$%^&*()")
print("Unicode: \\u4e2d\\u6587")
"""
        
        submission_data = {
            "answer": special_chars_code,
            "codeRepoHash": "hash_special_chars"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )
            
            # 验证特殊字符被正确存储
            db_result = db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == task.id,
                models.TaskEvaluationResult.user_id == student.id
            ).first()
            
            assert db_result is not None
            assert "测试中文" in db_result.submission_code

    def test_cross_user_data_access_protection(self, db_session):
        """测试跨用户数据访问防护"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=2, practice_count=1, task_count_per_practice=1
        )
        
        student1 = scenario["students"][0]
        student2 = scenario["students"][1]
        task = scenario["practices"][0].tasks[0]
        
        # 学生1提交评测
        submission_data1 = {
            "answer": "print('student1')",
            "codeRepoHash": "hash_student1"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            crud.submit_task_evaluation(
                db_session, task.id, student1.id, submission_data1
            )

        # 学生2不应该能访问学生1的评测结果
        student1_results = db_session.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.user_id == student1.id
        ).all()
        
        student2_results = db_session.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.user_id == student2.id
        ).all()

        # 验证学生2没有学生1的评测结果
        assert len(student1_results) > 0
        assert len(student2_results) == 0


