#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查课程状态枚举值
"""

from database import get_db, engine
from sqlalchemy import text

# 获取数据库连接
db = next(get_db())

try:
    print("✅ 数据库连接成功")
    
    # 检查course_in_classroom_status_teacher_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::course_in_classroom_status_teacher_enum))"))
        teacher_statuses = [row[0] for row in result]
        print(f"📋 course_in_classroom_status_teacher_enum的值: {teacher_statuses}")
    except Exception as e:
        print(f"❌ course_in_classroom_status_teacher_enum不存在或查询失败: {e}")
    
    # 检查course_in_classroom_status_student_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::course_in_classroom_status_student_enum))"))
        student_statuses = [row[0] for row in result]
        print(f"📋 course_in_classroom_status_student_enum的值: {student_statuses}")
    except Exception as e:
        print(f"❌ course_in_classroom_status_student_enum不存在或查询失败: {e}")
    
    # 检查classroom_status_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::classroom_status_enum))"))
        classroom_statuses = [row[0] for row in result]
        print(f"📋 classroom_status_enum的值: {classroom_statuses}")
    except Exception as e:
        print(f"❌ classroom_status_enum不存在或查询失败: {e}")
    
    # 检查course_type_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::course_type_enum))"))
        course_types = [row[0] for row in result]
        print(f"📋 course_type_enum的值: {course_types}")
    except Exception as e:
        print(f"❌ course_type_enum不存在或查询失败: {e}")
    
    # 检查所有枚举类型
    print("\n📋 所有枚举类型:")
    result = db.execute(text("""
        SELECT typname 
        FROM pg_type 
        WHERE typtype = 'e' 
        ORDER BY typname
    """))
    enum_types = [row[0] for row in result]
    for enum_type in enum_types:
        print(f"  - {enum_type}")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
finally:
    db.close() 