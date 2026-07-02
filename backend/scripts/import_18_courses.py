import os
import sys
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models

# Sample data dictionary constructed from the user's list
INVENTORY = [
    # 实验课程包 (Practices)
    {
        "title": "大数据技术基础与应用实践", "type": "practice", 
        "files": {"教学视频": 30, "PDF文档": 28, "教学方案(DOCX)": 28, "教学手册(MD)": 28, "数据集文件": 15, "代码脚本": 15, "配套图片": 1}
    },
    {
        "title": "Spark编程基础（Python版）", "type": "practice", 
        "files": {"教学视频": 23, "PDF文档": 135, "教学方案(DOCX)": 30, "教学手册(MD)": 49, "数据集文件": 66, "代码脚本": 41, "配套图片": 1, "其他资源": 18}
    },
    {
        "title": "数据采集与预处理", "type": "practice", 
        "files": {"教学视频": 16, "PDF文档": 19, "教学方案(DOCX)": 16, "教学手册(MD)": 15, "Jupyter Notebook": 10, "数据集文件": 30, "代码脚本": 8, "配套图片": 2, "其他资源": 17}
    },
    {
        "title": "数据清洗", "type": "practice", 
        "files": {"教学视频": 8, "PDF文档": 14, "PPT课件": 8, "教学方案(DOCX)": 14, "教学手册(MD)": 19, "数据集文件": 25, "代码脚本": 3, "配套图片": 2, "配套软件/依赖": 3, "其他资源": 31}
    },
    {
        "title": "Python程序设计", "type": "practice", 
        "files": {"教学视频": 29, "PDF文档": 136, "教学方案(DOCX)": 35, "教学手册(MD)": 54, "Jupyter Notebook": 9, "数据集文件": 103, "代码脚本": 45, "配套图片": 54, "其他资源": 20}
    },
    {
        "title": "数据挖掘（机器学习）", "type": "practice", 
        "files": {"教学视频": 10, "PDF文档": 30, "教学方案(DOCX)": 10, "教学手册(MD)": 20, "Jupyter Notebook": 6, "数据集文件": 25, "配套图片": 1, "其他资源": 18}
    },
    {
        "title": "神经网络与深度学习", "type": "practice", 
        "files": {"教学视频": 10, "PDF文档": 24, "PPT课件": 10, "教学方案(DOCX)": 24, "教学手册(MD)": 26, "数据集文件": 14, "代码脚本": 21, "配套图片": 1, "其他资源": 1}
    },
    {
        "title": "计算机视觉", "type": "practice", 
        "files": {"教学视频": 10, "PPT课件": 10, "教学手册(MD)": 2, "数据集文件": 1, "代码脚本": 3}
    },
    # 实训案例 (Trainings)
    {
        "title": "某零售企业经营分析", "type": "training", 
        "files": {"教学视频": 2, "教学手册(MD)": 7, "数据集文件": 11, "代码脚本": 6, "配套图片": 107, "其他资源": 2}
    },
    {
        "title": "公募基金精准营销案例", "type": "training", 
        "files": {"教学手册(MD)": 10, "数据集文件": 10, "代码脚本": 8, "配套图片": 26, "其他资源": 2}
    },
    {
        "title": "某高校校情管理分析案例", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 6}
    },
    {
        "title": "企业用能环保监测分析", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 6, "配套图片": 1, "其他资源": 1}
    },
    {
        "title": "某公司人力薪酬分析", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 2}
    },
    {
        "title": "某公司财务报表分析案例", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 7, "代码脚本": 3}
    },
    {
        "title": "某电商货品销售分析案例", "type": "training", 
        "files": {"教学手册(MD)": 1, "数据集文件": 2, "代码脚本": 1, "配套图片": 1}
    },
    {
        "title": "某公司应收账款分析案例", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 2}
    },
    {
        "title": "风电齿轮箱预警分析", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 4, "代码脚本": 2}
    },
    {
        "title": "分布式光伏出力预测", "type": "training", 
        "files": {"教学手册(MD)": 1, "Jupyter Notebook": 1, "数据集文件": 3, "代码脚本": 1}
    }
]

