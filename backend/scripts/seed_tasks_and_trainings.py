import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_tasks_and_datasets():
    db = next(get_db())
    CLASSROOM_ID = 100
    TEACHER_ID = 3  # teacher1
    
    try:
        # 1. Fetch all Practice IDs for Classroom 100
        cls_practices = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.classroom_id == CLASSROOM_ID,
            models.ClassroomCourse.practice_id.isnot(None)
        ).all()
        
        practice_count = 0
        task_count = 0
        
        print("======== 正在为实战课程 (Practices) 补充关卡 (Tasks) ========")
        for cp in cls_practices:
            practice_id = cp.practice_id
            # 检查是否已有 Task
            existing_tasks = db.query(models.Task).filter(models.Task.practice_id == practice_id).count()
            if existing_tasks == 0:
                print(f"为 Practice ID {practice_id} 生成关联的任务...")
                practice = db.query(models.Practice).filter(models.Practice.id == practice_id).first()
                if not practice:
                    continue
                
                # 生成 3 个任务
                for i in range(1, 4):
                    task = models.Task(
                        practice_id=practice_id,
                        title=f"{practice.title} - 关卡 {i}",
                        task_type=models.TaskTypeEnum.CODE if i % 2 == 0 else models.TaskTypeEnum.PRACTICE,
                        order_in_practice=i,
                        coin=10 * i,
                        env_type="jupyter" if i % 2 == 0 else "linux",
                        difficulty="beginner",
                        skills=json.dumps([f"skill_{i}"]),
                        handbook_markdown=f"# {practice.title} 关卡 {i} 实验手册\n\n欢迎来到本实验。请按照提示完成代码编写。",
                        answer_content_markdown="print('Hello World')",
                        evaluation_script_path="/tests/test_script.py",
                        evaluation_command="pytest",
                        enable_page_preview=True
                    )
                    db.add(task)
                    task_count += 1
                practice_count += 1
            else:
                print(f"Practice ID {practice_id} 已有 {existing_tasks} 个任务，跳过。")
                
        # 2. Fetch all Training IDs for Classroom 100
        cls_trainings = db.query(models.ClassroomTraining).filter(
            models.ClassroomTraining.classroom_id == CLASSROOM_ID
        ).all()
        
        training_count = 0
        dataset_count = 0
        
        print("\n======== 正在为项目实训 (Trainings) 补充数据集 (Datasets) ========")
        for ct in cls_trainings:
            training_id = ct.training_id
            # 检查是否已有 Dataset
            existing_datasets = db.query(models.TrainingDataset).filter(
                models.TrainingDataset.training_id == training_id
            ).count()
            if existing_datasets == 0:
                print(f"为 Training ID {training_id} 生成关联的数据集...")
                training = db.query(models.Training).filter(models.Training.id == training_id).first()
                if not training:
                    continue
                
                for i in range(1, 3):
                    dataset = models.TrainingDataset(
                        training_id=training_id,
                        name=f"数据集 {i} - {training.title}",
                        file_url=f"/static/datasets/{training_id}_data_{i}.csv",
                        file_type="csv",
                        file_size=1024 * i * 50, # 50KB, 100KB
                        description=f"用于 {training.title} 的分析数据集 {i}",
                        uploader_id=TEACHER_ID
                    )
                    db.add(dataset)
                    dataset_count += 1
                training_count += 1
            else:
                print(f"Training ID {training_id} 已有 {existing_datasets} 个数据集，跳过。")
                
        db.commit()
        print(f"\n======== 补充完成 ========")
        print(f"成功为 {practice_count} 个课程补充了 {task_count} 个关卡 (Tasks)。")
        print(f"成功为 {training_count} 个实训补充了 {dataset_count} 个数据集 (Datasets)。")

    except Exception as e:
        db.rollback()
        print(f"出错: {e}")

if __name__ == "__main__":
    seed_tasks_and_datasets()
