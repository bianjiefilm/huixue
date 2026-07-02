"""
测试数据生成器
自动生成测试用户、课堂、课程、任务、代码样本
"""

import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import models


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_username(prefix: str = "test_student") -> str:
        """生成测试用户名"""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}_{suffix}"

    @staticmethod
    def create_test_user(
        db: Session,
        username: str = None,
        role: str = "student",
        email: str = None
    ) -> models.User:
        """创建测试用户"""
        if username is None:
            username = TestDataGenerator.generate_username()
        
        if email is None:
            email = f"{username}@test.com"

        user = models.User(
            username=username,
            email=email,
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_test_classroom(
        db: Session,
        teacher_id: int,
        name: str = None,
        status: str = "ongoing"
    ) -> models.Classroom:
        """创建测试课堂"""
        if name is None:
            name = f"测试课堂_{random.randint(1000, 9999)}"

        classroom = models.Classroom(
            name=name,
            teacher_id=teacher_id,
            status=getattr(models.ClassroomStatusEnum, status.upper()),
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() + timedelta(days=30)
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def create_test_practice(
        db: Session,
        title: str = None,
        difficulty: str = "beginner",
        task_count: int = 1
    ) -> models.Practice:
        """创建测试实践课程"""
        if title is None:
            title = f"测试实践_{random.randint(1000, 9999)}"

        practice = models.Practice(
            title=title,
            description=f"这是{title}的描述",
            direction="编程语言",
            category="Python基础",
            difficulty=getattr(models.DifficultyLevelEnum, difficulty.lower()),
            coin=10,
            task_count=task_count
        )
        db.add(practice)
        db.commit()
        db.refresh(practice)
        return practice

    @staticmethod
    def create_test_task(
        db: Session,
        practice_id: int,
        title: str = None,
        task_type: str = "PRACTICE",
        env_type: str = "code",
        order: int = 1,
        coin: int = 10
    ) -> models.Task:
        """创建测试任务"""
        if title is None:
            title = f"测试任务_{order}"

        task = models.Task(
            id=f"task_{practice_id}_{order}_{random.randint(1000, 9999)}",
            title=title,
            task_type=getattr(models.TaskTypeEnum, task_type),
            env_type=env_type,
            practice_id=practice_id,
            order_in_practice=order,
            coin=coin,
            difficulty="BEGINNER"  # Task的difficulty是String类型，不是枚举
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def create_test_task_test(
        db: Session,
        task_id: str,
        test_order: int = 1,
        input_data: str = None,
        expected_output: str = None,
        is_hidden: bool = False
    ) -> models.TaskTest:
        """创建测试用例"""
        if input_data is None:
            input_data = '{"name": "Python"}'
        if expected_output is None:
            expected_output = '{"output": "Python version 3.9"}'

        test = models.TaskTest(
            task_id=task_id,
            case_id=f"case_{task_id}_{test_order}",  # 添加case_id
            test_order=test_order,
            input_data=input_data,
            expected_output=expected_output,
            is_hidden=is_hidden
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def create_complete_test_scenario(
        db: Session,
        student_count: int = 1,
        practice_count: int = 1,
        task_count_per_practice: int = 1
    ) -> dict:
        """创建完整的测试场景"""
        # 创建教师
        teacher = TestDataGenerator.create_test_user(db, role="teacher")
        
        # 创建课堂
        classroom = TestDataGenerator.create_test_classroom(db, teacher.id)
        
        # 创建学生
        students = []
        for i in range(student_count):
            student = TestDataGenerator.create_test_user(
                db,
                username=f"test_student_{i+1}",
                role="student"
            )
            students.append(student)
            
            # 将学生添加到课堂
            classroom_student = models.ClassroomStudent(
                classroom_id=classroom.id,
                student_id=student.id
            )
            db.add(classroom_student)
        
        # 创建实践课程
        practices = []
        for i in range(practice_count):
            practice = TestDataGenerator.create_test_practice(
                db,
                title=f"测试实践课程_{i+1}",
                task_count=task_count_per_practice
            )
            practices.append(practice)
            
            # 将实践添加到课堂
            classroom_practice = models.ClassroomPractice(
                classroom_id=classroom.id,
                practice_id=practice.id,
                added_at=datetime.now()
            )
            db.add(classroom_practice)
            
            # 创建任务
            tasks = []
            for j in range(task_count_per_practice):
                task = TestDataGenerator.create_test_task(
                    db,
                    practice.id,
                    title=f"任务_{j+1}",
                    order=j+1
                )
                tasks.append(task)
                
                # 创建测试用例
                TestDataGenerator.create_test_task_test(
                    db,
                    task.id,
                    test_order=1,
                    input_data='{"name": "Python"}',
                    expected_output='{"output": "Python version 3.9"}',
                    is_hidden=False
                )
            
            practice.tasks = tasks
        
        db.commit()
        
        return {
            "teacher": teacher,
            "classroom": classroom,
            "students": students,
            "practices": practices
        }

    @staticmethod
    def get_test_code_samples() -> dict:
        """获取测试代码样本"""
        return {
            "correct_code": '''name = "Python"
version = 3.9
print(f"{name} version {version}")''',
            
            "syntax_error": "print('unclosed quote",
            
            "runtime_error": "x = 1 / 0",
            
            "wrong_output": '''name = "Python"
version = 3.8
print(f"{name} version {version}")''',
            
            "empty_code": "",
            
            "timeout_code": "while True: pass",
            
            "large_code": "print('Hello')" * 1000,
            
            "unicode_code": '''name = "Python中文"
version = 3.9
print(f"{name} version {version}")''',
            
            "special_chars": '''name = "Python"
version = 3.9
print(f"{name}\\tversion\\n{version}")'''
        }

