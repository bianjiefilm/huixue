#!/usr/bin/env python3
"""
初始化考试阅卷功能的测试数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import get_db, engine, Base
from sqlalchemy import text
from app.models import models
from datetime import datetime, timezone, timedelta
import json

def init_exam_test_data():
    """初始化考试测试数据"""
    print("初始化考试测试数据...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        # 获取教师和课堂信息
        teacher = db.query(models.User).filter(models.User.username == "teacher_test").first()
        classroom = db.query(models.Classroom).filter(models.Classroom.name == "测试课堂").first()
        
        if not teacher or not classroom:
            print("❌ 请先运行基础数据初始化脚本 (python init_test_data.py)")
            return
        
        print("1. 创建试卷...")
        # 检查是否已存在
        existing_paper = db.query(models.TestPaper).filter(
            models.TestPaper.title == "Python基础测试试卷"
        ).first()
        
        if not existing_paper:
            test_paper = models.TestPaper(
                title="Python基础测试试卷",
                description="Python基础知识测试",
                creator_id=teacher.id,
                difficulty=models.DifficultyEnum.INTERMEDIATE,
                total_score=100,
                estimated_duration_minutes=90,
                direction="计算机科学",
                category="编程语言",
                is_shared=True
            )
            db.add(test_paper)
            db.commit()
            db.refresh(test_paper)
            print(f"  ✓ 创建试卷，ID: {test_paper.id}")
        else:
            test_paper = existing_paper
            print(f"  ✓ 使用现有试卷，ID: {test_paper.id}")
        
        print("2. 创建题目...")
        
        questions_data = [
            {
                "content": "Python中哪个关键字用于定义函数？",
                "question_type": "SINGLE_CHOICE",
                "options": [
                    {"key": "A", "content": "function"},
                    {"key": "B", "content": "def"},
                    {"key": "C", "content": "define"},
                    {"key": "D", "content": "func"}
                ],
                "correct_answers": ["B"],
                "explanation": "Python使用def关键字定义函数",
                "score": 10
            },
            {
                "content": "以下哪些是Python的数据类型？（多选）",
                "question_type": "MULTIPLE_CHOICE",
                "options": [
                    {"key": "A", "content": "int"},
                    {"key": "B", "content": "string"},
                    {"key": "C", "content": "list"},
                    {"key": "D", "content": "dict"}
                ],
                "correct_answers": ["A", "C", "D"],
                "explanation": "Python中string应该是str，其他都是正确的数据类型",
                "score": 15
            },
            {
                "content": "请简述Python中列表和元组的区别。",
                "question_type": "SHORT_ANSWER",
                "options": [],
                "correct_answers": ["列表是可变的，元组是不可变的"],
                "explanation": "列表可以修改元素，元组创建后不能修改",
                "score": 25
            }
        ]
        
        question_ids = []
        for i, q_data in enumerate(questions_data):
            existing_question = db.query(models.Question).filter(
                models.Question.content == q_data["content"]
            ).first()
            
            if not existing_question:
                question = models.Question(
                    content=q_data["content"],
                    question_type=getattr(models.QuestionTypeEnum, q_data["question_type"]),
                    options=json.dumps(q_data["options"]) if q_data["options"] else None,
                    correct_answers=json.dumps(q_data["correct_answers"]),
                    explanation=q_data["explanation"],
                    creator_id=teacher.id,
                    difficulty=models.DifficultyEnum.INTERMEDIATE
                )
                db.add(question)
                db.commit()
                db.refresh(question)
                question_id = question.id
                print(f"  ✓ 创建题目 {i+1}，ID: {question_id}")
            else:
                question_id = existing_question.id
                print(f"  ✓ 使用现有题目 {i+1}，ID: {question_id}")
            
            question_ids.append((question_id, q_data["score"]))
                 
        print("3. 关联题目到试卷...")
        
        for i, (question_id, score) in enumerate(question_ids):
            existing_relation = db.query(models.TestPaperQuestion).filter(
                models.TestPaperQuestion.test_paper_id == test_paper.id,
                models.TestPaperQuestion.question_id == question_id
            ).first()
            
            if not existing_relation:
                paper_question = models.TestPaperQuestion(
                    test_paper_id=test_paper.id,
                    question_id=question_id,
                    score_for_question=score,
                    order_in_paper=i + 1
                )
                db.add(paper_question)
                print(f"  ✓ 关联题目 {question_id} 到试卷")
        
        print("4. 创建课堂考试...")
        # 检查是否已存在
        existing_exam = db.query(models.ClassroomExam).filter(
            models.ClassroomExam.classroom_id == classroom.id,
            models.ClassroomExam.title == "Python基础测试"
        ).first()
        
        if not existing_exam:
            classroom_exam = models.ClassroomExam(
                classroom_id=classroom.id,
                test_paper_id=test_paper.id,
                title="Python基础测试",
                exam_start_time=datetime.now(timezone.utc) + timedelta(hours=1),
                exam_end_time=datetime.now(timezone.utc) + timedelta(hours=3),
                duration_minutes=90,
                pass_mark=60,
                shuffle_questions=False,
                shuffle_options=False,
                status=models.ExamStatusEnum.UNPUBLISHED,
                created_by_teacher_id=teacher.id
            )
            db.add(classroom_exam)
            db.commit()
            db.refresh(classroom_exam)
            print(f"  ✓ 创建考试，ID: {classroom_exam.id}")
        else:
            classroom_exam = existing_exam
            print(f"  ✓ 使用现有考试，ID: {classroom_exam.id}")
        
        print("5. 创建学生答题记录...")
        # 获取课堂中的学生
        students = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom.id
        ).all()
        
        attempt_count = 0
        for cs in students:
            existing_attempt = db.query(models.StudentExamAttempt).filter(
                models.StudentExamAttempt.classroom_exam_id == classroom_exam.id,
                models.StudentExamAttempt.student_id == cs.student_id
            ).first()
            
            if not existing_attempt:
                attempt = models.StudentExamAttempt(
                    classroom_exam_id=classroom_exam.id,
                    student_id=cs.student_id,
                    attempt_start_time=None,  # 未开始答题
                    attempt_submission_time=None,
                    actual_duration_seconds=None,
                    total_score_achieved=None,
                    is_graded=False
                )
                db.add(attempt)
                attempt_count += 1
        
        db.commit()
        print("✅ 考试测试数据初始化完成！")
        
        print(f"\n📋 测试信息:")
        print(f"  试卷ID: {test_paper.id}")
        print(f"  考试ID: {classroom_exam.id}")
        print(f"  课堂ID: {classroom.id}")
        print(f"  教师ID: {teacher.id}")
        print(f"  题目数量: {len(question_ids)}")
        print(f"  学生答题数量: {attempt_count}")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_exam_test_data() 