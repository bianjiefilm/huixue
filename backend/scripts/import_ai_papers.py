#!/usr/bin/env python3
"""
导入AI生成的试卷到数据库

用法:
    python import_ai_papers.py [--dry-run] [--course python|nn|all]

示例:
    python import_ai_papers.py                    # 导入所有试卷
    python import_ai_papers.py --course python   # 只导入Python试卷
    python import_ai_papers.py --dry-run         # 预览模式
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

# 试卷配置
PAPERS_CONFIG = {
    "python": {
        "title": "Python程序设计 - 期中考试",
        "direction": "Python开发",
        "category": "编程语言",
        "file": OUTPUT_DIR / "paper_python.json",
    },
    "nn": {
        "title": "神经网络与深度学习 - 期中考试",
        "direction": "人工智能",
        "category": "深度学习",
        "file": OUTPUT_DIR / "paper_nn.json",
    },
}

# ============= 数据库操作 =============

def get_db_session():
    """创建数据库会话"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def create_question(session, q: dict, creator_id: Optional[int] = None) -> str:
    """创建题目，返回题目ID"""
    # 生成题目ID
    qid = f"ai_{q['id']:03d}"

    # 检查是否已存在
    existing = session.execute(
        text("SELECT id FROM questions WHERE id = :id"),
        {"id": qid}
    ).fetchone()

    if existing:
        print(f"    跳过已有题目: {qid}")
        return qid

    # 转换选项为JSON
    options = json.dumps(q.get("options", []), ensure_ascii=False)
    correct_answers = json.dumps([q.get("answer", "")], ensure_ascii=False)

    # 确定题目类型
    q_type = q.get("type", "single")
    if q_type == "single":
        question_type = "SINGLE_CHOICE"
    elif q_type == "multiple":
        question_type = "MULTIPLE_CHOICE"
    elif q_type == "true_false":
        question_type = "TRUE_FALSE"
    else:
        question_type = "SINGLE_CHOICE"

    # 难度映射
    difficulty_map = {"easy": "BEGINNER", "medium": "INTERMEDIATE", "hard": "ADVANCED"}
    difficulty = difficulty_map.get(q.get("difficulty", "medium"), "INTERMEDIATE")

    now = datetime.now(timezone.utc)

    # 创建题目
    session.execute(
        text("""
            INSERT INTO questions (
                id, content, question_type, options,
                correct_answers, explanation, difficulty,
                is_shared, creator_id,
                created_at, updated_at
            ) VALUES (
                :id, :content, :question_type, :options,
                :correct_answers, :explanation, :difficulty,
                true, :creator_id,
                :now, :now
            )
        """),
        {
            "id": qid,
            "content": q["question"],
            "question_type": question_type,
            "options": options,
            "correct_answers": correct_answers,
            "explanation": q.get("explanation", ""),
            "difficulty": difficulty,
            "creator_id": creator_id,
            "now": now
        }
    )

    print(f"    创建题目: {qid} - {q['question'][:30]}...")
    return qid


def create_test_paper(
    session,
    title: str,
    questions_data: list,
    config: dict,
    creator_id: Optional[int] = None,
    dry_run: bool = False
) -> Optional[int]:
    """创建试卷及其题目关联"""
    if dry_run:
        print(f"  [DRY-RUN] 创建试卷: {title}")
        print(f"    包含 {len(questions_data)} 道题目")
        return None

    now = datetime.now(timezone.utc)

    # 创建试卷
    result = session.execute(
        text("""
            INSERT INTO test_papers (
                title, description, creator_id,
                difficulty, total_score,
                direction, category,
                composition_method,
                created_at, updated_at
            ) VALUES (
                :title, :description, :creator_id,
                'INTERMEDIATE', 100,
                :direction, :category,
                'AUTO_GENERATED',
                :now, :now
            ) RETURNING id
        """),
        {
            "title": title,
            "description": f"AI自动生成的{config['direction']}课程试卷",
            "creator_id": creator_id,
            "direction": config["direction"],
            "category": config["category"],
            "now": now
        }
    )
    paper_id = result.fetchone()[0]
    print(f"  创建试卷: {title} (ID: {paper_id})")

    # 创建题目关联
    for idx, q in enumerate(questions_data, 1):
        qid = create_question(session, q, creator_id)

        session.execute(
            text("""
                INSERT INTO test_paper_questions (
                    test_paper_id, question_id,
                    score_for_question, order_in_paper
                ) VALUES (
                    :paper_id, :question_id,
                    :score, :order_in_paper
                )
            """),
            {
                "paper_id": paper_id,
                "question_id": qid,
                "score": 100 // len(questions_data),  # 平均分配分数
                "order_in_paper": idx
            }
        )

    return paper_id


def import_paper(session, course_key: str, dry_run: bool = False) -> dict:
    """导入单个试卷"""
    config = PAPERS_CONFIG[course_key]
    file_path = config["file"]

    if not file_path.exists():
        print(f"  警告: 文件不存在 {file_path}")
        return {"course": config["title"], "paper_id": None}

    print(f"\n加载试卷: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    print(f"发现 {len(questions)} 道题目")

    paper_id = create_test_paper(
        session,
        config["title"],
        questions,
        config,
        dry_run=dry_run
    )

    if not dry_run:
        session.commit()

    return {"course": config["title"], "paper_id": paper_id}


def main():
    parser = argparse.ArgumentParser(description="导入AI生成的试卷")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入数据库")
    parser.add_argument(
        "--course",
        choices=["python", "nn", "all"],
        default="all",
        help="导入的试卷 (默认: all)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AI试卷导入工具")
    print("=" * 60)
    print(f"数据库: {DATABASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"模式: {'DRY-RUN (预览)' if args.dry_run else 'LIVE (写入数据库)'}")
    print("=" * 60)

    session = get_db_session()

    try:
        papers_to_import = []
        if args.course == "all":
            papers_to_import = ["python", "nn"]
        else:
            papers_to_import = [args.course]

        results = []
        for course_key in papers_to_import:
            result = import_paper(session, course_key, args.dry_run)
            results.append(result)

        # 汇总报告
        print("\n" + "=" * 60)
        print("导入汇总")
        print("=" * 60)
        for result in results:
            status = "已创建" if result["paper_id"] else "跳过"
            print(f"  {result['course']}: {status} (ID: {result['paper_id']})")

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
