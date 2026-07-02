import os
import sys

# Remove any existing PYTHONPATH to avoid conflicts, then set the correct one
if 'PYTHONPATH' in os.environ:
    del os.environ['PYTHONPATH']

# backend_dir = "/Users/jimfu/Work/huixue/backend"
backend_dir = "/app"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models

def seed_18_courses():
    db = SessionLocal()
    try:
        # Get admin user
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            print("❌ 错误: 找不到 admin 用户，请检查数据库")
            return

        target_courses = list(range(100, 118)) # 100 to 117 (inclusive) 18 total courses
        print(f"-> 准备为 {len(target_courses)} 门课程 (ID: 100-117) 植入 100% 覆盖率的视觉校验用例...")
        
        inserted_count = 0
        for course_id in target_courses:
            from datetime import datetime, timedelta
            # Check if classroom exists
            classroom = db.query(models.Classroom).filter(models.Classroom.id == course_id).first()
            if not classroom:
                print(f"  ⚠️ 创建测试课程 {course_id}...")
                now = datetime.now()
                classroom = models.Classroom(
                    id=course_id,
                    name=f"E2E Test Course {course_id}",
                    teacher_id=admin_user.id,
                    start_date=now - timedelta(days=30),
                    end_date=now + timedelta(days=150),
                    academic_year="2024-2025",
                    semester="春季",
                    status="ONGOING",
                    student_count=1
                )
                db.add(classroom)
                db.commit()
                
                # Assign student1 (id=30)
                student_mapper = models.ClassroomStudent(
                    classroom_id=course_id,
                    student_id=30
                )
                db.add(student_mapper)
                db.commit()

            # Check if training exists for this classroom
            from app.core.enums import TrainingTypeEnum, TrainingPublishStatusEnum, TrainingVisibilityEnum, DifficultyLevelEnum
            training = db.query(models.Training).filter(models.Training.id == course_id).first()
            if not training:
                print(f"  ⚠️ 创建BI测试实训 {course_id}...")
                training = models.Training(
                    id=course_id,
                    title=f"E2E BI 测试实训 {course_id}",
                    training_type=TrainingTypeEnum.DRAG_DROP,
                    intro=f"自动化生成的 UI 测试数据 {course_id}",
                    difficulty=DifficultyLevelEnum.beginner,
                    course_hours=1,
                    publish_status=TrainingPublishStatusEnum.PUBLISHED,
                    visibility=TrainingVisibilityEnum.PUBLIC,
                    is_published=True,
                    creator_id=admin_user.id
                )
                db.add(training)
                db.commit()

            # Link classroom and training
            classroom_training = db.query(models.ClassroomTraining).filter(
                models.ClassroomTraining.classroom_id == course_id,
                models.ClassroomTraining.training_id == course_id
            ).first()
            if not classroom_training:
                classroom_training = models.ClassroomTraining(
                    classroom_id=course_id,
                    training_id=course_id,
                    order_index=1
                )
                db.add(classroom_training)
                db.commit()

            # Add mock training dataset to bypass Vue frontend "empty" logic
            dataset = db.query(models.TrainingDataset).filter(models.TrainingDataset.training_id == course_id).first()
            if not dataset:
                dataset = models.TrainingDataset(
                    training_id=course_id,
                    name=f"Dummy Dataset {course_id}",
                    file_url=f"/static/resources/fake_dataset_{course_id}.csv",
                    relative_path=f"fake_dataset_{course_id}.csv",
                    file_type="csv",
                    file_size=1024,
                    uploader_id=admin_user.id
                )
                db.add(dataset)
                db.commit()

            # Check if an "E2E 全量扫测模块" exists for this classroom, if not, create it
            module_name = "E2E 全量视觉扫测校验模块"
            module = db.query(models.ResourceModule).filter(
                models.ResourceModule.classroom_id == course_id,
                models.ResourceModule.name == module_name
            ).first()

            if not module:
                module = models.ResourceModule(
                    classroom_id=course_id,
                    name=module_name,
                    created_by=admin_user.id
                )
                db.add(module)
                db.commit()
                db.refresh(module)

            # Check if the W3Schools video is mapped
            mp4_name = f"自动化全量覆盖扫测视频_{course_id}.mp4"
            mp4_file = db.query(models.ResourceFile).filter(
                models.ResourceFile.module_id == module.id,
                models.ResourceFile.name == mp4_name
            ).first()

            url = "/static/resources/E2E_Test_Dummy.mp4"
            
            if not mp4_file:
                mp4_file = models.ResourceFile(
                    module_id=module.id,
                    name=mp4_name,
                    url=url,
                    file_type="video/mp4",
                    file_size=788493, # Exact W3Schools dummy size
                    uploader_id=admin_user.id
                )
                db.add(mp4_file)
                inserted_count += 1
            else:
                mp4_file.url = url
                db.add(mp4_file)

            # Check if the PPTX dummy is mapped
            ppt_name = f"自动化全量覆盖扫测演示文稿_{course_id}.pptx"
            ppt_file = db.query(models.ResourceFile).filter(
                models.ResourceFile.module_id == module.id,
                models.ResourceFile.name == ppt_name
            ).first()

            if not ppt_file:
                ppt_file = models.ResourceFile(
                    module_id=module.id,
                    name=ppt_name,
                    url="/static/resources/E2E_Test_Dummy.pptx", # Faked path that triggers the fallback download logic in iframe wrapper
                    file_type="application/x-pptx",
                    file_size=1024,
                    uploader_id=admin_user.id
                )
                db.add(ppt_file)
                inserted_count += 1

        db.commit()
        print(f"\n✅ 成功植入 {inserted_count} 个 E2E 视觉校验用例。")
        print("-> 所有 18 门课程均已具备 1 个外站流媒体视频以及 1 个内网课件的断言素材。")

    except Exception as e:
        db.rollback()
        print(f"❌ 植入过程中出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_18_courses()
