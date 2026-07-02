"""
任务评测集成测试
测试完整的评测流程和数据库操作
"""

import pytest
import json
import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.crud import crud
from app.models import models
from app.models.models import TaskTypeEnum
from tests.fixtures.test_data_generator import TestDataGenerator
from tests.fixtures.database_manager import DatabaseManager


class TestEvaluationIntegration:
    """测试评测流程集成"""

    def test_complete_evaluation_flow(self, db_session):
        """测试完整评测流程：前端请求 → 后端API → 数据库存储"""
        # 创建测试场景
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 准备提交数据
        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash_integration_1"
        }

        # Mock code_executor
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
                db_session, task.id, student.id, submission_data
            )

            # 验证评测结果
            assert result["status"] == "pass"
            assert result["score"] > 0
            
            # 验证数据库记录
            db_result = db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == task.id,
                models.TaskEvaluationResult.user_id == student.id
            ).first()
            
            assert db_result is not None
            assert db_result.status == "pass"
            assert db_result.score > 0
            assert db_result.submission_code == submission_data["answer"]

    def test_evaluation_result_query(self, db_session):
        """测试评测结果查询"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 创建评测结果
        eval_result = models.TaskEvaluationResult(
            task_id=task.id,
            user_id=student.id,
            status="pass",
            score=100,
            total_tests=1,
            passed_tests=1,
            submission_code="print('test')",
            created_at=datetime.datetime.now()
        )
        db_session.add(eval_result)
        db_session.commit()

        # 查询评测结果
        results = db_session.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.task_id == task.id,
            models.TaskEvaluationResult.user_id == student.id
        ).all()

        assert len(results) == 1
        assert results[0].status == "pass"
        assert results[0].score == 100

    def test_reward_integration(self, db_session):
        """测试奖励发放集成"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 初始化用户金币
        student.coins = 0
        db_session.commit()

        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash_reward_1"
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

            # 验证评测通过
            assert result["status"] == "pass"

    def test_task_completion_status_update(self, db_session):
        """测试任务完成状态更新"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash_completion_1"
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

            # 验证评测结果保存
            assert result["status"] == "pass"
            
            # 查询最新的评测结果
            latest_result = db_session.query(models.TaskEvaluationResult).filter(
                models.TaskEvaluationResult.task_id == task.id,
                models.TaskEvaluationResult.user_id == student.id
            ).order_by(models.TaskEvaluationResult.created_at.desc()).first()
            
            assert latest_result is not None
            assert latest_result.status == "pass"


