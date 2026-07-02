"""
数据库迁移：添加成绩系统表

运行方式：
  python -m alembic upgrade head
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

import sqlite3
from datetime import datetime

DB_PATH = '/Users/jimfu/Desktop/huixue/huixue_local.db'


def create_grading_tables():
    """创建成绩系统表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. StudentCourseProgress 表
        print("📋 创建 student_course_progress 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_course_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classroom_course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status VARCHAR(50) DEFAULT 'not_started',
                overall_score REAL,
                teacher_penalties REAL DEFAULT 0,
                final_calculated_score REAL,
                completed_task_count INTEGER DEFAULT 0,
                total_time_spent_seconds INTEGER DEFAULT 0,
                training_assignment_files JSON,
                last_submission_at DATETIME,
                teacher_feedback TEXT,
                graded_by_teacher_id INTEGER,
                graded_at DATETIME,
                is_excellent_work BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (classroom_course_id) REFERENCES classroom_courses(id),
                FOREIGN KEY (student_id) REFERENCES api_users(id),
                FOREIGN KEY (graded_by_teacher_id) REFERENCES api_users(id),
                UNIQUE(classroom_course_id, student_id)
            )
        ''')
        print("  ✅ student_course_progress 表创建成功")
        
        # 2. TaskEvaluationResults 表
        print("📋 创建 task_evaluation_results 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_course_progress_id INTEGER NOT NULL,
                task_id INTEGER,
                score REAL NOT NULL,
                completed BOOLEAN DEFAULT 0,
                evaluation_details JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_course_progress_id) REFERENCES student_course_progress(id)
            )
        ''')
        print("  ✅ task_evaluation_results 表创建成功")
        
        # 3. ClassroomCourseSettings 表
        print("📋 创建 classroom_course_settings 表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_course_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classroom_course_id INTEGER NOT NULL UNIQUE,
                is_required BOOLEAN DEFAULT 1,
                allow_late_submission BOOLEAN DEFAULT 1,
                late_penalty_per_day REAL DEFAULT 5,
                final_deadline DATETIME,
                show_rankings BOOLEAN DEFAULT 1,
                allow_public_score_view BOOLEAN DEFAULT 0,
                enable_teacher_feedback BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (classroom_course_id) REFERENCES classroom_courses(id)
            )
        ''')
        print("  ✅ classroom_course_settings 表创建成功")
        
        # 创建索引
        print("📋 创建索引...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scp_classroom_course ON student_course_progress(classroom_course_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scp_student ON student_course_progress(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ter_progress ON task_evaluation_results(student_course_progress_id)')
        print("  ✅ 索引创建成功")
        
        conn.commit()
        print("\n✅ 所有成绩系统表创建完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


def insert_initial_settings():
    """为现有课堂插入默认设置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n📋 为现有课堂插入默认设置...")
        
        # 获取所有课堂课程
        cursor.execute('SELECT id FROM classroom_courses')
        classroom_courses = cursor.fetchall()
        
        count = 0
        for (cc_id,) in classroom_courses:
            # 检查是否已存在
            cursor.execute('SELECT id FROM classroom_course_settings WHERE classroom_course_id = ?', (cc_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO classroom_course_settings (classroom_course_id)
                    VALUES (?)
                ''', (cc_id,))
                count += 1
        
        conn.commit()
        print(f"  ✅ 为 {count} 个课堂插入了默认设置")
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 P3 成绩系统数据库迁移")
    print("=" * 60)
    
    if create_grading_tables():
        insert_initial_settings()
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)

