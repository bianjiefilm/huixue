#!/usr/bin/env python3
"""
数据库迁移脚本：创建 training_sessions 和 training_submissions 表
用于存储 ClassroomTraining（课堂实训）的学习进度和代码/记录提交。
"""

import sqlite3
from pathlib import Path

def create_training_session_tables():
    db_path = Path("huixue_local.db")

    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查 training_sessions 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_sessions'")
        if cursor.fetchone():
            print("training_sessions 表已存在，跳过创建")
        else:
            cursor.execute("""
                CREATE TABLE training_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classroom_training_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    progress_percentage INTEGER DEFAULT 0,
                    last_active_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (classroom_training_id) REFERENCES classroom_trainings(id),
                    FOREIGN KEY (student_id) REFERENCES api_users(id)
                )
            """)
            print("training_sessions 表创建成功")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_session_lookup
                ON training_sessions(classroom_training_id, student_id)
            """)

        # 检查 training_submissions 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_submissions'")
        if cursor.fetchone():
            print("training_submissions 表已存在，跳过创建")
        else:
            cursor.execute("""
                CREATE TABLE training_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL UNIQUE,
                    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    teacher_score REAL,
                    auto_score REAL,
                    content TEXT,
                    FOREIGN KEY (session_id) REFERENCES training_sessions(id)
                )
            """)
            print("training_submissions 表创建成功")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("开始数据库迁移：新增 ClassroomTraining 进度表")
    print("=" * 50)
    
    if create_training_session_tables():
        print("\n数据库迁移完成")
    else:
        print("\n数据库迁移失败")
        exit(1)
