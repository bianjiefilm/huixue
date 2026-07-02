"""
P1 Seed Script: Fix BUG-M5-1, BUG-M6-1, BUG-M7-1
- Seeds Task records for practices bound via ClassroomPractice (fixes empty task list)
- Seeds ClassroomStudent enrollment for student_id=30 (fixes 403 on student exam list)
- Verifies exam data exists for classroom 100 (ensures exam workflow works)

Run inside Docker container:
  docker exec -it huixue-yuanban-backend-1 python /app/scripts/seed_p1_fixes.py
"""
import json
import os
import sys
from datetime import datetime, timedelta

backend_dir = "/app"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models
from app.models.models import DifficultyLevelEnum, DifficultyEnum

CLASSROOM_ID = 100
STUDENT_ID = 30  # student1 user


def seed_tasks_for_practices(db: Session):
    """BUG-M5-1: Seed Task records for practices bound via ClassroomPractice."""
    print("\n===== BUG-M5-1: Seeding Tasks for Practices =====")

    # Use ClassroomPractice (NOT ClassroomCourse — that was the original bug)
    cls_practices = db.query(models.ClassroomPractice).filter(
        models.ClassroomPractice.classroom_id == CLASSROOM_ID
    ).all()

    if not cls_practices:
        print(f"  No ClassroomPractice records for classroom {CLASSROOM_ID}.")
        return

    practice_count = 0
    task_count = 0

    for cp in cls_practices:
        practice_id = cp.practice_id
        existing_tasks = db.query(models.Task).filter(
            models.Task.practice_id == practice_id
        ).count()

        if existing_tasks > 0:
            print(f"  Practice {practice_id} already has {existing_tasks} tasks, skipping.")
            continue

        practice = db.query(models.Practice).filter(
            models.Practice.id == practice_id
        ).first()
        if not practice:
            print(f"  Practice {practice_id} not found in DB, skipping.")
            continue

        # Create 3 tasks per practice with meaningful content
        tasks_def = [
            {
                "title": f"{practice.title} - 关卡 1: 数据探索",
                "task_type": models.TaskTypeEnum.PRACTICE,
                "order": 1,
                "handbook": (
                    f"# {practice.title} - 数据探索\n\n"
                    "## 目标\n"
                    "了解数据集的基本结构和特征。\n\n"
                    "## 任务\n"
                    "1. 导入所需的Python库（pandas, numpy）\n"
                    "2. 读取数据文件并查看前10行\n"
                    "3. 使用 `df.info()` 和 `df.describe()` 了解数据概况\n"
                    "4. 检查是否存在缺失值\n"
                ),
                "answer": "import pandas as pd\nimport numpy as np\n\ndf = pd.read_csv('data.csv')\nprint(df.head(10))\nprint(df.info())\nprint(df.describe())\nprint(df.isnull().sum())",
                "env_type": "jupyter",
            },
            {
                "title": f"{practice.title} - 关卡 2: 数据清洗",
                "task_type": models.TaskTypeEnum.CODE,
                "order": 2,
                "handbook": (
                    f"# {practice.title} - 数据清洗\n\n"
                    "## 目标\n"
                    "对数据进行清洗和预处理。\n\n"
                    "## 任务\n"
                    "1. 处理缺失值（填充或删除）\n"
                    "2. 处理重复数据\n"
                    "3. 修正数据类型\n"
                    "4. 处理异常值\n"
                ),
                "answer": "df = df.dropna(subset=['key_column'])\ndf = df.fillna(df.mean(numeric_only=True))\ndf = df.drop_duplicates()\nprint(f'清洗后数据量: {len(df)}')",
                "env_type": "jupyter",
            },
            {
                "title": f"{practice.title} - 关卡 3: 数据可视化",
                "task_type": models.TaskTypeEnum.CODE,
                "order": 3,
                "handbook": (
                    f"# {practice.title} - 数据可视化\n\n"
                    "## 目标\n"
                    "使用可视化工具展示分析结果。\n\n"
                    "## 任务\n"
                    "1. 绘制数据分布直方图\n"
                    "2. 绘制关键特征的箱线图\n"
                    "3. 绘制相关性热力图\n"
                    "4. 总结分析发现\n"
                ),
                "answer": "import matplotlib.pyplot as plt\nimport seaborn as sns\n\nplt.figure(figsize=(10,6))\nsns.heatmap(df.corr(), annot=True)\nplt.title('Correlation Heatmap')\nplt.show()",
                "env_type": "jupyter",
            },
        ]

        for td in tasks_def:
            task = models.Task(
                practice_id=practice_id,
                title=td["title"],
                task_type=td["task_type"],
                order_in_practice=td["order"],
                coin=10 * td["order"],
                env_type=td["env_type"],
                difficulty="beginner",
                skills=json.dumps(["python", "pandas", "data-analysis"]),
                handbook_markdown=td["handbook"],
                answer_content_markdown=td["answer"],
                evaluation_script_path="/tests/test_script.py",
                evaluation_command="pytest",
                enable_page_preview=True,
            )
            db.add(task)
            task_count += 1

        practice_count += 1
        print(f"  Created 3 tasks for Practice {practice_id} ({practice.title})")

    db.commit()
    print(f"  Total: {task_count} tasks created for {practice_count} practices.")