EXT_MAPPING = {
    "教学视频": ("mp4", "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"),
    "PDF文档": ("pdf", "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"),
    "PPT课件": ("pptx", "https://example.com/dummy.pptx"),
    "教学方案(DOCX)": ("docx", "https://example.com/dummy.docx"),
    "教学手册(MD)": ("md", "https://raw.githubusercontent.com/markdown-it/markdown-it/master/README.md"),
    "Jupyter Notebook": ("ipynb", "https://example.com/dummy.ipynb"),
    "数据集文件": ("csv", "/app/ziyuan_data/dummy.csv"),
    "代码脚本": ("py", "https://example.com/dummy.py"),
    "配套图片": ("png", "https://via.placeholder.com/150"),
    "配套软件/依赖": ("zip", "https://example.com/dummy.zip"),
    "其他资源": ("zip", "https://example.com/dummy.zip")
}

PROJECT_PATH_MAP = {
    "某零售企业经营分析": "实训资源/01-某零售企业经营分析",
    "公募基金精准营销案例": "实训资源/02-公募基金精准营销案例",
    "某高校校情管理分析案例": "实训资源/07-某高校校情管理分析案例",
    "企业用能环保监测分析": "实训资源/06-企业用能环保监测分析",
    "某公司人力薪酬分析": "实训资源/09-某公司人力薪酬分析",
    "某公司财务报表分析案例": "实训资源/10-某公司财务报表分析案例",
    "某电商货品销售分析案例": "实训资源/05-某电商货品销售分析案例",
    "某公司应收账款分析案例": "课程资源/应收账款管理",
    "风电齿轮箱预警分析": "实训资源/11-风电齿轮箱预警分析",
    "分布式光伏出力预测": "实训资源/12-分布式光伏出力预测",
}

CLASSROOM_ID = 100
TEACHER_ID = 29

