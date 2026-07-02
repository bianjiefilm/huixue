#!/usr/bin/env python3
"""
实测种子数据脚本
向 huixue_local.db 插入完整的测试数据链路，
覆盖：课堂、课程、考试、试题、成绩、资源、实践、实训

用法: cd backend && python3 scripts/seed_test_data.py
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 确保可以 import app 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DATABASE_URL", "sqlite:///./huixue_local.db")

import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "huixue_local.db")

# ── 时间常量（使用本地时间，因为前端与本地时间比较）──
NOW = datetime.now()  # 本地时间
TWELVE_HOURS_AGO = NOW - timedelta(hours=12)
TWELVE_HOURS_LATER = NOW + timedelta(hours=12)
ONE_MONTH_AGO = NOW - timedelta(days=30)
ONE_MONTH_LATER = NOW + timedelta(days=30)
ONE_WEEK_AGO = NOW - timedelta(days=7)

# ── 固定 ID（方便浏览器测试引用）──
TEACHER_ID = 29
STUDENT_ID = 30
CLASSROOM_ID = 100
COURSE_ID_1 = 100          # 普通课程（有视频/PPT资源）
COURSE_ID_2 = 101          # 第二门课程
CC_ID_1 = 100              # classroom_course id
CC_ID_2 = 101
RESOURCE_MODULE_ID = 100
PRACTICE_ID = 100
TASK_ID_1 = 100
TASK_ID_2 = 101
TRAINING_ID = 100
PAPER_ID = 100
EXAM_ID = 100
QUESTION_IDS = ["q_single_1", "q_multi_1", "q_tf_1"]


def ts(dt):
    """格式化 datetime 为 ISO 字符串"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🌱 开始种子数据注入...")

    # ══════════════════════════════════════════
    # 1. 课堂 (Classroom)
    # ══════════════════════════════════════════
    c.execute("DELETE FROM classrooms WHERE id = ?", (CLASSROOM_ID,))
    c.execute("""
        INSERT INTO classrooms (id, name, description, teacher_id, credit, start_date, end_date,
            academic_year, semester, status, student_count, cover_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        CLASSROOM_ID, "大数据分析实验班", "用于实测的课堂",
        TEACHER_ID, 4, ts(ONE_MONTH_AGO), ts(ONE_MONTH_LATER),
        "2025-2026", "春季", "ONGOING", 3, None, ts(ONE_MONTH_AGO)
    ))
    print("  ✅ 课堂")

    # ══════════════════════════════════════════
    # 2. 学生加入课堂
    # ══════════════════════════════════════════
    c.execute("DELETE FROM classroom_students WHERE classroom_id = ?", (CLASSROOM_ID,))
    for sid in [30, 31, 32]:
        c.execute("""
            INSERT INTO classroom_students (classroom_id, student_id, joined_at)
            VALUES (?, ?, ?)
        """, (CLASSROOM_ID, sid, ts(ONE_MONTH_AGO)))
    print("  ✅ 学生加入课堂 (3人)")

    # ══════════════════════════════════════════
    # 3. 课程 (Course)
    # ══════════════════════════════════════════
    for cid, title, ctype in [
        (COURSE_ID_1, "Python数据分析基础", "COURSE_MATERIAL"),
        (COURSE_ID_2, "Spark大数据处理", "COURSE_MATERIAL"),
    ]:
        c.execute("DELETE FROM courses WHERE id = ?", (cid,))
        c.execute("""
            INSERT INTO courses (id, title, course_type, description, difficulty, direction,
                visibility, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid, title, ctype,
            f"{title} 课程简介",
            "INTERMEDIATE", "大数据", "PUBLIC_PLATFORM", ts(ONE_MONTH_AGO)
        ))
    print("  ✅ 课程 (2门)")

    # ══════════════════════════════════════════
    # 4. 课堂课程关联 (ClassroomCourse)
    # ══════════════════════════════════════════
    c.execute("DELETE FROM classroom_courses WHERE classroom_id = ?", (CLASSROOM_ID,))
    for cc_id, course_id, order_idx in [
        (CC_ID_1, COURSE_ID_1, 1),
        (CC_ID_2, COURSE_ID_2, 2),
    ]:
        c.execute("""
            INSERT INTO classroom_courses (id, classroom_id, course_id, order_in_classroom,
                teacher_publish_status, is_mandatory, deadline_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cc_id, CLASSROOM_ID, course_id, order_idx,
            "LEARNING", 1, ts(ONE_MONTH_LATER), ts(ONE_MONTH_AGO)
        ))
    print("  ✅ 课堂-课程关联")

    # ══════════════════════════════════════════
    # 5. 资源模块 + 资源文件（视频 + PPT）
    # ══════════════════════════════════════════
    c.execute("DELETE FROM resource_files WHERE module_id = ?", (RESOURCE_MODULE_ID,))
    c.execute("DELETE FROM resource_modules WHERE id = ?", (RESOURCE_MODULE_ID,))
    c.execute("""
        INSERT INTO resource_modules (id, classroom_id, name, description, order_index,
            created_by, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        RESOURCE_MODULE_ID, CLASSROOM_ID, "第一章 Python基础",
        "Python基础知识", 1, TEACHER_ID, 1, ts(ONE_MONTH_AGO)
    ))

    resources = [
        (100, "Python变量与数据类型.mp4", "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4", "video", 1048576, 120),
        (101, "Python控制流程.pptx", "https://example.com/python_control_flow.pptx", "ppt", 524288, None),
        (102, "Python函数与模块.pdf", "https://example.com/python_functions.pdf", "pdf", 262144, None),
    ]
    for rid, name, url, ftype, fsize, duration in resources:
        c.execute("""
            INSERT INTO resource_files (id, module_id, name, url, file_type, file_size,
                duration_seconds, uploader_id, view_count, download_count, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rid, RESOURCE_MODULE_ID, name, url, ftype, fsize,
            duration, TEACHER_ID, 0, 0, 1, ts(ONE_MONTH_AGO)
        ))
    print("  ✅ 资源模块 + 资源文件 (视频/PPT/PDF)")

    # ══════════════════════════════════════════
    # 6. 试题 (Question) — 单选 / 多选 / 判断
    # ══════════════════════════════════════════
    for qid in QUESTION_IDS:
        c.execute("DELETE FROM questions WHERE id = ?", (qid,))

    # 单选题
    c.execute("""
        INSERT INTO questions (id, content, question_type, options, correct_answers, explanation,
            difficulty, creator_id, is_shared, direction, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q_single_1",
        "Python中，以下哪个函数用于获取列表的长度？",
        "SINGLE_CHOICE",
        json.dumps([
            {"key": "A", "content": "size()"},
            {"key": "B", "content": "length()"},
            {"key": "C", "content": "len()"},
            {"key": "D", "content": "count()"},
        ]),
        json.dumps(["C"]),
        "len() 是Python内置函数，用于返回对象的长度。",
        "BEGINNER", TEACHER_ID, 1, "大数据", ts(ONE_WEEK_AGO)
    ))

    # 多选题
    c.execute("""
        INSERT INTO questions (id, content, question_type, options, correct_answers, explanation,
            difficulty, creator_id, is_shared, direction, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q_multi_1",
        "以下哪些是Python的基本数据类型？（多选）",
        "MULTIPLE_CHOICE",
        json.dumps([
            {"key": "A", "content": "int"},
            {"key": "B", "content": "float"},
            {"key": "C", "content": "array"},
            {"key": "D", "content": "str"},
        ]),
        json.dumps(["A", "B", "D"]),
        "Python的基本数据类型包括int、float、str、bool等。array不是内置类型。",
        "BEGINNER", TEACHER_ID, 1, "大数据", ts(ONE_WEEK_AGO)
    ))

    # 判断题
    c.execute("""
        INSERT INTO questions (id, content, question_type, options, correct_answers, explanation,
            difficulty, creator_id, is_shared, direction, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q_tf_1",
        "Python中的列表(list)是不可变的。",
        "TRUE_FALSE",
        json.dumps([
            {"key": "true", "content": "正确"},
            {"key": "false", "content": "错误"},
        ]),
        json.dumps(["false"]),
        "Python中的列表是可变的，元组(tuple)才是不可变的。",
        "BEGINNER", TEACHER_ID, 1, "大数据", ts(ONE_WEEK_AGO)
    ))
    print("  ✅ 试题 (单选/多选/判断 各1)")

    # ══════════════════════════════════════════
    # 7. 试卷 (TestPaper) + 试卷-试题关联
    # ══════════════════════════════════════════
    c.execute("DELETE FROM test_paper_questions WHERE test_paper_id = ?", (PAPER_ID,))
    c.execute("DELETE FROM test_papers WHERE id = ?", (PAPER_ID,))
    c.execute("""
        INSERT INTO test_papers (id, title, description, creator_id, difficulty,
            total_score, estimated_duration_minutes, is_shared, direction, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        PAPER_ID, "Python基础测验", "Python基础知识随堂测验",
        TEACHER_ID, "BEGINNER", 30, 30, 0, "大数据", ts(ONE_WEEK_AGO)
    ))

    for idx, (qid, score) in enumerate([
        ("q_single_1", 10), ("q_multi_1", 10), ("q_tf_1", 10)
    ]):
        c.execute("""
            INSERT INTO test_paper_questions (test_paper_id, question_id, score_for_question,
                order_in_paper, section_title)
            VALUES (?, ?, ?, ?, ?)
        """, (PAPER_ID, qid, score, idx + 1, "基础知识"))
    print("  ✅ 试卷 + 试题关联")

    # ══════════════════════════════════════════
    # 8. 考试 (ClassroomExam) — 进行中
    # ══════════════════════════════════════════
    c.execute("DELETE FROM student_exam_answers WHERE student_exam_attempt_id IN (SELECT id FROM student_exam_attempts WHERE classroom_exam_id = ?)", (EXAM_ID,))
    c.execute("DELETE FROM student_exam_attempts WHERE classroom_exam_id = ?", (EXAM_ID,))
    c.execute("DELETE FROM classroom_exams WHERE id = ?", (EXAM_ID,))
    c.execute("""
        INSERT INTO classroom_exams (id, classroom_id, test_paper_id, title,
            exam_start_time, exam_end_time, duration_minutes, pass_mark,
            shuffle_questions, shuffle_options, status, created_by_teacher_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        EXAM_ID, CLASSROOM_ID, PAPER_ID, "Python基础随堂测验",
        ts(TWELVE_HOURS_AGO), ts(TWELVE_HOURS_LATER), 720, 18,
        0, 0, "ONGOING", TEACHER_ID, ts(TWELVE_HOURS_AGO)
    ))
    print("  ✅ 考试 (IN_PROGRESS, 时间窗口=now±2h)")

    # ══════════════════════════════════════════
    # 9. 学生课程成绩 — student1 第一门课 75分
    # ══════════════════════════════════════════
    c.execute("DELETE FROM student_course_progress WHERE classroom_course_id IN (?, ?) AND student_id = ?",
              (CC_ID_1, CC_ID_2, STUDENT_ID))
    c.execute("""
        INSERT INTO student_course_progress (classroom_course_id, student_id, student_status,
            overall_score, teacher_penalties, final_calculated_score, graded_by_teacher_id,
            graded_at, teacher_feedback, is_excellent_work, first_access_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        CC_ID_1, STUDENT_ID, "COMPLETED_ON_TIME",
        75, 0, 75, TEACHER_ID,
        ts(ONE_WEEK_AGO), "基础扎实，继续保持", 0, ts(ONE_MONTH_AGO)
    ))
    print("  ✅ 学生成绩 (student1: 75分)")

    # ══════════════════════════════════════════
    # 10. 实践 (Practice) + 关卡 (Task)
    # ══════════════════════════════════════════
    c.execute("DELETE FROM tasks WHERE practice_id = ?", (PRACTICE_ID,))
    c.execute("DELETE FROM classroom_practices WHERE practice_id = ?", (PRACTICE_ID,))
    c.execute("DELETE FROM practices WHERE id = ?", (PRACTICE_ID,))
    c.execute("""
        INSERT INTO practices (id, title, description, direction, category, difficulty,
            coin, task_count, practice_type, publish_status, creator_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        PRACTICE_ID, "Python列表操作练习",
        "掌握Python列表的基本操作：增删改查、切片、推导式",
        "大数据", "Python编程", "beginner",
        20, 2, "CODING", "PUBLISHED", TEACHER_ID, ts(ONE_MONTH_AGO)
    ))

    for tid, title, ttype, order_val in [
        (TASK_ID_1, "列表基本操作", "CODING", 1),
        (TASK_ID_2, "列表推导式", "CODING", 2),
    ]:
        c.execute("""
            INSERT INTO tasks (id, practice_id, title, task_type, order_in_practice,
                coin, difficulty, handbook_markdown, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tid, PRACTICE_ID, title, ttype, order_val,
            10, "beginner",
            f"# {title}\n\n请完成以下练习...",
            ts(ONE_MONTH_AGO)
        ))

    # 关联到课堂
    c.execute("""
        INSERT INTO classroom_practices (classroom_id, practice_id, sync_doc, added_at)
        VALUES (?, ?, ?, ?)
    """, (CLASSROOM_ID, PRACTICE_ID, 0, ts(ONE_MONTH_AGO)))
    print("  ✅ 实践 + 关卡 (2个)")

    # ══════════════════════════════════════════
    # 11. 实训 (Training) — 编程类型
    # ══════════════════════════════════════════
    c.execute("DELETE FROM classroom_trainings WHERE training_id = ?", (TRAINING_ID,))
    c.execute("DELETE FROM trainings WHERE id = ?", (TRAINING_ID,))
    c.execute("""
        INSERT INTO trainings (id, title, training_type, intro, industry, difficulty,
            course_hours, visibility, publish_status, creator_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        TRAINING_ID, "数据清洗实训项目",
        "JUPYTER", "使用Pandas进行数据清洗和预处理",
        "大数据", "intermediate",
        8, "PUBLIC", "PUBLISHED", TEACHER_ID, ts(ONE_MONTH_AGO)
    ))

    c.execute("""
        INSERT INTO classroom_trainings (classroom_id, training_id, order_index, added_at)
        VALUES (?, ?, ?, ?)
    """, (CLASSROOM_ID, TRAINING_ID, 1, ts(ONE_MONTH_AGO)))
    print("  ✅ 实训 + 课堂关联")

    # ══════════════════════════════════════════
    # 完成
    # ══════════════════════════════════════════
    conn.commit()
    conn.close()

    print("\n🎉 种子数据注入完成！")
    print(f"   数据库: {os.path.abspath(DB_PATH)}")
    print(f"\n📋 数据总览:")
    print(f"   课堂:   id={CLASSROOM_ID} (大数据分析实验班)")
    print(f"   课程:   id={COURSE_ID_1},{COURSE_ID_2}")
    print(f"   考试:   id={EXAM_ID} (IN_PROGRESS)")
    print(f"   试题:   {QUESTION_IDS}")
    print(f"   成绩:   student_id={STUDENT_ID}, score=75")
    print(f"   实践:   id={PRACTICE_ID}")
    print(f"   实训:   id={TRAINING_ID}")
    print(f"\n🌐 浏览器测试入口:")
    print(f"   课堂详情: http://localhost:3000/#/classroom/{CLASSROOM_ID}")
    print(f"   考试答题: http://localhost:3000/#/classroom/{CLASSROOM_ID}/exam/{EXAM_ID}/take")
    print(f"   学生成绩: http://localhost:3000/#/classroom/{CLASSROOM_ID}/student-grades")


if __name__ == "__main__":
    seed()
