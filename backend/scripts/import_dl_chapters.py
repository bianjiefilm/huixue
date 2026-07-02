#!/usr/bin/env python3
"""
导入《神经网络与深度学习》课程的章节和实践任务
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.models import Course, Chapter, Practice, Task, DifficultyLevelEnum, TaskTypeEnum

# 课程ID (Docker PostgreSQL中)
COURSE_ID = 4

# 章节列表（基于本地目录结构）
CHAPTERS = [
    {"order": 0, "title": "人工智能起源与发展", "experiment_count": 1},
    {"order": 1, "title": "TensorFlow环境安装", "experiment_count": 2},
    {"order": 2, "title": "Python语言基础", "experiment_count": 2},
    {"order": 3, "title": "科学计算与可视化", "experiment_count": 2},
    {"order": 4, "title": "TensorFlow基础", "experiment_count": 2},
    {"order": 5, "title": "监督学习基础", "experiment_count": 2},
    {"order": 6, "title": "人工神经网络", "experiment_count": 2},
    {"order": 7, "title": "深度学习基础", "experiment_count": 2},
    {"order": 8, "title": "卷积神经网络", "experiment_count": 2},
    {"order": 9, "title": "目标检测基础", "experiment_count": 1},
]

# 10个深度学习实践任务
PRACTICES = [
    {"id": "dl01", "title": "TensorFlow环境配置", "description": "安装配置TensorFlow 2.0开发环境", "difficulty": "BEGINNER"},
    {"id": "dl02", "title": "NumPy与Matplotlib实战", "description": "科学计算与数据可视化基础", "difficulty": "BEGINNER"},
    {"id": "dl03", "title": "张量操作与自动微分", "description": "TensorFlow核心概念与操作", "difficulty": "INTERMEDIATE"},
    {"id": "dl04", "title": "线性回归模型", "description": "使用TensorFlow实现线性回归", "difficulty": "INTERMEDIATE"},
    {"id": "dl05", "title": "多层感知机MLP", "description": "构建多层神经网络分类器", "difficulty": "INTERMEDIATE"},
    {"id": "dl06", "title": "反向传播与优化器", "description": "理解和实现梯度下降优化", "difficulty": "INTERMEDIATE"},
    {"id": "dl07", "title": "卷积神经网络CNN", "description": "构建图像分类CNN模型", "difficulty": "ADVANCED"},
    {"id": "dl08", "title": "经典CNN架构实现", "description": "实现LeNet/VGG等经典网络", "difficulty": "ADVANCED"},
    {"id": "dl09", "title": "目标检测入门", "description": "YOLO/SSD目标检测基础", "difficulty": "ADVANCED"},
    {"id": "dl10", "title": "深度学习综合项目", "description": "端到端深度学习应用开发", "difficulty": "ADVANCED"},
]


def import_chapters_and_practices():
    """导入章节和实践任务"""
    db = next(get_db())

    try:
        course = db.query(Course).filter(Course.id == COURSE_ID).first()
        if not course:
            print(f"课程不存在: ID={COURSE_ID}")
            return

        print(f"找到课程: {course.title} (ID: {course.id})")

        # 1. 导入章节
        print("\n=== 导入章节 ===")
        chapter_count = 0
        for ch in CHAPTERS:
            existing = db.query(Chapter).filter(
                Chapter.course_id == COURSE_ID,
                Chapter.title == ch["title"]
            ).first()

            if existing:
                print(f"  章节已存在: {ch['title']}")
                continue

            chapter = Chapter(
                course_id=COURSE_ID,
                title=ch["title"],
                order_index=ch["order"],
                experiment_count=ch["experiment_count"]
            )
            db.add(chapter)
            chapter_count += 1
            print(f"  创建章节: {ch['title']}")

        db.flush()
        print(f"新增章节: {chapter_count}")

        # 2. 导入实践任务
        print("\n=== 导入实践任务 ===")
        practice_count = 0

        for prac in PRACTICES:
            existing = db.query(Practice).filter(
                Practice.parent_course_id == COURSE_ID,
                Practice.title == prac["title"]
            ).first()

            if existing:
                print(f"  实践已存在: {prac['title']}")
                continue

            difficulty_map = {
                "BEGINNER": DifficultyLevelEnum.beginner,
                "INTERMEDIATE": DifficultyLevelEnum.intermediate,
                "ADVANCED": DifficultyLevelEnum.advanced
            }

            practice = Practice(
                title=prac["title"],
                description=prac["description"],
                summary=prac["description"],
                difficulty=difficulty_map.get(prac["difficulty"], DifficultyLevelEnum.intermediate),
                direction="人工智能",
                category="深度学习",
                practice_type="online_coding",
                parent_course_id=COURSE_ID
            )
            db.add(practice)
            db.flush()

            task = Task(
                practice_id=practice.id,
                title=f"{prac['title']} - 实验任务",
                task_type=TaskTypeEnum.PRACTICE,
                order_in_practice=0,
                coin=15,
                handbook_markdown=f"## {prac['title']}\n\n{prac['description']}"
            )
            db.add(task)

            practice_count += 1
            print(f"  创建实践: {prac['title']} (ID: {practice.id})")

        # 3. 更新课程统计
        total_chapters = db.query(Chapter).filter(Chapter.course_id == COURSE_ID).count()
        total_practices = db.query(Practice).filter(Practice.parent_course_id == COURSE_ID).count()

        course.practice_task_count = total_practices

        db.commit()

        print(f"\n=== 导入完成 ===")
        print(f"课程: {course.title}")
        print(f"章节数: {total_chapters}")
        print(f"实践数: {total_practices}")

    except Exception as e:
        db.rollback()
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_chapters_and_practices()
