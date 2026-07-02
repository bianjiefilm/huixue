import json
import os
import sys
from datetime import datetime, timedelta

# Avoid path issues by running from app root
if 'PYTHONPATH' in os.environ:
    del os.environ['PYTHONPATH']

backend_dir = "/app"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models
from app.models.models import DifficultyLevelEnum, DifficultyEnum

def seed_practices_and_exams():
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            print("❌ Error: Admin user not found.")
            return

        target_courses = list(range(100, 118))
        print(f"-> Preparing to inject Practice & Exam seeds for {len(target_courses)} Classrooms (IDs: 100-117)...")
        
        now = datetime.now()
        
        # 1. Idempotent fetch-or-create for global entities
        print("--> Generating / Fetching generic Practice template...")
        global_practice = db.query(models.Practice).filter(models.Practice.title == "E2E 自动化测试综合数据分析实践").first()
        if not global_practice:
            global_practice = models.Practice(
                title="E2E 自动化测试综合数据分析实践",
                description="本实践用于验证教学平台环境的端到端加载挂载和列表展示有效性。",
                difficulty=DifficultyLevelEnum.intermediate,
                practice_type="jupyter",
                direction="人工智能",
                category="数据分析",
                is_published=True,
                visibility="PUBLIC",
                creator_id=admin_user.id
            )
            db.add(global_practice)
            db.commit()
            db.refresh(global_practice)

        print("--> Generating / Fetching generic Test Paper & Question template...")
        global_question = db.query(models.Question).filter(models.Question.id == "q_e2e_100").first()
        if not global_question:
            global_question = models.Question(
                id="q_e2e_100",
                content="以下哪项是正确的数据清洗实践流程？(E2E 测试用例)",
                question_type="SINGLE_CHOICE",
                options=json.dumps([
                    {"key": "A", "content": "直接丢弃所有缺失值，不分析原因"},
                    {"key": "B", "content": "保留所有异常值原样进入模型"},
                    {"key": "C", "content": "进行异常值探测并执行均值/中位数填充或适当裁剪"},
                    {"key": "D", "content": "完全伪造缺失位置的数据"}
                ], ensure_ascii=False),
                correct_answers=json.dumps(["C"]),
                explanation="合理清洗数据不仅提升模型表现，还能避免分布偏移。",
                difficulty=DifficultyEnum.INTERMEDIATE,
                creator_id=admin_user.id,
                is_shared=True
            )
            db.add(global_question)
            db.commit()
            db.refresh(global_question)

        global_paper = db.query(models.TestPaper).filter(models.TestPaper.title == "E2E 平台功能综合审查在线测试试卷").first()
        if not global_paper:
            global_paper = models.TestPaper(
                title="E2E 平台功能综合审查在线测试试卷",
                description="该试卷全自动生成以供在前端列表内完成渲染提取。",
                creator_id=admin_user.id,
                difficulty=DifficultyEnum.INTERMEDIATE,
                total_score=100.0,
                estimated_duration_minutes=60,
                is_shared=True
            )
            db.add(global_paper)
            db.commit()
            db.refresh(global_paper)

            paper_question = models.TestPaperQuestion(
                test_paper_id=global_paper.id,
                question_id=global_question.id,
                score_for_question=100.0,
                order_in_paper=1,
                section_title="单项选择题"
            )
            db.add(paper_question)
            db.commit()

        # 2. Iterate through courses and bind Classroom entities
        for course_id in target_courses:
            # Bind Practice
            class_practice = db.query(models.ClassroomPractice).filter(
                models.ClassroomPractice.classroom_id == course_id,
                models.ClassroomPractice.practice_id == global_practice.id
            ).first()
            if not class_practice:
                class_practice = models.ClassroomPractice(
                    classroom_id=course_id,
                    practice_id=global_practice.id
                )
                db.add(class_practice)
            
            # Bind Exam
            class_exam = db.query(models.ClassroomExam).filter(
                models.ClassroomExam.classroom_id == course_id,
                models.ClassroomExam.test_paper_id == global_paper.id
            ).first()
            if not class_exam:
                class_exam = models.ClassroomExam(
                    classroom_id=course_id,
                    test_paper_id=global_paper.id,
                    title=f"【班级 {course_id}】期中综合在线审查考试任务",
                    exam_start_time=now - timedelta(days=1),
                    exam_end_time=now + timedelta(days=7),
                    duration_minutes=60,
                    pass_mark=60.0,
                    status=models.ExamStatusEnum.ONGOING,
                    created_by_teacher_id=admin_user.id
                )
                db.add(class_exam)
            
            print(f"  ✅ 课堂 {course_id} - [实践] & [考试] 分发完成")

        db.commit()
        print("\n🎉 全部 18 间教室的 E2E 实训、实践、考试前置验证数据挂载成功！")

    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_practices_and_exams()
