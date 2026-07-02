#!/usr/bin/env python3
"""
同步计算机视觉课程的PPT和视频资源到数据库
"""
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.models import CourseResource

# 课程ID
COURSE_ID = 5

# PPT资源（11个章节）
PPT_RESOURCES = [
    {"title": "第1章 计算机视觉概述 PPT", "filename": "chapter_01_计算机视觉概述.png"},
    {"title": "第2章 图像标注 PPT", "filename": "chapter_02_图像标注.png"},
    {"title": "第3章 神经网络基础 PPT", "filename": "chapter_03_神经网络基础.png"},
    {"title": "第4章 卷积神经网络CNN PPT", "filename": "chapter_04_卷积神经网络CNN.png"},
    {"title": "第5章 经典CNN模型 PPT", "filename": "chapter_05_经典CNN模型.png"},
    {"title": "第6章 目标检测基础 PPT", "filename": "chapter_06_目标检测基础.png"},
    {"title": "第7章 RCNN系列算法 PPT", "filename": "chapter_07_RCNN系列算法.png"},
    {"title": "第8章 YOLO系列算法 PPT", "filename": "chapter_08_YOLO系列算法.png"},
    {"title": "第9章 语义分割 PPT", "filename": "chapter_09_语义分割.png"},
    {"title": "第10章 目标跟踪 PPT", "filename": "chapter_10_目标跟踪.png"},
    {"title": "第11章 图像生成 PPT", "filename": "chapter_11_图像生成.png"},
]

# 视频资源（11个章节）
VIDEO_RESOURCES = [
    {"title": "第1章 计算机视觉概述 视频", "filename": "chapter_01_计算机视觉概述.mp4"},
    {"title": "第2章 图像标注 视频", "filename": "chapter_02_图像标注.mp4"},
    {"title": "第3章 神经网络基础 视频", "filename": "chapter_03_神经网络基础.mp4"},
    {"title": "第4章 卷积神经网络CNN 视频", "filename": "chapter_04_卷积神经网络CNN.mp4"},
    {"title": "第5章 经典CNN模型 视频", "filename": "chapter_05_经典CNN模型.mp4"},
    {"title": "第6章 目标检测基础 视频", "filename": "chapter_06_目标检测基础.mp4"},
    {"title": "第7章 RCNN系列算法 视频", "filename": "chapter_07_RCNN系列算法.mp4"},
    {"title": "第8章 YOLO系列算法 视频", "filename": "chapter_08_YOLO系列算法.mp4"},
    {"title": "第9章 语义分割 视频", "filename": "chapter_09_语义分割.mp4"},
    {"title": "第10章 目标跟踪 视频", "filename": "chapter_10_目标跟踪.mp4"},
    {"title": "第11章 图像生成 视频", "filename": "chapter_11_图像生成.mp4"},
]

# 资源URL前缀
BASE_URL = "/api/v1/files/teaching-resources/课程资源/计算机视觉/assets"


def sync_resources():
    """同步PPT和视频资源"""
    db = SessionLocal()

    try:
        added_count = 0
        skipped_count = 0

        # 获取现有资源URL列表
        existing_urls = set()
        existing = db.query(CourseResource).filter(
            CourseResource.course_id == COURSE_ID
        ).all()
        for r in existing:
            existing_urls.add(r.url)

        print(f"课程 {COURSE_ID} 现有 {len(existing_urls)} 个资源")

        # 添加PPT资源
        print("\n添加PPT资源...")
        for ppt in PPT_RESOURCES:
            url = f"{BASE_URL}/slides/{ppt['filename']}"

            if url in existing_urls:
                print(f"  跳过（已存在）: {ppt['title']}")
                skipped_count += 1
                continue

            resource = CourseResource(
                course_id=COURSE_ID,
                title=ppt['title'],
                url=url,
                resource_type="ppt",
                can_download=True
            )
            db.add(resource)
            print(f"  添加: {ppt['title']}")
            added_count += 1

        # 添加视频资源
        print("\n添加视频资源...")
        for video in VIDEO_RESOURCES:
            url = f"{BASE_URL}/videos/{video['filename']}"

            if url in existing_urls:
                print(f"  跳过（已存在）: {video['title']}")
                skipped_count += 1
                continue

            resource = CourseResource(
                course_id=COURSE_ID,
                title=video['title'],
                url=url,
                resource_type="video",
                can_download=True
            )
            db.add(resource)
            print(f"  添加: {video['title']}")
            added_count += 1

        db.commit()

        print(f"\n同步完成:")
        print(f"  新增: {added_count} 个资源")
        print(f"  跳过: {skipped_count} 个资源（已存在）")

        # 统计各类型资源数量
        print("\n当前资源统计:")
        for rtype in ['pdf', 'doc', 'ppt', 'video']:
            count = db.query(CourseResource).filter(
                CourseResource.course_id == COURSE_ID,
                CourseResource.resource_type == rtype
            ).count()
            print(f"  {rtype}: {count} 个")

    except Exception as e:
        db.rollback()
        print(f"同步失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("同步《计算机视觉》课程PPT和视频资源")
    print("=" * 60)
    sync_resources()
