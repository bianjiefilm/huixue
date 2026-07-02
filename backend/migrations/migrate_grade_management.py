#!/usr/bin/env python3
"""
成绩查看和作业点评功能数据库迁移脚本

功能说明：
1. 添加实训课程提交状态枚举
2. 添加点评状态枚举  
3. 更新StudentCourseProgress表，添加实训作业相关字段
4. 创建必要的索引以提升查询性能

使用方法：
python migrate_grade_management.py

注意事项：
- 执行前请备份数据库
- 确保数据库连接正常
- 迁移过程中请勿中断
"""

import sys
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import enum

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine

# 定义枚举类型
class SubmissionStatusEnum(enum.Enum):
    NOT_STARTED = "NOT_STARTED"      # 未开始
    NOT_SUBMITTED = "NOT_SUBMITTED"  # 未提交
    SUBMITTED = "SUBMITTED"          # 已提交
    LATE_SUBMITTED = "LATE_SUBMITTED"  # 已补交

class GradingStatusEnum(enum.Enum):
    NOT_GRADED = "NOT_GRADED"  # 未点评
    GRADED = "GRADED"          # 已点评

def check_database_connection():
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 数据库连接正常")
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def check_table_exists(table_name):
    """检查表是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            """))
            exists = result.scalar() > 0
            print(f"{'✓' if exists else '✗'} 表 {table_name} {'存在' if exists else '不存在'}")
            return exists
    except Exception as e:
        print(f"✗ 检查表 {table_name} 失败: {e}")
        return False

def check_column_exists(table_name, column_name):
    """检查列是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = '{column_name}'
            """))
            exists = result.scalar() > 0
            return exists
    except Exception as e:
        print(f"✗ 检查列 {table_name}.{column_name} 失败: {e}")
        return False

def check_enum_exists(enum_name):
    """检查枚举类型是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM pg_type 
                WHERE typname = '{enum_name}'
            """))
            exists = result.scalar() > 0
            return exists
    except Exception as e:
        print(f"✗ 检查枚举 {enum_name} 失败: {e}")
        return False

def create_enum_types():
    """创建枚举类型"""
    print("\n=== 创建枚举类型 ===")
    
    try:
        with engine.begin() as conn:
            # 创建实训课程提交状态枚举
            if not check_enum_exists('submission_status_enum'):
                conn.execute(text("""
                    CREATE TYPE submission_status_enum AS ENUM (
                        'NOT_STARTED',
                        'NOT_SUBMITTED', 
                        'SUBMITTED',
                        'LATE_SUBMITTED'
                    )
                """))
                print("✓ 创建 submission_status_enum 枚举类型")
            else:
                print("✓ submission_status_enum 枚举类型已存在")
            
            # 创建点评状态枚举
            if not check_enum_exists('grading_status_enum'):
                conn.execute(text("""
                    CREATE TYPE grading_status_enum AS ENUM (
                        'NOT_GRADED',
                        'GRADED'
                    )
                """))
                print("✓ 创建 grading_status_enum 枚举类型")
            else:
                print("✓ grading_status_enum 枚举类型已存在")
                
    except Exception as e:
        print(f"✗ 创建枚举类型失败: {e}")
        raise

def add_training_assignment_fields():
    """添加实训作业相关字段"""
    print("\n=== 添加实训作业相关字段 ===")
    
    if not check_table_exists('student_course_progress'):
        print("✗ student_course_progress 表不存在，请先运行基础迁移")
        return False
    
    try:
        with engine.begin() as conn:
            # 添加实训作业文件字段
            if not check_column_exists('student_course_progress', 'training_assignment_files'):
                conn.execute(text("""
                    ALTER TABLE student_course_progress 
                    ADD COLUMN training_assignment_files TEXT
                """))
                print("✓ 添加 training_assignment_files 字段")
            else:
                print("✓ training_assignment_files 字段已存在")
            
            # 添加实训提交状态字段
            if not check_column_exists('student_course_progress', 'training_submission_status'):
                conn.execute(text("""
                    ALTER TABLE student_course_progress 
                    ADD COLUMN training_submission_status submission_status_enum DEFAULT 'NOT_STARTED'
                """))
                print("✓ 添加 training_submission_status 字段")
            else:
                print("✓ training_submission_status 字段已存在")
            
            return True
            
    except Exception as e:
        print(f"✗ 添加实训作业字段失败: {e}")
        raise

