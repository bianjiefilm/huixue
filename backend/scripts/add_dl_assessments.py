#!/usr/bin/env python3
"""
为《神经网络与深度学习》课程添加考核配置
"""
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.models import CourseAssessment

# 课程ID
COURSE_ID = 4

# 考核配置
ASSESSMENTS = [
    {
        "title": "第一单元测验 - AI基础与环境配置",
        "assessment_type": "单元测验",
        "url": "/api/v1/exams/placeholder/unit1"
    },
    {
        "title": "第二单元测验 - Python与科学计算",
        "assessment_type": "单元测验",
        "url": "/api/v1/exams/placeholder/unit2"
    },
    {
        "title": "第三单元测验 - TensorFlow基础",
        "assessment_type": "单元测验",
        "url": "/api/v1/exams/placeholder/unit3"
    },
    {
        "title": "期中考试 - 神经网络基础",
        "assessment_type": "期中考试",
        "url": "/api/v1/exams/placeholder/midterm"
    },
    {
        "title": "第四单元测验 - 深度学习与CNN",
        "assessment_type": "单元测验",
        "url": "/api/v1/exams/placeholder/unit4"
    },
    {
        "title": "期末考试 - 神经网络与深度学习综合",
        "assessment_type": "期末考试",
        "url": "/api/v1/exams/placeholder/final"
    },
    {
        "title": "实践项目评估 - 目标检测应用",
        "assessment_type": "项目评估",
        "url": "/api/v1/exams/placeholder/project"
    },
]


def add_assessments():
    """添加考核配置"""
    db = SessionLocal()

    try:
        # 检查现有考核
        existing = db.query(CourseAssessment).filter(
            CourseAssessment.course_id == COURSE_ID
        ).all()

        if existing:
            print(f"课程 {COURSE_ID} 已有 {len(existing)} 个考核配置")
            response = input("是否删除现有配置并重新创建？(y/N): ")
            if response.lower() == 'y':
                for a in existing:
                    db.delete(a)
                db.commit()
                print("已删除现有考核配置")
            else:
                print("保留现有配置，退出")
                return

        # 添加新考核
        print(f"\n添加考核配置...")
        for assessment in ASSESSMENTS:
            new_assessment = CourseAssessment(
                course_id=COURSE_ID,
                title=assessment["title"],
                url=assessment["url"],
                assessment_type=assessment["assessment_type"]
            )
            db.add(new_assessment)
            print(f"  添加: {assessment['title']} ({assessment['assessment_type']})")

        db.commit()

        # 统计
        total = db.query(CourseAssessment).filter(
            CourseAssessment.course_id == COURSE_ID
        ).count()

        print(f"\n添加完成:")
        print(f"  考核总数: {total}")

        # 按类型统计
        from sqlalchemy import func
        stats = db.query(
            CourseAssessment.assessment_type,
            func.count(CourseAssessment.id)
        ).filter(
            CourseAssessment.course_id == COURSE_ID
        ).group_by(CourseAssessment.assessment_type).all()

        print("\n按类型统计:")
        for atype, count in stats:
            print(f"  {atype}: {count} 个")

    except Exception as e:
        db.rollback()
        print(f"添加失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("为《神经网络与深度学习》课程添加考核配置")
    print("=" * 60)
    add_assessments()
