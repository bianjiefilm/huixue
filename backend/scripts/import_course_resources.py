#!/usr/bin/env python3
"""
简化的课程资源导入脚本
扫描 ziyuan_data/课程资源 目录，创建课程和资源记录
"""
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.models import Course, CourseResource, CourseTypeEnum, DifficultyEnum, CourseVisibilityEnum

def get_resource_type(filename: str) -> str:
    """根据文件名判断资源类型"""
    ext = Path(filename).suffix.lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext in ['.ppt', '.pptx']:
        return 'ppt'
    elif ext in ['.doc', '.docx']:
        return 'doc'
    elif ext in ['.mp4', '.avi', '.mov']:
        return 'video'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        return 'image'
    else:
        return 'other'

def import_courses_and_resources():
    """导入课程和资源"""
    # 获取资源目录
    resource_base_dir = os.environ.get('RESOURCE_BASE_DIR', '/app/ziyuan_data')
    course_dir = Path(resource_base_dir) / "课程资源"

    if not course_dir.exists():
        print(f"课程资源目录不存在: {course_dir}")
        return

    db = next(get_db())

    try:
        course_count = 0
        resource_count = 0

        # 遍历课程目录
        for course_folder in course_dir.iterdir():
            if not course_folder.is_dir() or course_folder.name.startswith('.'):
                continue

            course_name = course_folder.name
            print(f"\n处理课程: {course_name}")

            # 检查课程是否已存在
            existing_course = db.query(Course).filter(Course.title == course_name).first()

            if existing_course:
                course = existing_course
                print(f"  课程已存在 (ID: {course.id})")
            else:
                # 创建新课程
                course = Course(
                    title=course_name,
                    course_type=CourseTypeEnum.COURSE_MATERIAL,
                    description=f"{course_name} 课程教材",
                    difficulty=DifficultyEnum.INTERMEDIATE,
                    direction="大数据",
                    visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
                )
                db.add(course)
                db.flush()  # 获取ID
                course_count += 1
                print(f"  创建课程 (ID: {course.id})")

            # 扫描课程目录下的资源文件
            resource_files = []
            for root, dirs, files in os.walk(course_folder):
                for file in files:
                    if file.startswith('.'):
                        continue
                    ext = Path(file).suffix.lower()
                    if ext in ['.pdf', '.ppt', '.pptx', '.doc', '.docx', '.mp4']:
                        rel_path = Path(root).relative_to(course_folder)
                        resource_files.append({
                            'filename': file,
                            'relative_path': str(rel_path / file),
                            'full_path': os.path.join(root, file)
                        })

            print(f"  发现 {len(resource_files)} 个资源文件")

            # 创建资源记录
            for res_file in resource_files:
                # 检查资源是否已存在
                existing_resource = db.query(CourseResource).filter(
                    CourseResource.course_id == course.id,
                    CourseResource.title == res_file['filename']
                ).first()

                if existing_resource:
                    continue

                # 构建URL路径
                url_path = f"/api/v1/files/teaching-resources/课程资源/{course_name}/{res_file['relative_path']}"

                resource = CourseResource(
                    course_id=course.id,
                    title=res_file['filename'],
                    url=url_path,
                    resource_type=get_resource_type(res_file['filename']),
                    can_download=True
                )
                db.add(resource)
                resource_count += 1

            # 更新课程的资源计数
            total_resources = db.query(CourseResource).filter(
                CourseResource.course_id == course.id
            ).count()
            course.material_resources_count = total_resources

        db.commit()
        print(f"\n=== 导入完成 ===")
        print(f"新增课程: {course_count}")
        print(f"新增资源: {resource_count}")

    except Exception as e:
        db.rollback()
        print(f"导入失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import_courses_and_resources()
