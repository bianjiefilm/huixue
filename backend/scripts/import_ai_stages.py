#!/usr/bin/env python3
"""
导入AI生成的阶段内容到数据库
包括: 实训手册、题目、参考答案

用法:
    python import_ai_stages.py [--dry-run] [--course python|nn|all]

示例:
    python import_ai_stages.py                    # 导入所有课程
    python import_ai_stages.py --course python   # 只导入Python课程
    python import_ai_stages.py --dry-run         # 预览模式，不写入数据库
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ============= 配置 =============
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://huixue:huixue123@localhost:5432/huixue"
)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

# 课程配置
COURSES_CONFIG = {
    "python": {
        "title": "Python程序设计",
        "direction": "Python开发",
        "category": "编程语言",
        "files": [
            OUTPUT_DIR / "stage_python_1-5_fixed.json",
            OUTPUT_DIR / "stage_python_6-12.json",
        ],
    },
    "nn": {
        "title": "神经网络与深度学习",
        "direction": "人工智能",
        "category": "深度学习",
        "files": [
            OUTPUT_DIR / "stage_nn_1-6_fixed.json",
            OUTPUT_DIR / "stage_07_object_detection.json",
            OUTPUT_DIR / "stage_08_rcnn_series.json",
            OUTPUT_DIR / "stage_09_yolo_series.json",
            OUTPUT_DIR / "stage_10_semantic_segmentation.json",
            OUTPUT_DIR / "stage_11_object_tracking_fixed.json",
            OUTPUT_DIR / "stage_12_image_generation.json",
        ],
    },
}

# ============= 数据库操作 =============

def get_db_session():
    """创建数据库会话"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def find_or_create_course(session, config: dict) -> dict:
    """查找或创建课程"""
    title = config["title"]

    # 查询课程
    result = session.execute(
        text("SELECT id FROM courses WHERE title = :title"),
        {"title": title}
    ).fetchone()

    if result:
        course_id = result[0]
        print(f"  找到已有课程: {title} (ID: {course_id})")
        return {"id": course_id, "is_new": False}

    # 创建新课程
    now = datetime.now(timezone.utc)
    result = session.execute(
        text("""
            INSERT INTO courses (
                title, course_type, description, difficulty,
                direction, visibility, created_at, updated_at
            ) VALUES (
                :title, 'COURSE_MATERIAL', :description, 'INTERMEDIATE',
                :direction, 'PUBLIC_PLATFORM', :now, :now
            ) RETURNING id
        """),
        {
            "title": title,
            "description": f"{title} 课程教材",
            "direction": config["direction"],
            "now": now
        }
    )
    course_id = result.fetchone()[0]
    session.commit()
    print(f"  创建新课程: {title} (ID: {course_id})")
    return {"id": course_id, "is_new": True}


def find_or_create_practice(session, course_id: int, stage: dict, config: dict) -> dict:
    """查找或创建实训(关卡)"""
    stage_name = stage["stage_name"]
    order_index = stage["stage_id"]  # Use stage_id as order_index

    # 查询实训
    result = session.execute(
        text("""
            SELECT id, title FROM practices
            WHERE parent_course_id = :course_id AND title = :title
        """),
        {"course_id": course_id, "title": f"关卡{stage['stage_id']}-{stage_name}"}
    ).fetchone()

    if result:
        practice_id = result[0]
        print(f"    跳过已有实训: 关卡{stage['stage_id']}-{stage_name} (ID: {practice_id})")
        return {"id": practice_id, "is_new": False}

    # 创建实训
    now = datetime.now(timezone.utc)
    result = session.execute(
        text("""
            INSERT INTO practices (
                title, description, direction, category, difficulty,
                parent_course_id, summary, practice_type,
                is_published, publish_status, visibility,
                order_index, created_at, updated_at
            ) VALUES (
                :title, :description, :direction, :category, 'intermediate',
                :parent_course_id, :summary, 'online_coding',
                true, 'PUBLISHED', 'PUBLIC',
                :order_index, :now, :now
            ) RETURNING id
        """),
        {
            "title": f"关卡{stage['stage_id']}-{stage_name}",
            "description": stage.get("summary", ""),
            "direction": config["direction"],
            "category": config["category"],
            "parent_course_id": course_id,
            "summary": stage.get("summary", "")[:500] if stage.get("summary") else None,
            "order_index": order_index,
            "now": now
        }
    )
    practice_id = result.fetchone()[0]
    print(f"    创建实训: 关卡{stage['stage_id']}-{stage_name} (ID: {practice_id})")
    return {"id": practice_id, "is_new": True}


