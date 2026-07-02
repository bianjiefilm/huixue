"""
创建测试数据脚本
用于在数据库中创建考试相关的测试数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import models
from datetime import datetime, timedelta
import random

def create_test_papers(db: Session, teacher_id: int = 1):
    """创建测试试卷"""
    print("创建测试试卷...")
    
    papers = [
        {
            "title": "Python基础测试卷",
            "description": "测试Python基础知识",
            "total_score": 100,
            "estimated_duration_minutes": 90,
            "creator_id": teacher_id,
            "difficulty": models.DifficultyEnum.INTERMEDIATE
        },
        {
            "title": "数据结构期中考试",
            "description": "数据结构与算法期中测试",
            "total_score": 100,
            "estimated_duration_minutes": 120,
            "creator_id": teacher_id,
            "difficulty": models.DifficultyEnum.INTERMEDIATE
        },
        {
            "title": "Web开发实践测试",
            "description": "HTML/CSS/JavaScript综合测试",
            "total_score": 100,
            "estimated_duration_minutes": 60,
            "creator_id": teacher_id,
            "difficulty": models.DifficultyEnum.BASIC
        }
    ]
    
    created_papers = []
    for paper_data in papers:
        paper = models.TestPaper(**paper_data)
        db.add(paper)
        db.commit()
        db.refresh(paper)
        created_papers.append(paper)
        print(f"  ✅ 创建试卷: {paper.title} (ID: {paper.id})")
        
        # 为每个试卷创建题目
        create_questions_for_paper(db, paper.id)
    
    return created_papers


def create_questions_for_paper(db: Session, paper_id: int):
    """为试卷创建题目"""
    # 首先创建题库中的题目
    questions_data = [
        # 单选题
        {
            "type": models.QuestionTypeEnum.SINGLE_CHOICE,
            "content": "Python中用于定义函数的关键字是？",
            "correct_answer": "B",
            "score": 10,
            "difficulty": models.DifficultyEnum.BASIC,
            "creator_id": 1,
            "options": [
                {"option_label": "A", "option_content": "function", "is_correct": False},
                {"option_label": "B", "option_content": "def", "is_correct": True},
                {"option_label": "C", "option_content": "func", "is_correct": False},
                {"option_label": "D", "option_content": "define", "is_correct": False}
            ]
        },
        # 多选题
        {
            "paper_id": paper_id,
            "question_type": "multiple",
            "question_content": "以下哪些是Python的内置数据类型？",
            "question_score": 15,
            "question_answer": "A,C,D",
            "options": [
                {"option_label": "A", "option_content": "list", "is_correct": True},
                {"option_label": "B", "option_content": "array", "is_correct": False},
                {"option_label": "C", "option_content": "dict", "is_correct": True},
                {"option_label": "D", "option_content": "tuple", "is_correct": True}
            ]
        },
        # 判断题
        {
            "paper_id": paper_id,
            "question_type": "judge",
            "question_content": "Python是一种编译型语言。",
            "question_score": 10,
            "question_answer": "错",
            "options": [
                {"option_label": "对", "option_content": "对", "is_correct": False},
                {"option_label": "错", "option_content": "错", "is_correct": True}
            ]
        },
        # 简答题
        {
            "paper_id": paper_id,
            "question_type": "essay",
            "question_content": "请简述Python中列表(list)和元组(tuple)的主要区别。",
            "question_score": 25,
            "question_answer": "主要区别：1. 可变性：列表是可变的，可以修改、添加、删除元素；元组是不可变的，创建后不能修改。2. 性能：元组比列表更快，占用内存更少。3. 用途：列表用于需要修改的数据；元组用于不应该改变的数据。"
        },
        {
            "paper_id": paper_id,
            "question_type": "essay",
            "question_content": "编写一个Python函数，实现计算列表中所有数字的平均值。",
            "question_score": 40,
            "question_answer": "def average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"
        }
    ]
    
    for i, q_data in enumerate(questions, 1):
        options = q_data.pop("options", [])
        question = models.TestQuestion(**q_data, question_order=i)
        db.add(question)
        db.commit()
        db.refresh(question)
        
        # 创建选项
        for opt in options:
            option = models.QuestionOption(
                question_id=question.id,
                **opt
            )
            db.add(option)
        db.commit()


def create_classroom_exams(db: Session, classroom_id: int, teacher_id: int, papers):
    """创建课堂考试"""
    print("\n创建课堂考试...")
    
    exams = []
    for i, paper in enumerate(papers):
        exam_data = {
            "classroom_id": classroom_id,
            "title": f"{paper.paper_name} - 考试",
            "exam_type": "online",
            "test_paper_id": paper.id,
            "created_by_teacher_id": teacher_id
        }
        
        exam = models.ClassroomExam(**exam_data)
        db.add(exam)
        db.commit()
        db.refresh(exam)
        exams.append(exam)
        print(f"  ✅ 创建考试: {exam.title} (ID: {exam.id})")
        
        # 发布第一个考试
        if i == 0:
            publish_exam(db, exam, teacher_id)
    
    return exams


def publish_exam(db: Session, exam, teacher_id: int):
    """发布考试"""
    now = datetime.now()
    exam.exam_start_time = now + timedelta(minutes=10)  # 10分钟后开始
    exam.exam_end_time = now + timedelta(hours=2)  # 持续2小时
    exam.duration_minutes = 90
    exam.pass_mark = 60
    exam.status = models.ExamStatus.PUBLISHED
    exam.published_by_teacher_id = teacher_id
    exam.published_at = now
    
    db.commit()
    print(f"    ➡️ 考试已发布: {exam.title}")


def create_student_attempts(db: Session, exam_id: int, classroom_id: int):
    """创建学生答题记录"""
    print("\n创建学生答题记录...")
    
    # 获取课堂中的学生
    students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).all()
    
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    paper = db.query(models.TestPaper).filter(
        models.TestPaper.id == exam.test_paper_id
    ).first()
    
    questions = db.query(models.TestQuestion).filter(
        models.TestQuestion.paper_id == paper.id
    ).all()
    
    for student in students[:3]:  # 只为前3个学生创建答题记录
        # 创建考试尝试
        attempt = models.ExamAttempt(
            exam_id=exam_id,
            student_id=student.student_id,
            attempt_start_time=datetime.now() - timedelta(hours=1),
            attempt_end_time=datetime.now() - timedelta(minutes=30),
            status=models.AttemptStatus.SUBMITTED
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        
        total_score = 0
        
        # 为每个题目创建答案
        for question in questions:
            if question.question_type == "single":
                # 单选题 - 随机选择
                options = db.query(models.QuestionOption).filter(
                    models.QuestionOption.question_id == question.id
                ).all()
                selected = random.choice(options)
                answer_text = selected.option_id
                is_correct = selected.is_correct
                score = question.question_score if is_correct else 0
                
            elif question.question_type == "multiple":
                # 多选题 - 随机选择多个
                options = db.query(models.QuestionOption).filter(
                    models.QuestionOption.question_id == question.id
                ).all()
                selected_count = random.randint(1, len(options))
                selected_options = random.sample(options, selected_count)
                answer_text = ",".join([opt.option_id for opt in selected_options])
                # 简化判断：如果选中了所有正确选项，得满分
                correct_options = [opt for opt in options if opt.is_correct]
                is_correct = set(selected_options) == set(correct_options)
                score = question.question_score if is_correct else 0
                
            elif question.question_type == "judge":
                # 判断题
                answer_text = random.choice(["对", "错"])
                is_correct = answer_text == question.question_answer
                score = question.question_score if is_correct else 0
                
            else:  # essay
                # 简答题 - 需要教师批阅
                answer_text = f"这是学生{student.student_id}对问题的回答..."
                is_correct = None
                score = None
            
            answer = models.StudentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                answer_text=answer_text,
                is_correct=is_correct,
                score_achieved=score,
                answered_at=datetime.now() - timedelta(minutes=45)
            )
            db.add(answer)
            
            if score is not None:
                total_score += score
        
        # 更新尝试的总分
        attempt.total_score_achieved = total_score
        db.commit()
        
        print(f"  ✅ 学生{student.student_id}已提交答卷 (得分: {total_score})")


def main():
    """主函数"""
    print("="*50)
    print("开始创建测试数据")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 假设已有的数据
        teacher_id = 1  # 教师ID
        classroom_id = 1  # 课堂ID
        
        # 1. 创建试卷和题目
        papers = create_test_papers(db, teacher_id)
        
        # 2. 创建考试
        exams = create_classroom_exams(db, classroom_id, teacher_id, papers)
        
        # 3. 为第一个考试创建学生答题记录
        if exams:
            create_student_attempts(db, exams[0].id, classroom_id)
        
        print("\n✅ 测试数据创建完成！")
        print("\n可以使用以下信息进行测试：")
        print(f"  - 教师ID: {teacher_id}")
        print(f"  - 课堂ID: {classroom_id}")
        print(f"  - 考试ID: {exams[0].id if exams else 'N/A'}")
        
    except Exception as e:
        print(f"\n❌ 创建测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()