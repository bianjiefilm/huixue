#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查classroom_courses表结构
"""

from database import get_db, engine
from sqlalchemy import text

# 获取数据库连接
db = next(get_db())

try:
    print("✅ 数据库连接成功")
    
    # 检查classroom_courses表是否存在
    result = db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'classroom_courses'
        )
    """))
    table_exists = result.scalar()
    
    if table_exists:
        print("✅ classroom_courses表存在")
        
        # 获取表字段信息
        result = db.execute(text("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'classroom_courses'
            ORDER BY ordinal_position
        """))
        
        print("\n📋 classroom_courses表字段:")
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"  {row[0]:<30} {row[1]:<20} {nullable}{default}")
        
        # 检查表中的数据
        result = db.execute(text("SELECT COUNT(*) FROM classroom_courses"))
        count = result.scalar()
        print(f"\n📊 classroom_courses表中有 {count} 条记录")
        
        if count > 0:
            # 显示前几条记录
            result = db.execute(text("""
                SELECT 
                    id, classroom_id, course_id, 
                    teacher_publish_status, published_at, deadline_at
                FROM classroom_courses 
                LIMIT 5
            """))
            print("\n📋 前5条记录:")
            for row in result:
                print(f"  ID: {row[0]}, 课堂: {row[1]}, 课程: {row[2]}, 状态: {row[3]}")
    else:
        print("❌ classroom_courses表不存在")
        
    # 检查student_course_progress表
    result = db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'student_course_progress'
        )
    """))
    progress_table_exists = result.scalar()
    
    if progress_table_exists:
        print("\n✅ student_course_progress表存在")
        
        # 检查表中的数据
        result = db.execute(text("SELECT COUNT(*) FROM student_course_progress"))
        count = result.scalar()
        print(f"📊 student_course_progress表中有 {count} 条记录")
    else:
        print("\n❌ student_course_progress表不存在")
    
except Exception as e:
    print(f"❌ 查询失败: {e}")
finally:
    db.close() 