def seed_18_courses():
    db = SessionLocal()
    try:
        # Check classroom exists
        classroom = db.query(models.Classroom).filter(models.Classroom.id == CLASSROOM_ID).first()
        if not classroom:
            print(f"Error: Classroom {CLASSROOM_ID} not found.")
            return

        print("Removing previous mock resources for this script...")
        db.query(models.ResourceFile).filter(models.ResourceFile.uploader_id == TEACHER_ID, models.ResourceFile.name.like("%-[18_MOCK]-%")).delete(synchronize_session=False)
        db.commit()

        total_files = 0
        order_index = 10  # start after seeded courses

        for course in INVENTORY:
            print(f"Processing: {course['title']} ({course['type']})")
            
            if course['type'] == 'practice':
                # Create Practice
                practice = models.Practice(
                    title=course['title'],
                    description="18门标准课程实验包测试数据",
                    direction="后端开发",
                    category="Python",
                    difficulty="intermediate",
                    is_published=True,
                    publish_status="PUBLISHED",
                    visibility="PUBLIC",
                    practice_type="online_coding"
                )
                db.add(practice)
                db.flush()
                
                # Link to Classroom
                cls_course = models.ClassroomCourse(
                    classroom_id=CLASSROOM_ID,
                    practice_id=practice.id,
                    teacher_publish_status="LEARNING",
                    order_in_classroom=order_index
                )
                db.add(cls_course)
            
            elif course['type'] == 'training':
                # Create Training
                training = models.Training(
                    title=course['title'],
                    intro="18门标准课程实训案例测试数据",
                    training_type="DATA_ANALYSIS",
                    industry="IT",
                    difficulty="intermediate",
                    is_published=True,
                    publish_status="PUBLISHED",
                    visibility="PUBLIC",
                    project_path=PROJECT_PATH_MAP.get(course['title']),
                    creator_id=TEACHER_ID
                )
                db.add(training)
                db.flush()
                
                # Link to Classroom
                cls_training = models.ClassroomTraining(
                    classroom_id=CLASSROOM_ID,
                    training_id=training.id,
                    order_index=order_index
                )
                db.add(cls_training)

            order_index += 1

            # Provide Resources (Create Module)
            module = models.ResourceModule(
                classroom_id=CLASSROOM_ID,
                name=f"{course['title']} - 配套资源",
                description="标准正版课程素材",
                order_index=order_index,
                created_by=TEACHER_ID
            )
            db.add(module)
            db.flush()

            # Create Files
            for f_type, count in course['files'].items():
                ext, dummy_url = EXT_MAPPING.get(f_type, ("bin", "https://example.com/dummy.bin"))
                for i in range(count):
                    if f_type == "数据集文件":
                        # Create specific dataset records for BI workspaces
                        if course['type'] == 'practice':
                            ds = models.PracticeDataset(
                                practice_id=practice.id,
                                name=f"{course['title']}_dataset_{i+1}.{ext}",
                                file_url=dummy_url,
                                file_type=ext,
                                file_size=1024 * 1024,
                                uploader_id=TEACHER_ID
                            )
                            db.add(ds)
                        elif course['type'] == 'training':
                            # Skip generic dummy creation here; handled below
                            pass

                    file = models.ResourceFile(
                        module_id=module.id,
                        name=f"{course['title']}_{f_type}_-[18_MOCK]-_{i+1}.{ext}",
                        url=dummy_url,
                        file_type=ext,
                        file_size=1024 * 1024, # 1MB dummy
                        duration_seconds=120 if ext == 'mp4' else None,
                        uploader_id=TEACHER_ID
                    )
                    db.add(file)
                    total_files += 1

        # === Create TrainingDataset records for all training courses ===
        import glob as _glob
        from pathlib import Path as _Path
        RESOURCE_BASE = _Path("/app/ziyuan_data")

        # Collect all training objects created in this run
        all_trainings = db.query(models.Training).filter(
            models.Training.creator_id == TEACHER_ID,
            models.Training.training_type == "DATA_ANALYSIS"
        ).all()

        for tr in all_trainings:
            # Skip if already has datasets from a previous run
            existing = db.query(models.TrainingDataset).filter(
                models.TrainingDataset.training_id == tr.id
            ).count()
            if existing > 0:
                continue

            csv_files_found = []
            mapped_path = PROJECT_PATH_MAP.get(tr.title)
            if mapped_path:
                scan_dir = RESOURCE_BASE / mapped_path
                if scan_dir.exists():
                    # Scan recursively for CSV files
                    for csv_path in scan_dir.rglob("*.csv"):
                        rel = str(csv_path.relative_to(RESOURCE_BASE))
                        csv_files_found.append((csv_path.stem, rel, csv_path.stat().st_size))

            if csv_files_found:
                for name, rel_path, size in csv_files_found:
                    ds = models.TrainingDataset(
                        training_id=tr.id,
                        name=name,
                        file_url=f"/api/v1/storage/trainings/{tr.id}/datasets/{name}.csv",
                        relative_path=rel_path,
                        file_type="csv",
                        file_size=size,
                        uploader_id=TEACHER_ID
                    )
                    db.add(ds)
                print(f"  -> Created {len(csv_files_found)} REAL TrainingDataset records for '{tr.title}'")
            else:
                # Fallback: create dummy dataset records
                ds = models.TrainingDataset(
                    training_id=tr.id,
                    name=f"{tr.title}_sample_data",
                    file_url="/app/ziyuan_data/dummy.csv",
                    relative_path="dummy.csv",
                    file_type="csv",
                    file_size=1024,
                    uploader_id=TEACHER_ID
                )
                db.add(ds)
                print(f"  -> Created 1 DUMMY TrainingDataset record for '{tr.title}'")

        db.commit()
        print(f"\\n✅ Successfully seeded {len(INVENTORY)} courses and {total_files} resource files!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_18_courses()
