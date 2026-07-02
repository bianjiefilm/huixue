#!/usr/bin/env python3
"""
导入《数据清洗》课程的章节和实践任务
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.models import Course, Chapter, Practice, Task, DifficultyLevelEnum

# 数据清洗课程ID
COURSE_ID = 3

# 章节列表（基于本地目录结构）
CHAPTERS = [
    {"order": 0, "title": "数据清洗概述", "experiment_count": 2},
    {"order": 1, "title": "ETL基础", "experiment_count": 2},
    {"order": 2, "title": "数据质量评估", "experiment_count": 2},
    {"order": 3, "title": "Kettle工具安装", "experiment_count": 1},
    {"order": 4, "title": "重复数据处理", "experiment_count": 1},
    {"order": 5, "title": "Kettle基本使用", "experiment_count": 2},
    {"order": 6, "title": "格式标准化", "experiment_count": 1},
    {"order": 7, "title": "数据抽取", "experiment_count": 2},
    {"order": 8, "title": "数据一致性处理", "experiment_count": 1},
    {"order": 9, "title": "文本数据清洗", "experiment_count": 1},
    {"order": 10, "title": "数据清洗与校验", "experiment_count": 2},
    {"order": 11, "title": "数据转换", "experiment_count": 2},
    {"order": 12, "title": "数据清洗自动化", "experiment_count": 1},
    {"order": 13, "title": "数据加载", "experiment_count": 2},
    {"order": 14, "title": "数据清洗实战", "experiment_count": 1},
]

# 18个Kettle实验任务
PRACTICES = [
    {"id": "exp01", "title": "CSV数据输入", "description": "学习使用Kettle读取CSV文件", "difficulty": "BEGINNER"},
    {"id": "exp02", "title": "Excel数据输入", "description": "学习使用Kettle读取Excel文件", "difficulty": "BEGINNER"},
    {"id": "exp03", "title": "文本数据输入", "description": "学习使用Kettle读取文本文件", "difficulty": "BEGINNER"},
    {"id": "exp04", "title": "数据库表输入", "description": "学习使用Kettle从数据库读取数据", "difficulty": "INTERMEDIATE"},
    {"id": "exp05", "title": "JSON数据输入", "description": "学习使用Kettle读取JSON文件", "difficulty": "INTERMEDIATE"},
    {"id": "exp06", "title": "多源数据合并", "description": "学习使用Kettle合并多个数据源", "difficulty": "INTERMEDIATE"},
    {"id": "exp07", "title": "字段选择与过滤", "description": "学习使用Kettle进行字段筛选", "difficulty": "BEGINNER"},
    {"id": "exp08", "title": "行过滤", "description": "学习使用Kettle过滤数据行", "difficulty": "BEGINNER"},
    {"id": "exp09", "title": "去重处理", "description": "学习使用Kettle去除重复数据", "difficulty": "INTERMEDIATE"},
    {"id": "exp10", "title": "空值处理", "description": "学习使用Kettle处理空值", "difficulty": "INTERMEDIATE"},
    {"id": "exp11", "title": "字符串操作", "description": "学习使用Kettle进行字符串操作", "difficulty": "INTERMEDIATE"},
    {"id": "exp12", "title": "数据校验", "description": "学习使用Kettle进行数据校验", "difficulty": "INTERMEDIATE"},
    {"id": "exp13", "title": "值映射转换", "description": "学习使用Kettle进行值映射", "difficulty": "INTERMEDIATE"},
    {"id": "exp14", "title": "字段拼接与拆分", "description": "学习字段拼接和拆分操作", "difficulty": "INTERMEDIATE"},
    {"id": "exp15", "title": "数据库表输出", "description": "学习使用Kettle输出到数据库", "difficulty": "INTERMEDIATE"},
    {"id": "exp16", "title": "文件输出", "description": "学习使用Kettle输出到文件", "difficulty": "BEGINNER"},
    {"id": "exp17", "title": "错误处理", "description": "学习Kettle的错误处理机制", "difficulty": "ADVANCED"},
    {"id": "exp18", "title": "完整ETL流程", "description": "综合实践：完整的ETL流程设计", "difficulty": "ADVANCED"},
]


def import_chapters_and_practices():
    """导入章节和实践任务"""
    db = next(get_db())

    try:
        # 检查课程是否存在
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

            # 映射难度
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
                direction="大数据",
                category="数据清洗",
                practice_type="cloud_desktop",  # VDI类型
                parent_course_id=COURSE_ID
            )
            db.add(practice)
            db.flush()

            # 创建一个任务关卡
            from app.models.models import TaskTypeEnum
            task = Task(
                practice_id=practice.id,
                title=f"{prac['title']} - 任务",
                task_type=TaskTypeEnum.PRACTICE,
                order_in_practice=0,
                coin=10,
                handbook_markdown=f"## {prac['title']}\n\n{prac['description']}"
            )
            db.add(task)

            practice_count += 1
            print(f"  创建实践: {prac['title']} (ID: {practice.id})")

        # 3. 更新课程统计
        total_chapters = db.query(Chapter).filter(Chapter.course_id == COURSE_ID).count()
        total_practices = db.query(Practice).filter(Practice.parent_course_id == COURSE_ID).count()
        total_experiments = sum(ch["experiment_count"] for ch in CHAPTERS)

        course.practice_task_count = total_practices

        db.commit()

        print(f"\n=== 导入完成 ===")
        print(f"课程: {course.title}")
        print(f"章节数: {total_chapters}")
        print(f"实践数: {total_practices}")
        print(f"总实验数: {total_experiments}")

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
