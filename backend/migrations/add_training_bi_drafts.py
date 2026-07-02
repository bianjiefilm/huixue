#!/usr/bin/env python3
"""
数据库迁移脚本：创建 training_bi_drafts 表
用于存储 BI 可视化分析实训的草稿数据
"""

import sqlite3
from pathlib import Path

def create_training_bi_drafts_table():
    """创建 training_bi_drafts 表"""

    # 数据库路径
    db_path = Path("huixue_local.db")

    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='training_bi_drafts'
        """)
        if cursor.fetchone():
            print("training_bi_drafts 表已存在，无需创建")
            conn.close()
            return True

        # 创建表
        cursor.execute("""
            CREATE TABLE training_bi_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                training_id INTEGER NOT NULL,
                classroom_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                draft_snapshot TEXT,
                schema_version VARCHAR(50),
                platform_version VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (training_id) REFERENCES trainings(id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
                FOREIGN KEY (student_id) REFERENCES api_users(id),
                UNIQUE (training_id, classroom_id, student_id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bi_draft_student
            ON training_bi_drafts(student_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bi_draft_training
            ON training_bi_drafts(training_id)
        """)

        conn.commit()
        print("training_bi_drafts 表创建成功")

        # 验证表创建成功
        cursor.execute("PRAGMA table_info(training_bi_drafts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"training_bi_drafts 表字段: {column_names}")

        conn.close()
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        return False


def add_snapshot_fields_to_progress():
    """向 student_course_progress 表添加快照相关字段（如果不存在）"""

    db_path = Path("huixue_local.db")

    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查 student_course_progress 表的现有字段
        cursor.execute("PRAGMA table_info(student_course_progress)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # 添加 snapshot_schema_version 字段
        if 'snapshot_schema_version' not in column_names:
            cursor.execute("""
                ALTER TABLE student_course_progress
                ADD COLUMN snapshot_schema_version VARCHAR(50)
            """)
            print("添加 snapshot_schema_version 字段成功")

        # 添加 snapshot_thumbnail 字段
        if 'snapshot_thumbnail' not in column_names:
            cursor.execute("""
                ALTER TABLE student_course_progress
                ADD COLUMN snapshot_thumbnail TEXT
            """)
            print("添加 snapshot_thumbnail 字段成功")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"添加字段失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("开始数据库迁移：BI 实训草稿表")
    print("=" * 50)

    success1 = create_training_bi_drafts_table()
    success2 = add_snapshot_fields_to_progress()

    if success1 and success2:
        print("\n数据库迁移完成")
    else:
        print("\n数据库迁移部分失败")
        exit(1)
