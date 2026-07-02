import os
import sys
import shutil
from pathlib import Path

# Fix python paths
if 'PYTHONPATH' in os.environ:
    del os.environ['PYTHONPATH']

backend_dir = "/Users/jimfu/Work/huixue/backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models
import mimetypes

def get_mime_type(filename):
    ext = Path(filename).suffix.lower()
    if ext == '.pdf': return 'application/pdf'
    if ext in ['.ppt', '.pptx']: return 'application/vnd.ms-powerpoint'
    if ext in ['.doc', '.docx']: return 'application/msword'
    if ext in ['.mp4']: return 'video/mp4'
    if ext in ['.jpg', '.png']: return 'image/jpeg'
    return 'application/octet-stream'

def restore_real_course_videos():
    mapping = {
        "Python程序设计": "python-programming",
        "Spark编程基础": "spark-basics",
        "数据采集与预处理": "data-collection-preprocessing",
        "数据清洗": "data-cleaning",
        "数据挖掘分析": "data-mining-analysis",
        "神经网络与深度学习": "neural-network-deep-learning",
        "应收账款管理": "accounts-receivable",
        "大数据技术基础与应用实践": "bigdata-fundamentals-practice"
    }

    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        admin_id = admin_user.id if admin_user else 1

        # 1. Clean up "E2E 全量视觉扫测校验模块" from ResourceModule and ResourceFile
        dummy_modules = db.query(models.ResourceModule).filter(
            models.ResourceModule.name == "E2E 全量视觉扫测校验模块"
        ).all()
        
        cleaned_files = 0
        cleaned_modules = 0
        for mod in dummy_modules:
            files = db.query(models.ResourceFile).filter(models.ResourceFile.module_id == mod.id).all()
            for f in files:
                db.delete(f)
                cleaned_files += 1
            db.delete(mod)
            cleaned_modules += 1
            
        db.commit()
        print(f"✅ 删除了 {cleaned_modules} 个 E2E 虚假测试模块 和 {cleaned_files} 个关联文件。")

        # 2. Iterate courses and copy real video files
        normalized_base = Path("/Users/jimfu/Work/huixue/ziyuan_normalized/B_Legacy_Materials/courses")
        live_base = Path("/Users/jimfu/Work/huixue/ziyuan_data/课程资源")
        
        inserted_count = 0
        
        for cn_name, en_name in mapping.items():
            print(f"\\n-> 恢复课程: {cn_name} ({en_name})")
            
            # Find the classroom for this course
            classroom = db.query(models.Classroom).filter(models.Classroom.name.like(f"%{cn_name}%")).first()
            if not classroom:
                print(f"   ⚠️ 未在数据库找到对应的课堂")
                continue
                
            norm_dir = normalized_base / en_name
            if not norm_dir.exists():
                print(f"   ⚠️ 未找到归一化源文件夹: {norm_dir}")
                continue
                
            # Create the Module "理论课件与视频"
            module_name = "理论课件与视频(已恢复真理资源)"
            module = db.query(models.ResourceModule).filter(
                models.ResourceModule.classroom_id == classroom.id,
                models.ResourceModule.name == module_name
            ).first()
            
            if not module:
                module = models.ResourceModule(
                    classroom_id=classroom.id,
                    name=module_name,
                    created_by=admin_id
                )
                db.add(module)
                db.commit()
                db.refresh(module)
                
            # Copy matching files
            target_out_dir = live_base / cn_name / "视频和课件"
            target_out_dir.mkdir(parents=True, exist_ok=True)
            
            # We want all mp4, pdf, pptx, docx inside `02-理论课件` and root dir
            valid_exts = {'.mp4', '.pdf', '.pptx', '.ppt', '.doc', '.docx'}
            
            # Helper to find and copy files
            def scan_and_copy(search_folder):
                nonlocal inserted_count
                if not search_folder.exists(): return
                for root, dirs, files in os.walk(search_folder):
                    for file in files:
                        ext = Path(file).suffix.lower()
                        if ext in valid_exts and not file.startswith('~'):
                            src_path = Path(root) / file
                            # Special case: Avoid copying dummy files or already present garbage
                            if "temp" in file.lower() or "E2E" in file:
                                continue
                                
                            dest_path = target_out_dir / file
                            
                            # Copy file if not exists
                            if not dest_path.exists():
                                shutil.copy2(src_path, dest_path)
                                
                            # Check if mapped to DB
                            existing_file = db.query(models.ResourceFile).filter(
                                models.ResourceFile.module_id == module.id,
                                models.ResourceFile.name == file
                            ).first()
                            
                            url_path = f"/static/resources/课程资源/{cn_name}/视频和课件/{file}"
                            
                            if not existing_file:
                                rf = models.ResourceFile(
                                    module_id=module.id,
                                    name=file,
                                    url=url_path,
                                    file_type=get_mime_type(file),
                                    file_size=dest_path.stat().st_size,
                                    uploader_id=admin_id
                                )
                                db.add(rf)
                                inserted_count += 1
                                print(f"   ✅ 恢复文件: {file}")
            
            scan_and_copy(norm_dir / "02-理论课件")
            scan_and_copy(norm_dir) # Scan root folder for any loose mp4/pptx
            
            db.commit()

        print(f"\\n🎉 真理课程视频恢复完毕！共补全 {inserted_count} 个物理原生课件资源文件。")

    except Exception as e:
        db.rollback()
        print(f"❌ 运行报错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore_real_course_videos()
