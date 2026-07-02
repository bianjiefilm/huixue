#!/usr/bin/env python3
"""
数据库初始化脚本 - 创建表结构并插入测试数据
使用方式: python3 init_database.py
"""

import sys
import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "huixue_local.db"

def execute_sql(conn, sql, params=None):
    """执行 SQL 语句"""
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        return cursor
    except sqlite3.Error as e:
        print(f"SQL 错误: {e}")
        print(f"SQL: {sql}")
        conn.rollback()
        return None

def create_tables(conn):
    """创建所有必要的表结构"""
    print("📋 创建表结构...")
    
    # 1. api_users 表
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS api_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            full_name VARCHAR(100),
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_superuser BOOLEAN DEFAULT 0,
            user_type VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)
    
    # 2. schools 表
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            short_name VARCHAR(100),
            code VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)
    
    # 3. organizations 表
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            parent_id INTEGER,
            name VARCHAR(255) NOT NULL,
            org_type VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(school_id) REFERENCES schools(id),
            FOREIGN KEY(parent_id) REFERENCES organizations(id)
        )
    """)
    
    # 4. practices 表 (实践课程)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS practices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            direction VARCHAR(100),
            category VARCHAR(100),
            difficulty VARCHAR(12),
            environment_id VARCHAR(100),
            is_published BOOLEAN DEFAULT 0,
            creator_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)
    
    # 5. tasks 表 (关卡/任务)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            practice_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            task_type VARCHAR(15),
            order_in_practice INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(practice_id) REFERENCES practices(id)
        )
    """)
    
    # 6. trainings 表 (实训项目)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            training_type VARCHAR(50),
            intro TEXT,
            industry VARCHAR(100),
            difficulty VARCHAR(12),
            handbook_content TEXT,
            assignment_nodes TEXT,
            cover_url VARCHAR(500),
            is_published BOOLEAN DEFAULT 0,
            creator_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """)
    
    # 7. classrooms 表 (课堂)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            teacher_id INTEGER NOT NULL,
            start_date DATETIME,
            end_date DATETIME,
            status VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(teacher_id) REFERENCES api_users(id)
        )
    """)
    
    # 8. classroom_practices 表 (课堂-实践关联)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS classroom_practices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_id INTEGER NOT NULL,
            practice_id INTEGER NOT NULL,
            is_required BOOLEAN DEFAULT 0,
            deadline_at DATETIME,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
            FOREIGN KEY(practice_id) REFERENCES practices(id),
            UNIQUE(classroom_id, practice_id)
        )
    """)
    
    # 9. classroom_trainings 表 (课堂-实训关联)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS classroom_trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_id INTEGER NOT NULL,
            training_id INTEGER NOT NULL,
            is_required BOOLEAN DEFAULT 0,
            deadline_at DATETIME,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
            FOREIGN KEY(training_id) REFERENCES trainings(id),
            UNIQUE(classroom_id, training_id)
        )
    """)
    
    # 10. classroom_students 表 (课堂-学生关联)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS classroom_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
            FOREIGN KEY(student_id) REFERENCES api_users(id),
            UNIQUE(classroom_id, student_id)
        )
    """)
    
    # 11. student_course_progress 表 (学生-课程进度)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS student_course_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_practice_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            overall_score INTEGER DEFAULT 0,
            first_access_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY(classroom_practice_id) REFERENCES classroom_practices(id),
            FOREIGN KEY(student_id) REFERENCES api_users(id)
        )
    """)
    
    # 12. student_training_submissions 表 (学生-实训提交)
    execute_sql(conn, """
        CREATE TABLE IF NOT EXISTS student_training_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_training_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            submission_status VARCHAR(20),
            design_file_url VARCHAR(500),
            experiment_report_url VARCHAR(500),
            teacher_score INTEGER,
            teacher_comments TEXT,
            is_excellent_work BOOLEAN DEFAULT 0,
            submitted_at DATETIME,
            graded_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(classroom_training_id) REFERENCES classroom_trainings(id),
            FOREIGN KEY(student_id) REFERENCES api_users(id)
        )
    """)
    
    print("✅ 表结构创建完成")

