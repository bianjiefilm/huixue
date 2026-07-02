"""
创建考试测试数据的简化脚本
直接使用现有的数据结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import models
from datetime import datetime, timedelta
import json

def create_simple_test_paper(db: Session, teacher_id: int = 1):
    """创建一个简单的测试试卷"""
    print("创建测试试卷...")
    
    # 创建试卷
    paper = models.TestPaper(
        title="Python编程基础测试",
        description="测试Python基础知识掌握情况",
        total_score=100,
        estimated_duration_minutes=90,
        creator_id=teacher_id,
        difficulty=models.DifficultyEnum.INTERMEDIATE,
        is_shared=False
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    print(f"✅ 创建试卷: {paper.title} (ID: {paper.id})")
    
    # 创建题目并关联到试卷
    questions_data = [
        {
            "content": "Python中用于定义函数的关键字是？",
            "question_type": models.QuestionTypeEnum.SINGLE_CHOICE,
            "options": json.dumps([
                {"label": "A", "content": "function"},
                {"label": "B", "content": "def"},
                {"label": "C", "content": "func"},
                {"label": "D", "content": "define"}
            ]),
            "correct_answers": json.dumps(["B"]),
            "score": 10
        },
        {
            "content": "以下哪些是Python的内置数据类型？",
            "question_type": models.QuestionTypeEnum.MULTIPLE_CHOICE,
            "options": json.dumps([
                {"label": "A", "content": "list"},
                {"label": "B", "content": "array"},
                {"label": "C", "content": "dict"},
                {"label": "D", "content": "tuple"}
            ]),
            "correct_answers": json.dumps(["A", "C", "D"]),
            "score": 15
        },
        {
            "content": "Python是一种编译型语言。",
            "question_type": models.QuestionTypeEnum.TRUE_FALSE,
            "options": json.dumps([
                {"label": "对", "content": "对"},
                {"label": "错", "content": "错"}
            ]),
            "correct_answers": json.dumps(["错"]),
            "score": 10
        },
        {
            "content": "请简述Python中列表(list)和元组(tuple)的主要区别。",
            "question_type": models.QuestionTypeEnum.SHORT_ANSWER,
            "correct_answers": json.dumps(["列表是可变的，元组是不可变的"]),
            "score": 25
        },
        {
            "content": "编写一个Python函数，实现计算列表中所有数字的平均值。",
            "question_type": models.QuestionTypeEnum.SHORT_ANSWER,
            "correct_answers": json.dumps(["def average(numbers): return sum(numbers) / len(numbers)"]),
            "score": 40
        }
    ]
    
    for i, q_data in enumerate(questions_data, 1):
        score = q_data.pop("score")
        
        # 创建题目
        question = models.Question(
            **q_data,
            difficulty=models.DifficultyEnum.INTERMEDIATE,
            creator_id=teacher_id
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        
        # 关联题目到试卷
        paper_question = models.TestPaperQuestion(
            test_paper_id=paper.id,
            question_id=question.id,
            score_for_question=score,
            order_in_paper=i
        )
        db.add(paper_question)
    
    db.commit()
    return paper


def create_classroom_exam(db: Session, classroom_id: int, paper_id: int, teacher_id: int):
    """创建课堂考试"""
    print("\n创建课堂考试...")
    
    exam = models.ClassroomExam(
        classroom_id=classroom_id,
        title="Python基础期中考试",
        exam_type=models.ExamTypeEnum.ONLINE,
        test_paper_id=paper_id,
        created_by_teacher_id=teacher_id,
        status=models.ExamStatus.DRAFT
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    print(f"✅ 创建考试: {exam.title} (ID: {exam.id})")
    
    # 发布考试
    now = datetime.now()
    exam.exam_start_time = now + timedelta(minutes=5)
    exam.exam_end_time = now + timedelta(hours=2)
    exam.duration_minutes = 90
    exam.pass_mark = 60
    exam.status = models.ExamStatus.PUBLISHED
    exam.published_by_teacher_id = teacher_id
    exam.published_at = now
    
    db.commit()
    print(f"✅ 考试已发布，将于5分钟后开始")
    
    return exam


def create_student_attempts(db: Session, exam_id: int, classroom_id: int):
    """创建学生答题记录"""
    print("\n创建学生答题记录...")
    
    # 获取课堂中的学生
    students = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == classroom_id
    ).limit(3).all()  # 只为前3个学生创建
    
    if not students:
        print("❌ 未找到学生")
        return
    
    exam = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.id == exam_id
    ).first()
    
    # 获取试卷的题目
    paper_questions = db.query(models.TestPaperQuestion).filter(
        models.TestPaperQuestion.test_paper_id == exam.test_paper_id
    ).order_by(models.TestPaperQuestion.order_in_paper).all()
    
    for student in students:
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
        for pq in paper_questions:
            question = db.query(models.Question).filter(
                models.Question.id == pq.question_id
            ).first()
            
            if question.question_type == models.QuestionTypeEnum.SINGLE_CHOICE:
                answer_text = "B"  # 假设选择B
                is_correct = "B" in json.loads(question.correct_answers)
                score = pq.score_for_question if is_correct else 0
                
            elif question.question_type == models.QuestionTypeEnum.MULTIPLE_CHOICE:
                answer_text = json.dumps(["A", "C"])  # 假设选择A和C
                correct = set(json.loads(question.correct_answers))
                selected = set(["A", "C"])
                is_correct = selected == correct
                score = pq.score_for_question if is_correct else 0
                
            elif question.question_type == models.QuestionTypeEnum.TRUE_FALSE:
                answer_text = "错"
                is_correct = answer_text in json.loads(question.correct_answers)
                score = pq.score_for_question if is_correct else 0
                
            else:  # SHORT_ANSWER
                answer_text = f"这是学生{student.student_id}对问题的回答..."
                is_correct = None
                score = None  # 需要教师批阅
            
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
        
        print(f"✅ 学生{student.student_id}已提交答卷 (客观题得分: {total_score})")


def main():
    """主函数"""
    print("="*50)
    print("开始创建考试测试数据")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 使用默认值
        teacher_id = 1
        classroom_id = 1
        
        # 1. 创建试卷
        paper = create_simple_test_paper(db, teacher_id)
        
        # 2. 创建考试
        exam = create_classroom_exam(db, classroom_id, paper.id, teacher_id)
        
        # 3. 创建学生答题记录
        create_student_attempts(db, exam.id, classroom_id)
        
        print("\n✅ 测试数据创建完成！")
        print("\n测试信息：")
        print(f"  - 试卷ID: {paper.id}")
        print(f"  - 考试ID: {exam.id}")
        print(f"  - 课堂ID: {classroom_id}")
        print(f"  - 教师ID: {teacher_id}")
        print("\n现在可以使用教师账号登录系统进行测试了！")
        
    except Exception as e:
        print(f"\n❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()