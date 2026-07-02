"""
任务评测边界测试
测试代码长度、特殊字符、并发边界、业务边界
"""

import pytest
import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.crud import crud
from app.models import models
from app.models.models import TaskTypeEnum
from tests.fixtures.test_data_generator import TestDataGenerator


class TestBoundary:
    """边界测试类"""

    def test_empty_code(self, db_session):
        """测试空代码"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        submission_data = {
            "answer": "",
            "codeRepoHash": "hash_empty_boundary"
        }

        result = crud.submit_task_evaluation(
            db_session, task.id, student.id, submission_data
        )

        assert result["status"] == "fail"
        assert result["score"] == 0

    def test_unicode_characters(self, db_session):
        """测试Unicode字符"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        unicode_code = """
print('中文')
print('日本語')
"""
        
        submission_data = {
            "answer": unicode_code,
            "codeRepoHash": "hash_unicode"
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

            assert result["status"] == "pass"

    def test_cooldown_boundary_5_seconds(self, db_session):
        """测试冷却时间边界（5秒精确验证）"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        task = scenario["practices"][0].tasks[0]
        
        # 创建6秒前的评测记录（应该允许）
        old_eval = models.TaskEvaluationResult(
            task_id=task.id,
            user_id=student.id,
            status="fail",
            score=0,
            created_at=datetime.datetime.now() - datetime.timedelta(seconds=6)
        )
        db_session.add(old_eval)
        db_session.commit()

        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_cooldown_boundary"
        }

        with patch('app.services.code_executor.code_executor') as mock_executor:
            mock_executor.execute_io_based_code.return_value = {
                'status': 'success',
                'test_results': [{'passed': True}],
                'total_score': 100,
                'execution_time': 100
            }

            # 应该成功（超过5秒）
            result = crud.submit_task_evaluation(
                db_session, task.id, student.id, submission_data
            )

            assert result["status"] == "pass"

    def test_nonexistent_task(self, db_session):
        """测试不存在任务"""
        scenario = TestDataGenerator.create_complete_test_scenario(
            db_session, student_count=1, practice_count=1, task_count_per_practice=1
        )
        
        student = scenario["students"][0]
        
        submission_data = {
            "answer": "print('test')",
            "codeRepoHash": "hash_nonexistent"
        }

        with pytest.raises(ValueError, match="任务不存在"):
            crud.submit_task_evaluation(
                db_session, "non_existent_task_id", student.id, submission_data
            )