def create_indexes():
    """创建索引以提升查询性能"""
    print("\n=== 创建索引 ===")
    
    indexes = [
        {
            "name": "idx_student_course_progress_submission_status",
            "table": "student_course_progress",
            "columns": ["training_submission_status"],
            "description": "实训提交状态索引"
        },
        {
            "name": "idx_student_course_progress_graded_at",
            "table": "student_course_progress", 
            "columns": ["graded_at"],
            "description": "点评时间索引"
        },
        {
            "name": "idx_student_course_progress_excellent",
            "table": "student_course_progress",
            "columns": ["is_excellent_work"],
            "description": "优秀作业索引"
        },
        {
            "name": "idx_student_course_progress_composite",
            "table": "student_course_progress",
            "columns": ["classroom_course_id", "student_status", "training_submission_status"],
            "description": "复合查询索引"
        }
    ]
    
    try:
        with engine.begin() as conn:
            for index in indexes:
                # 检查索引是否已存在
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE indexname = '{index['name']}'
                """))
                
                if result.scalar() == 0:
                    columns_str = ", ".join(index['columns'])
                    conn.execute(text(f"""
                        CREATE INDEX {index['name']} 
                        ON {index['table']} ({columns_str})
                    """))
                    print(f"✓ 创建索引 {index['name']} - {index['description']}")
                else:
                    print(f"✓ 索引 {index['name']} 已存在")
            
    except Exception as e:
        print(f"✗ 创建索引失败: {e}")
        raise

def verify_migration():
    """验证迁移结果"""
    print("\n=== 验证迁移结果 ===")
    
    checks = [
        ("枚举类型", "submission_status_enum", lambda: check_enum_exists('submission_status_enum')),
        ("枚举类型", "grading_status_enum", lambda: check_enum_exists('grading_status_enum')),
        ("字段", "training_assignment_files", lambda: check_column_exists('student_course_progress', 'training_assignment_files')),
        ("字段", "training_submission_status", lambda: check_column_exists('student_course_progress', 'training_submission_status')),
    ]
    
    all_passed = True
    for check_type, name, check_func in checks:
        try:
            if check_func():
                print(f"✓ {check_type} {name} 验证通过")
            else:
                print(f"✗ {check_type} {name} 验证失败")
                all_passed = False
        except Exception as e:
            print(f"✗ {check_type} {name} 验证出错: {e}")
            all_passed = False
    
    return all_passed

def create_sample_data():
    """创建示例数据（可选）"""
    print("\n=== 创建示例数据 ===")
    
    try:
        with engine.connect() as conn:
            # 检查是否有课堂课程数据
            result = conn.execute(text("""
                SELECT COUNT(*) FROM classroom_courses cc
                JOIN courses c ON cc.course_id = c.id
                WHERE c.course_type = 'TRAINING'
                LIMIT 1
            """))
            
            if result.scalar() > 0:
                print("✓ 发现实训课程，可以开始使用成绩管理功能")
            else:
                print("ℹ 暂无实训课程数据，请先添加实训课程到课堂")
                
    except Exception as e:
        print(f"✗ 检查示例数据失败: {e}")

def rollback_migration():
    """回滚迁移（仅删除新增字段，保留数据）"""
    print("\n=== 回滚迁移 ===")
    
    try:
        with engine.begin() as conn:
            # 删除新增字段
            if check_column_exists('student_course_progress', 'training_assignment_files'):
                conn.execute(text("""
                    ALTER TABLE student_course_progress 
                    DROP COLUMN training_assignment_files
                """))
                print("✓ 删除 training_assignment_files 字段")
            
            if check_column_exists('student_course_progress', 'training_submission_status'):
                conn.execute(text("""
                    ALTER TABLE student_course_progress 
                    DROP COLUMN training_submission_status
                """))
                print("✓ 删除 training_submission_status 字段")
            
            # 删除枚举类型（如果没有其他表使用）
            if check_enum_exists('submission_status_enum'):
                conn.execute(text("DROP TYPE submission_status_enum"))
                print("✓ 删除 submission_status_enum 枚举类型")
            
            if check_enum_exists('grading_status_enum'):
                conn.execute(text("DROP TYPE grading_status_enum"))
                print("✓ 删除 grading_status_enum 枚举类型")
            
            print("✓ 迁移回滚完成")
            
    except Exception as e:
        print(f"✗ 回滚迁移失败: {e}")
        raise

def main():
    """主函数"""
    print("成绩查看和作业点评功能数据库迁移脚本")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("执行回滚操作...")
        if not check_database_connection():
            return False
        rollback_migration()
        return True
    
    # 检查数据库连接
    if not check_database_connection():
        return False
    
    try:
        # 执行迁移步骤
        create_enum_types()
        add_training_assignment_fields()
        create_indexes()
        
        # 验证迁移结果
        if verify_migration():
            print("\n✓ 成绩查看和作业点评功能迁移完成！")
            create_sample_data()
            
            print("\n" + "=" * 50)
            print("迁移成功！现在可以使用以下功能：")
            print("1. 查看课程成绩列表（实践课程和实训课程）")
            print("2. 实训作业提交和点评")
            print("3. 奖惩扣分调整")
            print("4. 优秀作业评选")
            print("5. 成绩统计和导出")
            print("\n相关API接口已添加到 main.py 中")
            print("详细文档请查看即将生成的 API 文档")
            return True
        else:
            print("\n✗ 迁移验证失败，请检查错误信息")
            return False
            
    except Exception as e:
        print(f"\n✗ 迁移过程中发生错误: {e}")
        print("建议检查数据库状态并重试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 