def seed_student_enrollment(db: Session):
    """BUG-M7-1: Ensure student_id=30 is enrolled in classroom 100."""
    print("\n===== BUG-M7-1: Seeding ClassroomStudent enrollment =====")

    existing = db.query(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == CLASSROOM_ID,
        models.ClassroomStudent.student_id == STUDENT_ID,
    ).first()

    if existing:
        print(f"  Student {STUDENT_ID} already enrolled in classroom {CLASSROOM_ID}, skipping.")
        return

    enrollment = models.ClassroomStudent(
        classroom_id=CLASSROOM_ID,
        student_id=STUDENT_ID,
    )
    db.add(enrollment)
    db.commit()
    print(f"  Enrolled student {STUDENT_ID} in classroom {CLASSROOM_ID}.")


def verify_exam_data(db: Session):
    """BUG-M6-1: Verify exam data exists and is ONGOING for classroom 100."""
    print("\n===== BUG-M6-1: Verifying exam data for classroom 100 =====")

    exams = db.query(models.ClassroomExam).filter(
        models.ClassroomExam.classroom_id == CLASSROOM_ID
    ).all()

    if not exams:
        print("  No exams found for classroom 100. Creating one...")
        # Reuse the global paper from seed_practices_and_exams_all_18.py
        global_paper = db.query(models.TestPaper).filter(
            models.TestPaper.title == "E2E 平台功能综合审查在线测试试卷"
        ).first()

        if not global_paper:
            print("  Global test paper not found. Run seed_practices_and_exams_all_18.py first.")
            return

        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        now = datetime.now()

        exam = models.ClassroomExam(
            classroom_id=CLASSROOM_ID,
            test_paper_id=global_paper.id,
            title=f"【班级 {CLASSROOM_ID}】期中综合在线审查考试任务",
            exam_start_time=now - timedelta(days=1),
            exam_end_time=now + timedelta(days=30),
            duration_minutes=60,
            pass_mark=60.0,
            status=models.ExamStatusEnum.ONGOING,
            created_by_teacher_id=admin_user.id if admin_user else 1,
        )
        db.add(exam)
        db.commit()
        print(f"  Created exam for classroom {CLASSROOM_ID}.")
    else:
        for ex in exams:
            print(f"  Exam ID={ex.id}, title={ex.title}, status={ex.status}")
            # Ensure it's ONGOING and not expired
            if ex.exam_end_time and ex.exam_end_time < datetime.now():
                ex.exam_end_time = datetime.now() + timedelta(days=30)
                print(f"    Extended exam end time to {ex.exam_end_time}")
            if ex.status != models.ExamStatusEnum.ONGOING:
                ex.status = models.ExamStatusEnum.ONGOING
                print(f"    Updated status to ONGOING")
        db.commit()
        print(f"  Verified {len(exams)} exam(s) for classroom {CLASSROOM_ID}.")


def main():
    print("=" * 60)
    print("P1 Seed Script: BUG-M5-1 + BUG-M6-1 + BUG-M7-1")
    print("=" * 60)

    db = SessionLocal()
    try:
        seed_tasks_for_practices(db)
        seed_student_enrollment(db)
        verify_exam_data(db)
        print("\nAll P1 seeds completed successfully!")
    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