def insert_test_data(conn):
    """插入测试数据"""
    print("\n📝 插入测试数据...")
    
    # 1. 创建学校
    execute_sql(conn, """
        INSERT OR IGNORE INTO schools (id, name, short_name, code)
        VALUES (1, '慧学高校', 'HX', 'HX001')
    """)
    
    # 2. 创建组织
    execute_sql(conn, """
        INSERT OR IGNORE INTO organizations (id, school_id, name, org_type)
        VALUES (1, 1, '计算机学院', 'DEPARTMENT')
    """)
    
    # 3. 创建用户 (教师)
    execute_sql(conn, """
        INSERT OR IGNORE INTO api_users (id, username, email, full_name, hashed_password, user_type)
        VALUES 
        (1, 'teacher1', 'teacher1@example.com', '教师1', '$2b$12$fake_hash_1', 'teacher'),
        (2, 'teacher2', 'teacher2@example.com', '教师2', '$2b$12$fake_hash_2', 'teacher')
    """)
    
    # 4. 创建用户 (学生)
    for i in range(1, 11):
        execute_sql(conn, """
            INSERT OR IGNORE INTO api_users (username, email, full_name, hashed_password, user_type)
            VALUES (?, ?, ?, ?, 'student')
        """, (f'student{i}', f'student{i}@example.com', f'学生{i}', '$2b$12$fake_hash'))
    
    # 5. 创建课堂
    start_date = datetime.now()
    end_date = start_date + timedelta(days=120)
    
    execute_sql(conn, """
        INSERT OR IGNORE INTO classrooms (id, name, teacher_id, start_date, end_date, status)
        VALUES 
        (1, 'Python进阶班-1', 1, ?, ?, 'ongoing'),
        (2, 'Python进阶班-2', 2, ?, ?, 'ongoing'),
        (3, 'Spark数据处理-1', 1, ?, ?, 'ongoing')
    """, (start_date, end_date, start_date, end_date, start_date, end_date))
    
    # 6. 创建实践课程
    execute_sql(conn, """
        INSERT OR IGNORE INTO practices (id, title, description, direction, category, difficulty, is_published, creator_id)
        VALUES 
        (1, 'Python基础语法闯关', 'Python 基础语法学习', 'Python编程', 'practice', 'easy', 1, 1),
        (2, '程序控制结构编程', '学习 if/for/while 等控制结构', 'Python编程', 'practice', 'medium', 1, 1),
        (3, 'Python函数与模块', '学习函数定义和模块使用', 'Python编程', 'practice', 'medium', 1, 1)
    """)
    
    # 7. 创建关卡
    execute_sql(conn, """
        INSERT OR IGNORE INTO tasks (id, practice_id, title, task_type, order_in_practice)
        VALUES 
        ('task_1_1', 1, '变量与数据类型', 'coding', 1),
        ('task_1_2', 1, '字符串操作', 'coding', 2),
        ('task_2_1', 2, 'if 条件判断', 'coding', 1),
        ('task_2_2', 2, 'for 循环', 'coding', 2)
    """)
    
    # 8. 创建实训项目
    handbook = """
# 01-某零售企业经营分析

## 项目背景
本项目基于某零售企业的真实销售数据...

## 任务要求
1. 分析销售趋势
2. 计算关键指标
3. 生成报告
"""
    
    execute_sql(conn, """
        INSERT OR IGNORE INTO trainings (id, title, training_type, intro, industry, difficulty, handbook_content, is_published, creator_id)
        VALUES 
        (1, '01-某零售企业经营分析', 'DRAG_DROP', '基于某零售企业的真实数据进行经营分析', '零售', 'medium', ?, 1, 1),
        (2, '02-公募基金精准营销案例', 'DRAG_DROP', '分析公募基金的营销策略和客户行为', '金融', 'medium', ?, 1, 1),
        (3, 'Spark 数据处理项目', 'CODING', '使用 Spark 进行大规模数据处理', '数据', 'hard', ?, 1, 2)
    """, (handbook, handbook, handbook))
    
    # 9. 关联实践到课堂
    execute_sql(conn, """
        INSERT OR IGNORE INTO classroom_practices (classroom_id, practice_id, is_required)
        VALUES 
        (1, 1, 1),
        (1, 2, 1),
        (2, 3, 0)
    """)
    
    # 10. 关联实训到课堂
    execute_sql(conn, """
        INSERT OR IGNORE INTO classroom_trainings (classroom_id, training_id, is_required)
        VALUES 
        (1, 1, 1),
        (1, 2, 0),
        (3, 3, 1)
    """)
    
    # 11. 添加学生到课堂
    for i in range(1, 11):
        execute_sql(conn, """
            INSERT OR IGNORE INTO classroom_students (classroom_id, student_id)
            VALUES (1, ?)
        """, (i + 2,))  # 学生 ID 从 3 开始 (1,2 是教师)
    
    print("✅ 测试数据插入完成")

def verify_data(conn):
    """验证数据完整性"""
    print("\n🔍 验证数据完整性...")
    
    cursor = conn.cursor()
    
    tables = [
        ('api_users', 'INSERT INTO tables'),
        ('practices', '实践课程'),
        ('trainings', '实训项目'),
        ('classrooms', '课堂'),
        ('classroom_practices', '课堂-实践关联'),
        ('classroom_trainings', '课堂-实训关联'),
        ('classroom_students', '课堂-学生关联'),
    ]
    
    for table_name, description in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        status = "✅" if count > 0 else "⚠️ "
        print(f"{status} {description:20} ({table_name:25}): {count:3} 条记录")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 数据库初始化脚本")
    print("=" * 60)
    
    # 检查数据库文件
    if DB_PATH.exists():
        print(f"\n⚠️  数据库文件已存在: {DB_PATH}")
        print("💡 将在现有数据库中创建表（如果表不存在）")
    else:
        print(f"\n📍 创建新数据库: {DB_PATH}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        
        # 创建表
        create_tables(conn)
        
        # 插入测试数据
        insert_test_data(conn)
        
        # 验证数据
        verify_data(conn)
        
        # 关闭连接
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 数据库初始化成功！")
        print("=" * 60)
        print(f"\n📊 数据库位置: {DB_PATH}")
        print(f"👥 已创建用户: 2 个教师 + 8 个学生")
        print(f"🎓 已创建课堂: 3 个")
        print(f"📚 已创建课程: 3 个实践 + 3 个实训")
        print("\n现在可以启动后端服务了！")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
