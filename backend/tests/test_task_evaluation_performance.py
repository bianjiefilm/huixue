"""
任务评测性能测试
测试并发评测、响应时间、资源使用
"""

import pytest
import time
import threading
import concurrent.futures
import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.crud import crud
from app.models import models
from app.models.models import TaskTypeEnum
from tests.fixtures.test_data_generator import TestDataGenerator


class TestPerformance:
    """性能测试类"""

    def test_single_evaluation_response_time(self, db_session):
        """测试单次评测响应时间"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        submission_data = {
            "answer": 'name = "Python"\nversion = 3.9\nprint(f"{name} version {version}")',
            "codeRepoHash": "hash_perf_1"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            start_time = time.time()
            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )
            elapsed_time = time.time() - start_time

            assert result["status"] == "pass"
            assert elapsed_time < 5.0  # 单次评测应该在5秒内完成

    def test_concurrent_evaluations_10(self, db_session):
        """测试10个并发评测请求"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=10, practice_count=1, task_count_per_practice=1
        )
        
        task = scenario["practices"][0].tasks[0]
        
        def evaluate_task_for_student(student_id):
            """为单个学生执行评测"""
            submission_data = {
                "answer": f'print("Student {student_id}")',
                "codeRepoHash": f"hash_concurrent_{student_id}"
            }

            with patch('app.services.code_executor.code_executor') as mock_executor:
                mock_executor.execute_io_based_code.return_value = {
                    'status': 'success',
                    'test_results': [{'passed': True}],
                    'total_score': 100,
                    'execution_time': 100
                }

                try:
                    result = crud.submit_task_evaluation(
                        db_session, task.id, student_id, submission_data
                    )
                    return result["status"] == "pass"
                except Exception as e:
                    return False

        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(evaluate_task_for_student, student.id)
                for student in scenario["students"]
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time

        # 验证大部分请求成功
        success_count = sum(results)
        assert success_count >= 8  # 至少80%成功
        assert elapsed_time < 10.0  # 10个并发请求应该在10秒内完成

    def test_database_query_performance(self, db_session):
        """测试数据库查询性能"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 创建多个评测结果
        for i in range(10):
            eval_result = models.TaskEvaluationResult(
                task_id=task.id,
                user_id=student.id,
                status="pass" if i % 2 == 0 else "fail",
                score=100 if i % 2 == 0 else 0,
                total_tests=1,
                passed_tests=1 if i % 2 == 0 else 0,
                submission_code=f"print('test_{i}')",
                created_at=datetime.datetime.now()
            )
            db_session.add(eval_result)
        db_session.commit()

        # 测试查询性能
        start_time = time.time()
        
        results = db_session.query(models.TaskEvaluationResult).filter(
            models.TaskEvaluationResult.task_id == task.id,
            models.TaskEvaluationResult.user_id == student.id
        ).all()
        
        elapsed_time = time.time() - start_time

        assert len(results) == 10
        assert elapsed_time < 1.0  # 查询应该在1秒内完成


