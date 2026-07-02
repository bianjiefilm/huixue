#!/usr/bin/env python3
"""
课程教材导入工具
根据course_metadata.json配置文件导入课程教材到数据库
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import models
from app.models.models import CourseTypeEnum, DifficultyEnum, CourseVisibilityEnum


def load_course_metadata(config_path: str) -> dict:
    """加载课程元数据配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def map_difficulty(difficulty_str: str) -> DifficultyEnum:
    """映射难度级别"""
    mapping = {
        'BEGINNER': DifficultyEnum.beginner,
        'INTERMEDIATE': DifficultyEnum.intermediate,
        'ADVANCED': DifficultyEnum.advanced
    }
    return mapping.get(difficulty_str, DifficultyEnum.intermediate)


def map_visibility(visibility_str: str) -> CourseVisibilityEnum:
    """映射可见性"""
    mapping = {
        'PRIVATE': CourseVisibilityEnum.PRIVATE,
        'PUBLIC_SELF': CourseVisibilityEnum.PUBLIC_SELF,
        'PUBLIC_PLATFORM': CourseVisibilityEnum.PUBLIC_PLATFORM
    }
    return mapping.get(visibility_str, CourseVisibilityEnum.PRIVATE)


def import_course(db: Session, config_data: dict, config_dir: Path) -> models.Course:
    """导入课程基本信息"""
    course_info = config_data.get('course', {})
    teaching_info = config_data.get('teaching_info', {})
    metadata = config_data.get('metadata', {})
    resources = config_data.get('resources', {})
    
    # 创建课程记录
    course = models.Course(
        title=course_info.get('title'),
        course_type=CourseTypeEnum.COURSE_MATERIAL,
        description=course_info.get('description'),
        difficulty=map_difficulty(course_info.get('difficulty', 'INTERMEDIATE')),
        direction=course_info.get('direction'),
        categories=json.dumps(course_info.get('categories', []), ensure_ascii=False),
        visibility=map_visibility(course_info.get('visibility', 'PRIVATE')),
        
        # 元数据字段（如果数据库模型支持）
        # 注意：这些字段需要确保数据库模型中存在
        source=metadata.get('publisher'),  # 使用publisher作为source
        
        # 统计信息
        practice_task_count=resources.get('practice_task_count', 0),
        material_resources_count=resources.get('materials_count', 0),
        material_assessments_count=resources.get('assessments_count', 0),
        
        # 时间戳
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(course)
    db.flush()  # 获取course.id
    
    print(f"✅ 课程创建成功: {course.title} (ID: {course.id})")
    return course


def import_chapters(db: Session, course: models.Course, chapters_data: list):
    """导入章节信息"""
    for chapter_info in chapters_data:
        chapter = models.Chapter(
            course_id=course.id,
            title=chapter_info.get('title'),
            order_index=chapter_info.get('order_index'),
            experiment_count=chapter_info.get('experiment_count', 0),
            created_at=datetime.now()
        )
        db.add(chapter)
    
    db.flush()
    print(f"✅ 章节导入成功: {len(chapters_data)} 个章节")


def import_course_material(config_path: str, log_path: str = None):
    """导入课程教材主函数"""
    
    print("=" * 60)
    print("📚 课程教材导入工具")
    print("=" * 60)
    
    # 检查配置文件
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"❌ 错误: 配置文件不存在: {config_path}")
        return False
    
    config_dir = config_file.parent
    print(f"📂 配置文件: {config_path}")
    print(f"📂 课程目录: {config_dir}")
    
    # 加载配置
    try:
        config_data = load_course_metadata(config_path)
        print(f"✅ 配置加载成功")
        print(f"📖 课程名称: {config_data.get('course', {}).get('title')}")
        print(f"📖 版本: {config_data.get('version')}")
    except Exception as e:
        print(f"❌ 错误: 无法加载配置文件: {e}")
        return False
    
    # 连接数据库
    db = SessionLocal()
    
    try:
        # 检查课程是否已存在
        course_title = config_data.get('course', {}).get('title')
        existing_course = db.query(models.Course).filter(
            models.Course.title == course_title,
            models.Course.course_type == CourseTypeEnum.COURSE_MATERIAL
        ).first()
        
        if existing_course:
            print(f"⚠️  警告: 课程已存在 (ID: {existing_course.id})")
            response = input("是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("❌ 导入取消")
                return False
            
            # 删除旧记录
            db.delete(existing_course)
            db.commit()
            print("✅ 旧记录已删除")
        
        print("\n" + "=" * 60)
        print("开始导入...")
        print("=" * 60)
        
        # 1. 导入课程基本信息
        print("\n[1/3] 导入课程基本信息...")
        course = import_course(db, config_data, config_dir)
        
        # 2. 导入章节
        print("\n[2/3] 导入章节...")
        chapters_data = config_data.get('structure', {}).get('chapters', [])
        if chapters_data:
            import_chapters(db, course, chapters_data)
        else:
            print("⚠️  警告: 没有章节数据")
        
        # 3. 提交事务
        print("\n[3/3] 提交事务...")
        db.commit()
        print("✅ 事务提交成功")
        
        # 导入总结
        print("\n" + "=" * 60)
        print("📊 导入总结")
        print("=" * 60)
        print(f"✅ 课程ID: {course.id}")
        print(f"✅ 课程名称: {course.title}")
        print(f"✅ 章节数量: {len(chapters_data)}")
        print(f"✅ 实践课程: {len(config_data.get('structure', {}).get('practice_courses', []))}")
        print(f"✅ 实训项目: {len(config_data.get('structure', {}).get('training_projects', []))}")
        print(f"✅ 教学资源: {course.material_resources_count}")
        print(f"✅ 考核试卷: {course.material_assessments_count}")
        
        # 保存导入日志
        if log_path:
            log_data = {
                'import_time': datetime.now().isoformat(),
                'config_file': str(config_path),
                'course_id': course.id,
                'course_title': course.title,
                'status': 'success'
            }
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 导入日志已保存: {log_path}")
        
        print("\n" + "=" * 60)
        print("✅ 导入完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: 导入失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='课程教材导入工具')
    parser.add_argument('--config', required=True, help='课程配置文件路径')
    parser.add_argument('--log', help='导入日志保存路径')
    
    args = parser.parse_args()
    
    success = import_course_material(args.config, args.log)
    sys.exit(0 if success else 1)