def create_task(session, practice_id: int, stage: dict, config: dict, dry_run: bool = False) -> Optional[int]:
    """创建任务，包含手册和题目"""
    stage_name = stage["stage_name"]
    handbook = stage.get("handbook", "")
    answer = stage.get("answer", "")
    questions = stage.get("questions", [])
    summary = stage.get("summary", "")

    if dry_run:
        print(f"    [DRY-RUN] 创建任务: 手册({len(handbook)}字符), 题目({len(questions)}道)")
        return None

    now = datetime.now(timezone.utc)

    # 构建 question_data JSON
    question_data = {
        "questions": [
            {
                "id": q.get("id", i + 1),
                "type": q.get("type", "single"),
                "difficulty": q.get("difficulty", "medium"),
                "question": q.get("question", ""),
                "options": q.get("options"),
                "answer": q.get("answer", ""),
                "explanation": q.get("explanation", "")
            }
            for i, q in enumerate(questions)
        ]
    }

    # 创建任务
    result = session.execute(
        text("""
            INSERT INTO tasks (
                practice_id, title, task_type, order_in_practice,
                handbook_markdown, answer_content_markdown,
                question_data, difficulty,
                created_at, updated_at
            ) VALUES (
                :practice_id, :title, 'CODE', 1,
                :handbook_markdown, :answer_content_markdown,
                :question_data, 'intermediate',
                :now, :now
            ) RETURNING id
        """),
        {
            "practice_id": practice_id,
            "title": f"{stage_name} - 编程任务",
            "handbook_markdown": handbook,
            "answer_content_markdown": answer,
            "question_data": json.dumps(question_data, ensure_ascii=False),
            "now": now
        }
    )
    task_id = result.fetchone()[0]
    print(f"    创建任务: {stage_name} (ID: {task_id})")
    return task_id


def import_stage(session, course_id: int, stage: dict, config: dict, dry_run: bool = False) -> dict:
    """导入单个关卡"""
    result = {"stage_id": stage["stage_id"], "stage_name": stage["stage_name"]}

    # 创建或获取实训
    practice = find_or_create_practice(session, course_id, stage, config)
    result["practice_id"] = practice["id"]
    result["practice_is_new"] = practice["is_new"]

    if practice["is_new"] or dry_run:
        # 创建任务
        task_id = create_task(session, practice["id"], stage, config, dry_run)
        result["task_id"] = task_id

    return result


def import_course(session, course_key: str, dry_run: bool = False) -> dict:
    """导入单个课程的所有关卡"""
    config = COURSES_CONFIG[course_key]
    print(f"\n{'='*50}")
    print(f"导入课程: {config['title']}")
    print(f"{'='*50}")

    # 查找或创建课程
    course = find_or_create_course(session, config)
    course_id = course["id"]

    imported = []
    for file_path in config["files"]:
        if not file_path.exists():
            print(f"  警告: 文件不存在 {file_path}")
            continue

        print(f"\n  加载文件: {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 处理两种JSON格式:
        # 1. {"stages": [...]} - 多关卡数组格式
        # 2. {"stage_id": N, ...} - 单关卡格式
        if "stages" in data:
            stages = data["stages"]
        elif "stage_id" in data:
            stages = [data]
        else:
            stages = []
            print(f"  警告: 未知JSON格式，跳过")

        print(f"  发现 {len(stages)} 个关卡")

        for stage in stages:
            result = import_stage(session, course_id, stage, config, dry_run)
            imported.append(result)

        if not dry_run:
            session.commit()

    return {"course": config["title"], "imported": imported}


def main():
    parser = argparse.ArgumentParser(description="导入AI生成的阶段内容")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入数据库")
    parser.add_argument(
        "--course",
        choices=["python", "nn", "all"],
        default="all",
        help="导入的课程 (默认: all)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AI内容导入工具")
    print("=" * 60)
    print(f"数据库: {DATABASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"模式: {'DRY-RUN (预览)' if args.dry_run else 'LIVE (写入数据库)'}")
    print("=" * 60)

    session = get_db_session()

    try:
        courses_to_import = []
        if args.course == "all":
            courses_to_import = ["python", "nn"]
        else:
            courses_to_import = [args.course]

        all_results = []
        for course_key in courses_to_import:
            result = import_course(session, course_key, args.dry_run)
            all_results.append(result)

        # 汇总报告
        print("\n" + "=" * 60)
        print("导入汇总")
        print("=" * 60)
        for result in all_results:
            print(f"\n{result['course']}:")
            print(f"  总关卡数: {len(result['imported'])}")
            new_practices = sum(1 for r in result['imported'] if r.get('practice_is_new', False))
            print(f"  新增实训: {new_practices}")

        if args.dry_run:
            print("\n这是预览模式，未写入数据库。")
            print("去掉 --dry-run 参数以实际写入。")
        else:
            print("\n导入完成！")

    except Exception as e:
        session.rollback()
        print(f"\n错误: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
